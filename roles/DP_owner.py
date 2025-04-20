from metagpt.roles.role import Role, RoleReactMode
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

    def __init__(self, name: str = "Alice", data_product: str = "", opponent_name: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name
        self.set_actions([SimpleDataProductReader, SimpleDataProductComposer, MismatchIdentifier])
        self._set_react_mode(react_mode=RoleReactMode.PLAN_AND_ACT.value)
        self._watch([SimpleDataProductReader, SimpleDataProductComposer, MismatchIdentifier])
    
    async def _observe(self) -> int:
        await super()._observe()
        # Accept messages sent to self
        self.rc.news = [msg for msg in self.rc.news if msg.send_to == {self.name} or msg.send_to == "All"]
        return len(self.rc.news)
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        if isinstance(todo, SimpleDataProductReader):
            # Read own data product
            result = await todo.run(self.data_product)
            msg = Message(
                content=result,
                role=self.profile,
                cause_by=type(todo),
                sent_from=self.name,
                send_to="All"  # Share description with all
            )
        
        elif isinstance(todo, SimpleDataProductComposer):
            # Get own product description and opponent's product description
            memories = self.get_memories()
            own_desc = next((msg.content for msg in memories 
                         if msg.sent_from == self.name and isinstance(msg.cause_by(), SimpleDataProductReader)), "")
            opponent_desc = next((msg.content for msg in memories 
                               if msg.sent_from == self.opponent_name and isinstance(msg.cause_by(), SimpleDataProductReader)), "")
            
            if own_desc and opponent_desc:
                result = await todo.run(own_desc, opponent_desc)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by=type(todo),
                    sent_from=self.name,
                    send_to="All"  # Share assessment with all
                )
            else:
                msg = Message(
                    content="Waiting for product descriptions...",
                    role=self.profile,
                    cause_by=type(todo),
                    sent_from=self.name,
                    send_to="All"
                )
        
        elif isinstance(todo, MismatchIdentifier):
            # Get compatibility assessment
            memories = self.get_memories()
            assessment = next((msg.content for msg in memories 
                           if msg.sent_from == self.name and isinstance(msg.cause_by(), SimpleDataProductComposer)), "")
            
            if assessment:
                result = await todo.run(assessment)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by=type(todo),
                    sent_from=self.name,
                    send_to=self.opponent_name
                )
            else:
                msg = Message(
                    content="Waiting for compatibility assessment...",
                    role=self.profile,
                    cause_by=type(todo),
                    sent_from=self.name,
                    send_to=self.opponent_name
                )
        
        else:
            latest_msg = self.get_memories(k=1)[0] if self.get_memories() else None
            content = latest_msg.content if latest_msg else ""
            result = await todo.run(content)
            msg = Message(
                content=result, 
                role=self.profile, 
                cause_by=type(todo),
                sent_from=self.name,
                send_to="All"
            )
        
        self.rc.memory.add(msg)
        return msg