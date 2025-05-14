from metagpt.roles.role import Role
from actions.read_product import SimpleDataProductReader
from actions.assess_compatibility import SimpleDataProductComposer
from actions.analyze_mismatch import MismatchIdentifier
from metagpt.schema import Message
from metagpt.logs import logger
from actions.read_product import ContextAwareProductReader
from actions.assess_compatibility import ContextAwareProductComposer


class DPOwner(Role):
    current_round: int = 1  # Default to 1
    name: str = "Alice"
    profile: str = "Data Product Owner"
    data_product: str = ""
    opponent_name: str = ""
    broker: str = ""

    def __init__(self, name: str = "Alice", data_product: str = "", opponent_name: str = "", broker: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name
        self.set_actions([SimpleDataProductReader, SimpleDataProductComposer, ContextAwareProductComposer, ContextAwareProductReader, MismatchIdentifier])
        self._watch([SimpleDataProductReader, SimpleDataProductComposer, MismatchIdentifier])
        self.current_round = 1  # Default round
        self.goal = "First, Analyze your data product. Then, if your opponent has also analyzed their data product, assess compatibility. Finally, if your opponent has also assessed compatibility, identify mismatches in the data products."
        self.broker = broker
        

    async def _observe(self) -> int:
        await super()._observe()
        # Process messages sent directly to this agent or broadcast messages
        self.rc.news = [
            msg for msg in self.rc.news 
            if self.name in msg.send_to or  
                "All" in (msg.send_to if isinstance(msg.send_to, list) else [msg.send_to])
        ]

        return len(self.rc.news)
    
    
    def _has_required_inputs_for_discourse(self) -> bool:
        memories = self.get_memories()
        required_inputs = ["compatibilityA", "mismatchesA", "compatibilityB", "mismatchesB"]
        available_inputs = {key: False for key in required_inputs}

        for memory in memories:
            if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer":
                if memory.sent_from == self.name:
                    available_inputs["compatibilityA"] = True
                elif memory.sent_from == self.opponent_name:
                    available_inputs["compatibilityB"] = True
            elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                if memory.sent_from == self.name:
                    available_inputs["mismatchesA"] = True
                elif memory.sent_from == self.opponent_name:
                    available_inputs["mismatchesB"] = True

        return all(available_inputs.values())
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        if isinstance(todo, SimpleDataProductReader):
            # Read own data product
            result = await todo.run(self.data_product)
            msg = Message(
                content=result,
                role=self.profile,
                cause_by="actions.read_product.SimpleDataProductReader",
                sent_from=self.name,
                send_to=[self.opponent_name, self.broker]  # Send directly to opponent instead of "All"
            )
        
        elif isinstance(todo, SimpleDataProductComposer):
            
            # Get own product description and opponent's product description
            memories = self.get_memories()
            own_desc = ""
            opponent_desc = ""
            
            # Search for product descriptions in messages
            for memory in memories:
                if memory.cause_by == "actions.read_product.SimpleDataProductReader":
                    if memory.sent_from == self.name:
                        own_desc = memory.content
                    elif memory.sent_from == self.opponent_name:
                        opponent_desc = memory.content
                    if own_desc != "" and opponent_desc !="":
                        break
            
            if own_desc and opponent_desc:
                result = await todo.run(own_desc, opponent_desc)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.assess_compatibility.SimpleDataProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.broker]
                )
            else:
                msg = Message(
                    content=f"I'm still waiting for product descriptions. I have my own: {bool(own_desc)}, opponent's: {bool(opponent_desc)}",
                    role=self.profile,
                    cause_by="actions.assess_compatibility.SimpleDataProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.broker]
                )
        
        elif isinstance(todo, MismatchIdentifier):
            # Get compatibility assessment
            memories = self.get_memories()
            assessmentA = ""
            assessmentB = ""
            assessmentC = ""
            for memory in memories:
                if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == self.name:
                    assessmentA = memory.content
                elif memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == self.opponent_name:
                    assessmentB = memory.content
                if memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer" and memory.sent_from == self.name:
                    assessmentA = memory.content
                elif memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer" and memory.sent_from == self.opponent_name:
                    assessmentB = memory.content
                elif memory.cause_by == "actions.perform_broker_analysis.PerformBrokerAnalysis" and memory.sent_from == self.broker:
                    assessmentC = memory.content
                if assessmentA != "" and assessmentB !="" and assessmentC != "":
                    break

            
            if assessmentA and assessmentB and assessmentC:
                result = await todo.run(assessmentA=assessmentA, assessmentB=assessmentB, assessmentC=assessmentC)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.broker]
                )
            else:
                msg = Message(
                    content="Waiting for compatibility assessment...",
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.broker]
                )
        elif isinstance(todo, ContextAwareProductReader):
            # Read own data product with context
            memories = self.get_memories()
            compatibility = ""
            mismatches = ""
            
            for memory in memories:
                if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == self.name:
                    compatibility = memory.content
                elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier" and memory.sent_from == self.name:
                    mismatches = memory.content
                if compatibility != "" and mismatches !="":
                    break
            
            result = await todo.run(self.data_product, compatibility, mismatches)
            msg = Message(
                content=result,
                role=self.profile,
                cause_by="actions.read_product.ContextAwareProductReader",
                sent_from=self.name,
                send_to=[self.opponent_name, self.broker]
            )
        
        elif isinstance(todo, ContextAwareProductComposer):
            memories = self.get_memories()
            own_desc = ""
            opponent_desc = ""
            compatibilityA = ""
            mismatchesA = ""
            compatibilityB = ""
            mismatchesB = ""

            # Extract relevant information from memory
            for memory in memories:
                if memory.cause_by == "actions.read_product.SimpleDataProductReader":
                    if memory.sent_from == self.name:
                        own_desc = memory.content
                    elif memory.sent_from == self.opponent_name:
                        opponent_desc = memory.content

                elif memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer":
                    if memory.sent_from == self.name:
                        compatibilityA = memory.content
                    elif memory.sent_from == self.opponent_name:
                        compatibilityB = memory.content

                elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    if memory.sent_from == self.name:
                        mismatchesA = memory.content
                    elif memory.sent_from == self.opponent_name:
                        mismatchesB = memory.content
                if own_desc != "" and opponent_desc !="" and compatibilityA != "" and mismatchesA !="" and compatibilityB != "" and mismatchesB !="":
                    break

            # Check if all required inputs are available
            if all([own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB]):
                result = await todo.run(own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.assess_compatibility.ContextAwareProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name]
                )
            else:
                # Log missing inputs and defer execution
                missing_inputs = []
                if not own_desc:
                    missing_inputs.append("own_desc")
                if not opponent_desc:
                    missing_inputs.append("opponent_desc")
                if not compatibilityA:
                    missing_inputs.append("compatibilityA")
                if not mismatchesA:
                    missing_inputs.append("mismatchesA")
                if not compatibilityB:
                    missing_inputs.append("compatibilityB")
                if not mismatchesB:
                    missing_inputs.append("mismatchesB")
                logger.warning(f"{self.name} is waiting for complete context: missing {', '.join(missing_inputs)}.")

                msg = Message(
                    content=f"Waiting for complete context: missing {', '.join(missing_inputs)}.",
                    role=self.profile,
                    cause_by="actions.assess_compatibility.ContextAwareProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.broker]
                )
        else:
            msg = Message(
                content="I don't know how to handle this action.", 
                role=self.profile, 
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.opponent_name, self.broker]
            )
        
        self.rc.memory.add(msg)
        return msg