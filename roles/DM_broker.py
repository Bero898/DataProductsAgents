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
    data_product: str = ""
    ownerA: str = ""  # Owner of the first data product
    ownerB: str = ""  # Owner of the second data product
    ownerA_2: str = ""  # Owner of the first data product
    ownerB_2: str = ""  # Owner of the second data product
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
            "actions.assess_compatibility.ContextAwareProductReader",
        ]:
            # Check if both owners have completed their product readers
            memories = self.get_memories()
            productA_done = any(
                memory.cause_by in [
                    "actions.read_product.SimpleDataProductReader",
                    "actions.assess_compatibility.ContextAwareProductReader",
                ]
                and memory.sent_from in [self.ownerA, self.ownerA_2]
                for memory in memories
            )
            productB_done = any(
                memory.cause_by in [
                    "actions.read_product.SimpleDataProductReader",
                    "actions.assess_compatibility.ContextAwareProductReader",
                ]
                and memory.sent_from in [self.ownerB, self.ownerB_2]
                for memory in memories
            )

            if productA_done and productB_done:
                # Trigger PerformBrokerAnalysis
                self.rc.todo = PerformBrokerAnalysis()
            else:
                logger.debug(f"{self.name}: Waiting for both product readers to complete.")

        elif latest_msg.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
            # Check if both owners have completed their mismatch identifiers
            memories = self.get_memories()
            mismatchA_done = any(
                memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier"
                and memory.sent_from in [self.ownerA, self.ownerA_2]
                for memory in memories
            )
            mismatchB_done = any(
                memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier"
                and memory.sent_from in [self.ownerB, self.ownerB_2]
                for memory in memories
            )

            if mismatchA_done and mismatchB_done:
                # Trigger CreateCompatibilityReport
                self.rc.todo = CreateCompatibilityReport()
            else:
                logger.debug(f"{self.name}: Waiting for both mismatch identifiers to complete.")

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
                    "actions.assess_compatibility.ContextAwareProductReader",
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
                    send_to=[self.ownerA, self.ownerB , self.ownerA_2, self.ownerB_2],
                )

        elif isinstance(todo, CreateCompatibilityReport):
            # Create or update the compatibility report
            memories = self.get_memories()
            mismatchA = ""
            mismatchB = ""

            for memory in memories:
                if memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    if memory.sent_from in [self.ownerA, self.ownerA_2]:
                        mismatchA = memory.content
                    elif memory.sent_from in [self.ownerB, self.ownerB_2]:
                        mismatchB = memory.content

            # Read existing report content if the file exists
            report_content = ""
            if os.path.exists(self.report_file):
                with open(self.report_file, "r") as file:
                    report_content = file.read()

            result = await todo.run(mismatchA, mismatchB, report_content)

            # Write the updated report to the file
            with open(self.report_file, "w") as file:
                file.write(result)

            msg = Message(
                content=f"Updated compatibility report:\n{result}",
                role=self.profile,
                cause_by="actions.create_report.CreateCompatibilityReport",
                sent_from=self.name,
                send_to=[self.ownerA, self.ownerB],
            )

        else:
            msg = Message(
                content="I don't know how to handle this action.",
                role=self.profile,
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.ownerA, self.ownerB],
            )

        self.rc.memory.add(msg)
        return msg