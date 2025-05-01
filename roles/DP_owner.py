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

    def __init__(self, name: str = "Alice", data_product: str = "", opponent_name: str = "", opponent_2_name: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name
        self.opponent_2_name = opponent_2_name
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
        # Override the default react method to handle specific actions without planning
        if not self.rc.news:
            # If there's no news, use SimpleDataProductReader as default first action
            self.rc.todo = SimpleDataProductReader()
        else:
            # Process the latest message
            latest_msg = self.rc.news[-1]
            
            # Check what action to take based on conversation state
            if "Analyze your data product" in latest_msg.content:
                # Initial instruction - read data product
                self.rc.todo = SimpleDataProductReader()
            
            elif latest_msg.cause_by == "actions.read_product.SimpleDataProductReader":
                # After a data product is read, assess compatibility
                self.rc.todo = SimpleDataProductComposer()
            
            elif latest_msg.cause_by == "actions.assess_compatibility.SimpleDataProductComposer":
                # After compatibility assessment, identify mismatches
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
                send_to=[self.opponent_name, self.opponent_2_name]  # Send directly to opponent instead of "All"
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
            
            if own_desc and opponent_desc:
                result = await todo.run(own_desc, opponent_desc)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.assess_compatibility.SimpleDataProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.opponent_2_name]  # Send directly to opponent instead of "All"
                )
            else:
                msg = Message(
                    content=f"I'm still waiting for product descriptions. I have my own: {bool(own_desc)}, opponent's: {bool(opponent_desc)}",
                    role=self.profile,
                    cause_by="actions.assess_compatibility.SimpleDataProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.opponent_2_name]  # Send directly to opponent instead of "All"
                )
        
        elif isinstance(todo, MismatchIdentifier):
            # Get compatibility assessment
            memories = self.get_memories()
            assessment = ""
            
            for memory in memories:
                if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == self.name:
                    assessment = memory.content
                    break
            
            if assessment:
                result = await todo.run(assessment)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.opponent_2_name]  # Send directly to opponent instead of "All"
                )
            else:
                msg = Message(
                    content="Waiting for compatibility assessment...",
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.opponent_2_name]
                )
        
        else:
            msg = Message(
                content="I don't know how to handle this action.", 
                role=self.profile, 
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.opponent_name, self.opponent_2_name]  # Send directly to opponent instead of "All"
            )
        
        self.rc.memory.add(msg)
        return msg