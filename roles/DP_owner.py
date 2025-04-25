# dp_owner.py
from roles.phased_role import PhaseShiftMixin
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

from actions.read_product import (
    SimpleDataProductReader, ContextAwareProductReader
)
from actions.assess_compatibility import (
    SimpleDataProductComposer, DiscourseAwareComposer
)
from actions.analyze_mismatch import MismatchIdentifier


class DPOwner(PhaseShiftMixin, Role):
    """
    • Round‑1 runs all six actions in order.
    • Later rounds restart at ContextAwareProductReader (index‑6 ⇢ phase_start=6).
    """
    name: str = ""
    profile: str = "Data Product Owner"
                

    def __init__(self, name: str = "", data_product: str = "", opponent_name: str = "", **kw):
        super().__init__(name=name, **kw)  # <- ensures Role sees it
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name

        self.set_actions([                     # indices shown for clarity
            SimpleDataProductReader,           # 0
            SimpleDataProductReader,           # 1  (opponent’s turn is handled by Team scheduling)
            SimpleDataProductComposer,         # 2
            SimpleDataProductComposer,         # 3
            MismatchIdentifier,                # 4
            MismatchIdentifier,                # 5
            ContextAwareProductReader,         # 6   ← phase restart
            ContextAwareProductReader,         # 7
            DiscourseAwareComposer,            # 8
            DiscourseAwareComposer,            # 9
            MismatchIdentifier,                # 10
            MismatchIdentifier,                # 11
        ])

        self._set_react_mode("by_order")       # MetaGPT will call our custom _act_by_order
        self._watch(self.states)               # store every action’s messages

    # ── the only code that is still custom: how to really execute one action ──
    async def _act(self) -> Message:
        todo = self.rc.todo
        logger.info(f"{self.name}: executing {todo.name}")

        # Dispatch table keeps this method short
        handler = {
            SimpleDataProductReader: self._do_read,
            ContextAwareProductReader: self._do_ctx_read,
            SimpleDataProductComposer: self._do_compose,
            DiscourseAwareComposer:    self._do_discourse,
            MismatchIdentifier:        self._do_mismatch,
        }.get(type(todo), self._unknown)

        return await handler(todo)

    # ── tiny helpers, each < 15 lines ─────────────────────────────────────────

    async def _do_read(self, todo):
        result = await todo.run(self.data_product)
        return self._mk_msg(result, todo)

    async def _do_ctx_read(self, todo):
        compat, mism = self._latest("Composer"), self._latest("Mismatch")
        result = await todo.run(self.data_product, compat, mism)
        return self._mk_msg(result, todo)

    async def _do_compose(self, todo):
        own, opp = self._latest_read(self.name), self._latest_read(self.opponent_name)
        result = await todo.run(own, opp)
        return self._mk_msg(result, todo)


    async def _do_discourse(self, todo):
        data = {k: self._latest_by_agent(k) for k in
                ("Reader", "Composer", "Mismatch")}
        
        print(f"Data: {data}")
        if not all(data.values()):
            return self._mk_msg("Waiting for complete context.", todo)
        own, opp = data["Reader"][self.name], data["Reader"][self.opponent_name]
        compA, compB = data["Composer"][self.name], data["Composer"][self.opponent_name]
        misA, misB = data["Mismatch"][self.name], data["Mismatch"][self.opponent_name]
        result = await todo.run(own, opp, compA, misA, compB, misB)
        return self._mk_msg(result, todo)

    async def _do_mismatch(self, todo):
        comp = self._latest("Composer", self.name)
        result = await todo.run(comp)
        return self._mk_msg(result, todo)

    async def _unknown(self, todo):
        return self._mk_msg("I don't know this action", todo)

    # ── generic utilities ────────────────────────────────────────────────────
    #original ones
    
    def _latest(self, cause_substr: str, sender: str | None = None):
        for mem in reversed(self.get_memories()):
            if cause_substr in mem.cause_by and (sender is None or mem.sent_from == sender):
                return mem.content
        return ""

    def _latest_read(self, sender):
        for mem in reversed(self.get_memories()):
            if mem.cause_by.endswith("SimpleDataProductReader") and mem.sent_from == sender:
                return mem.content
        return ""
    
    #new ones
    def _latest_by_agent(self, cause_substr: str) -> dict[str, str]:
        """Return newest message of each sender that matches `cause_substr`."""
        seen = {}
        for mem in reversed(self.get_memories()):
            if cause_substr in mem.cause_by and mem.sent_from not in seen:
                seen[mem.sent_from] = mem.content
                if len(seen) == 2:          # we only need self & opponent
                    break
        return seen                       # {'Alice': '...', 'Bob': '...'}


    def _mk_msg(self, content, todo):
        msg = Message(
            content=content,
            role=self.profile,
            cause_by=f"{todo.__module__}.{todo.__class__.__name__}",
            sent_from=self.name,
            send_to=[self.opponent_name],
        )
        self.rc.memory.add(msg)
        return msg
