from metagpt.roles.role import Role
from actions.context_read import ContextAwareProductReader
from actions.context_compatibility import DiscourseAwareComposer
from actions.analyze_mismatch import MismatchIdentifier
from metagpt.schema import Message
from metagpt.logs import logger


class ContextDPOwner(Role):
    name: str = "Alice"
    profile: str = "Data Product Owner"
    data_product: str = ""
    opponent_name: str = ""

    def __init__(self, name: str = "Alice", data_product: str = "", opponent_name: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name
        self.set_actions([ContextAwareProductReader, DiscourseAwareComposer, MismatchIdentifier])
        self._watch([ContextAwareProductReader, DiscourseAwareComposer, MismatchIdentifier])
    
    async def _observe(self) -> int:
        await super()._observe()
        # Process messages sent directly to this agent or broadcast messages
        self.rc.news = [
            msg for msg in self.rc.news
            if self.name in msg.send_to or
            (self.name == "Alice2" and msg.sent_from == "Alice") or
            (self.name == "Bob2" and msg.sent_from == "Bob")
        ]
        return len(self.rc.news)
    
    async def react(self) -> Message:
        # Ensure the correct sequence of actions
        if not self.rc.news:
            # If there's no news, use ContextAwareProductReader as the default first action
            logger.error(f"{self.name} has no news, failed to collect context")
            self.rc.todo = ContextAwareProductReader()
        else:
            # Process the latest message
            latest_msg = self.rc.news[-1]

            # Check if ContextAwareProductReader has already been executed
            memories = self.get_memories()
            has_read_context = any(
                memory.cause_by == "actions.read_product.ContextAwareProductReader" and memory.sent_from == self.name
                for memory in memories
            )

            if not has_read_context:
                # Ensure ContextAwareProductReader is executed first
                self.rc.todo = ContextAwareProductReader()
            elif latest_msg.cause_by == "actions.read_product.ContextAwareProductReader":
                # After reading the context, assess compatibility
                self.rc.todo = DiscourseAwareComposer()
            elif latest_msg.cause_by == "actions.assess_compatibility.DiscourseAwareComposer":
                # After compatibility assessment, identify mismatches
                self.rc.todo = MismatchIdentifier()
            else:
                # Default to reading the context
                self.rc.todo = ContextAwareProductReader()

        # Log the selected action
        logger.info(f"{self.name} selected action: {self.rc.todo.name}")

        # Execute the action using _act
        return await self._act()
    
    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        if isinstance(todo, ContextAwareProductReader):
            # Extract context from previous agents
            memories = self.get_memories()
            compatibility = ""
            mismatches = ""

            if self.name == "Alice2":
                for memory in memories:
                    if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == "Alice":
                        compatibility = memory.content
                    elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier" and memory.sent_from == "Alice":
                        mismatches = memory.content
            elif self.name == "Bob2":
                for memory in memories:
                    if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == "Bob":
                        compatibility = memory.content
                    elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier" and memory.sent_from == "Bob":
                        mismatches = memory.content

            result = await todo.run(self.data_product, compatibility, mismatches)
            msg = Message(
                content=result,
                role=self.profile,
                cause_by="actions.read_product.ContextAwareProductReader",
                sent_from=self.name,
                send_to=[self.opponent_name, "Connor"]
            )
        
        elif isinstance(todo, DiscourseAwareComposer):
            memories = self.get_memories()
            own_desc = ""
            opponent_desc = ""
            compatibilityA = ""
            mismatchesA = ""
            compatibilityB = ""
            mismatchesB = ""

            # Extract relevant information from memory
            for memory in memories:
                if memory.cause_by == "actions.read_product.ContextAwareProductReader":
                    if memory.sent_from == self.name:
                        own_desc = memory.content
                    elif memory.sent_from == self.opponent_name:
                        opponent_desc = memory.content
                elif memory.cause_by == "actions.assess_compatibility.DiscourseAwareComposer":
                    if memory.sent_from == self.name:
                        compatibilityA = memory.content
                    elif memory.sent_from == self.opponent_name:
                        compatibilityB = memory.content
                elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    if memory.sent_from == self.name:
                        mismatchesA = memory.content
                    elif memory.sent_from == self.opponent_name:
                        mismatchesB = memory.content

            # Check if all required inputs are available
            if all([own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB]):
                result = await todo.run(own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.assess_compatibility.DiscourseAwareComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name]
                )
            else:
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
                    cause_by="actions.assess_compatibility.DiscourseAwareComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name]
                )

                
        elif isinstance(todo, MismatchIdentifier):
            # Get compatibility assessment
            memories = self.get_memories()
            assessment = ""
            
            for memory in memories:
                if memory.cause_by == "actions.assess_compatibility.DiscourseAwareComposer" and memory.sent_from == self.name:
                    assessment = memory.content
                    break
            
            if assessment:
                result = await todo.run(assessment)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, "Connor"]
                )
            else:
                msg = Message(
                    content="Waiting for compatibility assessment...",
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name, "Connor"]
                )
        
        else:
            msg = Message(
                content="I don't know how to handle this action.", 
                role=self.profile, 
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.opponent_name, "Connor"]
            )
        
        self.rc.memory.add(msg)
        return msg