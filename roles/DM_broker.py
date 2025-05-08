# Data Mesh Broker Agent
from metagpt.roles.role import Role
from actions.perform_broker_analysis import PerformBrokerAnalysis
from actions.create_report import CreateCompatibilityReport
from metagpt.schema import Message
from metagpt.logs import logger
import os


class DMBroker(Role):
    current_round: int = 1  # Default to 1
    name: str = "Connor"
    profile: str = "Data Mesh Broker"
    report_file: str = "compatibility_report.txt"  # File to store the report

    def __init__(self, name: str = "Connor", ownerA: str = "", ownerB: str = "", ownerA_2: str = "", ownerB_2: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.ownerA = ownerA
        self.ownerB = ownerB
        self.ownerA_2 = ownerA_2
        self.ownerB_2 = ownerB_2
        self.set_actions([PerformBrokerAnalysis, CreateCompatibilityReport])
        self._watch([PerformBrokerAnalysis, CreateCompatibilityReport])
        self.current_round = 1  # Default round

    async def react(self) -> Message:
        # Override the default react method to handle specific actions without planning
        if not self.rc.news:
            # If there's no news, wait for updates
            logger.debug(f"{self.name}: No news to process.")
            return None

        # Process the latest message
        latest_msg = self.rc.news[-1]

        # Check what action to take based on conversation state
        if latest_msg.cause_by in [
            "actions.read_product.SimpleDataProductReader",
            "actions.read_product.ContextAwareProductReader",
        ]:
            # Check if any two owners have completed their product readers
            memories = self.get_memories()
            completed_readers = set(
                memory.sent_from
                for memory in memories
                if memory.cause_by in [
                    "actions.read_product.SimpleDataProductReader",
                    "actions.read_product.ContextAwareProductReader",
                ]
            )

            if {self.ownerA, self.ownerB}.issubset(completed_readers) or \
               {self.ownerA_2, self.ownerB_2}.issubset(completed_readers):
                # Trigger PerformBrokerAnalysis
                self.rc.todo = PerformBrokerAnalysis()
            else:
                logger.debug(f"{self.name}: Waiting for product readers from all owners.")

        elif latest_msg.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
            # Check if all owners have completed their mismatch identifiers
            memories = self.get_memories()
            completed_mismatches = set(
                memory.sent_from
                for memory in memories
                if memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier"
            )

            if {self.ownerA, self.ownerB, self.ownerA_2, self.ownerB_2}.issubset(completed_mismatches):
                # Trigger CreateCompatibilityReport
                self.rc.todo = CreateCompatibilityReport()
            else:
                logger.debug(f"{self.name}: Waiting for mismatch identifiers from all owners.")

        else:
            # Default to waiting for relevant actions
            logger.debug(f"{self.name}: No relevant actions to process.")
            return None

        # Log the selected action
        logger.info(f"{self.name} selected action: {self.rc.todo.name}")

        # Execute the action using _act
        return await self._act()

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        if isinstance(todo, PerformBrokerAnalysis):
            # Perform broker analysis between two data products
            memories = self.get_memories()
            productA = ""
            productB = ""

            for memory in memories:
                if memory.cause_by in [
                    "actions.read_product.SimpleDataProductReader",
                    "actions.read_product.ContextAwareProductReader",
                ]:
                    if memory.sent_from in [self.ownerA, self.ownerA_2]:
                        productA = memory.content
                    elif memory.sent_from in [self.ownerB, self.ownerB_2]:
                        productB = memory.content

            if productA and productB:
                result = await todo.run(productA, productB)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.perform_broker_analysis.PerformBrokerAnalysis",
                    sent_from=self.name,
                    send_to=[self.ownerA, self.ownerB, self.ownerA_2, self.ownerB_2],
                )
            else:
                msg = Message(
                    content="Waiting for both data product descriptions to perform analysis.",
                    role=self.profile,
                    cause_by="actions.perform_broker_analysis.PerformBrokerAnalysis",
                    sent_from=self.name,
                    send_to=[self.ownerA, self.ownerB, self.ownerA_2, self.ownerB_2],
                )

        elif isinstance(todo, CreateCompatibilityReport):
            # Create or update the compatibility report
            memories = self.get_memories()
            mismatches = {self.ownerA: "", self.ownerB: "", self.ownerA_2: "", self.ownerB_2: ""}

            for memory in memories:
                if memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    mismatches[memory.sent_from] = memory.content

            # Read existing report content if the file exists
            report_content = ""
            if os.path.exists(self.report_file):
                with open(self.report_file, "r") as file:
                    report_content = file.read()

            result = await todo.run(
                mismatches[self.ownerA],
                mismatches[self.ownerB],
                mismatches[self.ownerA_2] + "\n" + mismatches[self.ownerB_2],
                report_content,
            )

            # Write the updated report to the file
            with open(self.report_file, "w") as file:
                file.write(result)

            msg = Message(
                content=f"Updated compatibility report:\n{result}",
                role=self.profile,
                cause_by="actions.create_report.CreateCompatibilityReport",
                sent_from=self.name,
                send_to=[self.ownerA, self.ownerB, self.ownerA_2, self.ownerB_2],
            )

        else:
            msg = Message(
                content="I don't know how to handle this action.",
                role=self.profile,
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.ownerA, self.ownerB, self.ownerA_2, self.ownerB_2],
            )

        self.rc.memory.add(msg)
        return msg