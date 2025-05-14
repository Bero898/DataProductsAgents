from metagpt.roles.role import Role
from actions.read_product import SimpleDataProductReader
from actions.assess_compatibility import SimpleDataProductComposer
from actions.analyze_mismatch import MismatchIdentifier
from metagpt.schema import Message
from metagpt.logs import logger


class DPOwner(Role):
    name: str = "Alice"
    profile: str = "Data Product Owner"
    data_product: str = ""
    opponent_name: str = ""
    requester: bool = True
    opponent_successor: str = ""
    successor: str = ""
    broker: str = ""

    def __init__(self, name: str = "Alice", successor: str = "Alice2", data_product: str = "", opponent_name: str = "", opponent_successor: str = "", requester: bool = True, broker: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name
        self.opponent_successor = opponent_successor
        self.successor = successor
        self.broker = broker
        self.requester = requester #requester goes first, requested (i.e. when False) goes second
        self.set_actions([SimpleDataProductReader, SimpleDataProductComposer, MismatchIdentifier])
        self._watch([SimpleDataProductReader, SimpleDataProductComposer, MismatchIdentifier])
    
    async def _observe(self) -> int:
        await super()._observe()
        # Process messages sent directly to this agent or broadcast messages
        self.rc.news = [
            msg for msg in self.rc.news 
            if self.name in msg.send_to or  
                "All" in (msg.send_to if isinstance(msg.send_to, list) else [msg.send_to])
        ]

        return len(self.rc.news)
    
    async def react(self) -> Message:
        # Ensure the correct sequence of actions
        if not self.rc.news:
            # If there's no news, use SimpleDataProductReader as the default first action
            self.rc.todo = SimpleDataProductReader()
        else:
            # Process the latest message
            latest_msg = self.rc.news[-1]

            # Check if SimpleDataProductReader has already been executed
            memories = self.get_memories()
            has_read_product = any(
                memory.cause_by == "actions.read_product.SimpleDataProductReader" and memory.sent_from == self.name
                for memory in memories
            )

            if not has_read_product:
                # Ensure SimpleDataProductReader is executed first
                self.rc.todo = SimpleDataProductReader()
            elif latest_msg.cause_by == "actions.read_product.SimpleDataProductReader" or latest_msg.cause_by == "actions.perform_broker_analysis.PerformBrokerAnalysis":
                # After reading the data product, assess compatibility
                self.rc.todo = SimpleDataProductComposer()
            elif latest_msg.cause_by == "actions.assess_compatibility.SimpleDataProductComposer":
                if self.requester:
                    # if the action before me was SimpleDataProductComposer and I'm the requester
                    # I should perform the MismatchIdentifier action
                    # After compatibility assessment, identify mismatches
                    self.rc.todo = MismatchIdentifier()
                else:
                    # if the action before me was SimpleDataProductComposer and I'm the requested
                    # I should perform the SimpleDataProductComposer action
                    self.rc.todo = SimpleDataProductComposer()
            elif latest_msg.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                if self.requester:
                    # if the action before me was MismatchIdentifier and I'm the requester
                    # I should perform wait for the opponent to perform an action
                    logger.debug(f"{self.name}: Waiting for required actions to complete.")
                    return None

                else:
                    # if the action before me was MismatchIdentifier and I'm the requested
                    # I should perform the MismatchIdentifier action
                    # After mismatch identification, read the data product again
                    self.rc.todo = MismatchIdentifier()

            else:
                # Default to reading the data product
                self.rc.todo = SimpleDataProductReader()

        # Log the selected action
        logger.info(f"{self.name} selected action: {self.rc.todo.name}")

        # Execute the action using _act
        return await self._act()
    
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
                send_to=[self.opponent_name, self.successor, self.opponent_successor, self.broker]
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
                if own_desc != "" and opponent_desc != "":
                    break   
            
            if own_desc and opponent_desc:
                result = await todo.run(own_desc, opponent_desc)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.assess_compatibility.SimpleDataProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.successor, self.opponent_successor, self.name]
                )
            else:
                msg = Message(
                    content=f"I'm still waiting for product descriptions. I have my own: {bool(own_desc)}, opponent's: {bool(opponent_desc)}",
                    role=self.profile,
                    cause_by="actions.assess_compatibility.SimpleDataProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.successor, self.opponent_successor, self.name]
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
                elif memory.cause_by == "actions.perform_broker_analysis.PerformBrokerAnalysis" and memory.sent_from == self.broker:
                    assessmentC = memory.content
                if assessmentA != "" and assessmentB !="" and assessmentC != "":
                    break


            if assessmentA and assessmentB:
                result = await todo.run(assessmentA=assessmentA, assessmentB=assessmentB,assessmentC=assessmentC)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.successor, self.opponent_successor, self.broker]
                )
            else:
                msg = Message(
                    content="Waiting for compatibility assessment...",
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.successor, self.opponent_successor, self.broker]
                )
        
        else:
            msg = Message(
                content="I don't know how to handle this action.", 
                role=self.profile, 
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.opponent_name, self.successor, self.opponent_successor, self.broker]
            )
        
        self.rc.memory.add(msg)
        return msg