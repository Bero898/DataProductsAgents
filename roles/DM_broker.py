from metagpt.roles.role import Role
from actions.perform_broker_analysis import PerformBrokerAnalysis
from actions.create_report import CreateCompatibilityReport
from metagpt.schema import Message
from metagpt.logs import logger
import os

class DMBroker(Role):
    name: str = "Connor"
    profile: str = "Data Mesh Broker"
    ownerA: str = ""  # Owner of the first data product
    ownerB: str = ""  # Owner of the second data product
    ownerA_2: str = ""  # Owner of the first data product after the first round
    ownerB_2: str = ""  # Owner of the second data product after the first round
    report_file: str = "compatibility_report.txt"  # File to store the report

    def __init__(self, name: str = "Connor", ownerA: str = "", ownerB: str = "", ownerA_2: str = "", ownerB_2: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.ownerA = ownerA
        self.ownerB = ownerB
        self.ownerA_2 = ownerA_2
        self.ownerB_2 = ownerB_2
        self.set_actions([PerformBrokerAnalysis, CreateCompatibilityReport])
        self._watch([PerformBrokerAnalysis, CreateCompatibilityReport])

    async def react(self) -> Message:
        # Ensure the broker reacts only to the most recent data from the current round
        if not self.rc.news:
            logger.debug(f"{self.name}: No news to process.")
            return None

        # Get the latest message
        latest_msg = self.rc.news[-1]

        # Check the current round's state
        memories = self.get_memories()
        current_round_memories = [
            memory for memory in memories if memory.round == self.rc.round
        ]

        # Check if owners have completed the required actions for PerformBrokerAnalysis
        completed_readers = set(
            memory.sent_from
            for memory in current_round_memories
            if memory.cause_by in [
                "actions.read_product.SimpleDataProductReader",
                "actions.context_read.ContextAwareProductReader",
            ]
        )

        if {self.ownerA, self.ownerB}.issubset(completed_readers) or \
        {self.ownerA_2, self.ownerB_2}.issubset(completed_readers):
            # Trigger PerformBrokerAnalysis if not already set
            if not isinstance(self.rc.todo, PerformBrokerAnalysis):
                logger.info(f"{self.name}: Triggering PerformBrokerAnalysis.")
                self.rc.todo = PerformBrokerAnalysis()
                return await self._act()

        # Check if owners have completed the required actions for CreateCompatibilityReport
        completed_mismatches = set(
            memory.sent_from
            for memory in current_round_memories
            if memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier"
        )

        if {self.ownerA, self.ownerB}.issubset(completed_mismatches) or \
        {self.ownerA_2, self.ownerB_2}.issubset(completed_mismatches):
            # Trigger CreateCompatibilityReport if not already set
            if not isinstance(self.rc.todo, CreateCompatibilityReport):
                logger.info(f"{self.name}: Triggering CreateCompatibilityReport.")
                self.rc.todo = CreateCompatibilityReport()
                return await self._act()

        # Default to waiting for relevant actions
        logger.debug(f"{self.name}: Waiting for required actions to complete.")
        return None

    async def _act(self) -> Message:
        logger.info(f"{self.name}: Executing {self.rc.todo.name}")
        todo = self.rc.todo

        if isinstance(todo, PerformBrokerAnalysis):
            # Perform broker analysis between two data products
            memories = self.get_memories()
            current_round_memories = [
                memory for memory in memories if memory.round == self.rc.round
            ]
            productA_desc = ""
            productB_desc = ""

            for memory in current_round_memories:
                if memory.cause_by == "actions.read_product.SimpleDataProductReader":
                    if memory.sent_from == self.ownerA:
                        productA_desc = memory.content
                    elif memory.sent_from == self.ownerB:
                        productB_desc = memory.content

            if productA_desc and productB_desc:
                result = await todo.run(productA_desc, productB_desc)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.perform_broker_analysis.PerformBrokerAnalysis",
                    sent_from=self.name,
                    send_to=[self.ownerA, self.ownerB]
                )
            else:
                logger.warning(f"{self.name} is waiting for product descriptions.")
                return None

        elif isinstance(todo, CreateCompatibilityReport):
            # Create or update the compatibility report
            memories = self.get_memories()
            current_round_memories = [
                memory for memory in memories if memory.round == self.rc.round
            ]
            mismatchA = ""
            mismatchB = ""
            existing_report = ""

            for memory in current_round_memories:
                if memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    if memory.sent_from == self.ownerA:
                        mismatchA = memory.content
                    elif memory.sent_from == self.ownerB:
                        mismatchB = memory.content

            if os.path.exists(self.report_file):
                with open(self.report_file, "r") as file:
                    existing_report = file.read()

            if mismatchA and mismatchB:
                result = await todo.run(mismatchA, mismatchB, existing_report)
                with open(self.report_file, "w") as file:
                    file.write(result)

                msg = Message(
                    content="Compatibility report updated.",
                    role=self.profile,
                    cause_by="actions.create_report.CreateCompatibilityReport",
                    sent_from=self.name,
                    send_to=[self.ownerA, self.ownerB]
                )
            else:
                logger.warning(f"{self.name} is waiting for mismatch data.")
                return None

        self.rc.memory.add(msg)
        return msg