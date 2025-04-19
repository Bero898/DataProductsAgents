from metagpt.roles.role import Role,RoleReactMode
from actions.read_product import SimpleDataProductReader
from actions.assess_compatibility import SimpleDataProductComposer
from actions.analyze_mismatch import MismatchIdentifier
from metagpt.schema import Message
from metagpt.logs import logger


class DPOwner(Role):
    name: str = "Alice"
    profile: str = "Data Product Reader"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleDataProductReader,SimpleDataProductComposer,MismatchIdentifier])
        # self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
        self._set_react_mode(react_mode = RoleReactMode.PLAN_AND_ACT.value)
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        # By choosing the Action by order under the hood
        # todo will be first SimpleWriteCode() then SimpleRunCode()
        todo = self.rc.todo

        msg = self.get_memories(k=1)[0]  # find the most k recent messages
        result = await todo.run(msg.content)

        msg = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg)
        return msg