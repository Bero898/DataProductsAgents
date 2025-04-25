# phased_role.py  (same as before – one generic place)
from metagpt.roles import Role
from metagpt.schema import Message


class PhaseShiftMixin(Role):
    """After the first complete sweep, restart every later sweep at `phase_start`."""
    
    phase_start: int = 0
    _first_round_done: bool = False

    async def _act_by_order(self) -> Message:
        start_idx = 0 if not self._first_round_done else self.phase_start
        start_idx = min(start_idx, len(self.states) - 1)

        rsp: Message | None = None
        for i in range(start_idx, len(self.states)):
            self._set_state(i)
            rsp = await self._act()

        self._first_round_done = True
        return rsp or Message(content="No actions executed")
