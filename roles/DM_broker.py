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
    report_file: str = "compatibility_report.txt"  # File to store the report

    def __init__(self, name: str = "Connor", ownerA: str = "", ownerB: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.ownerA = ownerA
        self.ownerB = ownerB
        self.set_actions([PerformBrokerAnalysis, CreateCompatibilityReport])
        self._watch([PerformBrokerAnalysis, CreateCompatibilityReport])
        self.current_round = 1  # Default round

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        if isinstance(todo, PerformBrokerAnalysis):
            # Perform broker analysis between two data products
            memories = self.get_memories()
            productA = ""
            productB = ""

            for memory in memories:
                if memory.cause_by == "actions.read_product.SimpleDataProductReader" or memory.cause_by == "actions.assess_compatibility.ContextAwareProductReader":
                    if memory.sent_from == self.ownerA:
                        productA = memory.content
                    elif memory.sent_from == self.ownerB:
                        productB = memory.content

            if productA and productB:
                result = await todo.run(productA, productB)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.perform_broker_analysis.PerformBrokerAnalysis",
                    sent_from=self.name,
                    send_to=[self.ownerA, self.ownerB]
                )
            else:
                msg = Message(
                    content="Waiting for both data product descriptions to perform analysis.",
                    role=self.profile,
                    cause_by="actions.perform_broker_analysis.PerformBrokerAnalysis",
                    sent_from=self.name,
                    send_to=[self.ownerA, self.ownerB]
                )

        elif isinstance(todo, CreateCompatibilityReport):
            # Create or update the compatibility report
            memories = self.get_memories()
            mismatchA = ""
            mismatchB = ""

            for memory in memories:
                if memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    if memory.sent_from == self.ownerA:
                        mismatchA = memory.content
                    elif memory.sent_from == self.ownerB:
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
                send_to=[self.ownerA, self.ownerB]
            )

        else:
            msg = Message(
                content="I don't know how to handle this action.",
                role=self.profile,
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.ownerA, self.ownerB]
            )

        self.rc.memory.add(msg)
        return msg