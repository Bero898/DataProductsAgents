from metagpt.roles.role import Role
from actions.context_read import ContextAwareProductReader
from actions.context_compatibility import ContextAwareProductComposer
from actions.analyze_mismatch import MismatchIdentifier
from metagpt.schema import Message
from metagpt.logs import logger


class ContextDPOwner(Role):
    name: str = "Alice"
    profile: str = "Data Product Owner"
    data_product: str = ""
    requester: bool = True
    opponent_name: str = ""
    predecessor: str = ""
    opponent_predecessor: str = ""

    def __init__(self, name: str = "Alice", predecessor: str = "Alice", opponent_predecessor: str = "Bob", data_product: str = "", opponent_name: str = "", requester: bool = True, **kwargs):
        super().__init__(name=name, **kwargs)
        self.name = name
        self.data_product = data_product
        self.opponent_name = opponent_name
        self.predecessor = predecessor
        self.opponent_predecessor = opponent_predecessor
        self.requester = requester #requester goes first, requested (i.e. when False) goes second
        self.set_actions([ContextAwareProductReader, ContextAwareProductComposer, MismatchIdentifier])
        self._watch([ContextAwareProductReader, ContextAwareProductComposer, MismatchIdentifier])
    
    async def _observe(self) -> int:
        await super()._observe()
        # Process messages sent directly to this agent or broadcast messages
        # Process messages sent directly to this agent or broadcast messages
        self.rc.news = [
            msg for msg in self.rc.news
            if self.name in msg.send_to
        ]
        return len(self.rc.news)
        # self.rc.news = [
        #     msg for msg in self.rc.news
        #     if self.name in msg.send_to or
        #     (self.name == "Alice2" and msg.sent_from == "Alice") or
        #     (self.name == "Bob2" and msg.sent_from == "Bob")
        # ]
        # return len(self.rc.news)
    
    async def react(self) -> Message:
        # Override the default react method to handle specific actions without planning

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
            elif latest_msg.cause_by == "actions.read_product.ContextAwareProductReader" or latest_msg.cause_by == "actions.perform_broker_analysis.PerformBrokerAnalysis":
                # After reading the context, assess compatibility
                self.rc.todo = ContextAwareProductComposer()
            elif latest_msg.cause_by == "actions.assess_compatibility.ContextAwareProductComposer":
                if self.requester:
                    # if the action before me was ContextAwareProductComposer and I'm the requester
                    # I should perform the MismatchIdentifier action
                    # After compatibility assessment, identify mismatches
                    self.rc.todo = MismatchIdentifier()
                else:
                    # if the action before me was ContextAwareProductComposer and I'm the requester
                    # I should perform the ContextAwareProductComposer action
                    self.rc.todo = ContextAwareProductComposer()
            elif latest_msg.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                if self.requester:
                    logger.debug(f"{self.name}: Waiting for required actions to complete.")
                    return None
                else:
                    # if the action before me was MismatchIdentifier and I'm the requested
                    # I should perform the MismatchIdentifier action
                    # After mismatch identification, read the data product again
                    self.rc.todo = MismatchIdentifier()

            else:
                # Default to reading the context
                self.rc.todo = ContextAwareProductReader()

        # if not self.rc.news:
        #     # If there's no news, use SimpleDataProductReader as default first action
        #     logger.error(f"{self.name} has no news, failed to collect context")
        # else:
        #     # Process the latest message
        #     latest_msg = self.rc.news[-1]
            
        #     # Check what action to take based on conversation state
        #     if latest_msg.cause_by == "actions.read_product.MismatchIdentifier":
        #         # Initial instruction - read data product
        #         self.rc.todo = ContextAwareProductReader()

        #     elif latest_msg.cause_by == "actions.read_product.ContextAwareProductReader":
        #         # After a data product is read, assess compatibility
        #         self.rc.todo = ContextAwareProductComposer()
            
        #     elif latest_msg.cause_by == "actions.assess_compatibility.ContextAwareProductComposer":
        #         # After compatibility assessment, identify mismatches
        #         self.rc.todo = MismatchIdentifier()
            
        #     else:
        #         # Default to reading the data product
        #         self.rc.todo = ContextAwareProductReader()
        
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

            # if self.name == "Alice2":
            #     for memory in memories:
            #         if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == "Alice":
            #             compatibility = memory.content
            #         elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier" and memory.sent_from == "Alice":
            #             mismatches = memory.content
            # elif self.name == "Bob2":
            #     for memory in memories:
            #         if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == "Bob":
            #             compatibility = memory.content
            #         elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier" and memory.sent_from == "Bob":
            #             mismatches = memory.content

            for memory in memories:
                if memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer" and memory.sent_from == self.predecessor:
                    compatibility = memory.content
                elif memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer" and memory.sent_from == self.name:
                    compatibility = memory.content
                elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier" and memory.sent_from == self.predecessor:
                    mismatches = memory.content
                if compatibility != "" and mismatches != "":
                    break


            result = await todo.run(self.data_product, compatibility, mismatches)
            msg = Message(
                content=result,
                role=self.profile,
                cause_by="actions.read_product.ContextAwareProductReader",
                sent_from=self.name,
                send_to=[self.opponent_name]
            )
        
        elif isinstance(todo, ContextAwareProductComposer):
            memories = self.get_memories()
            own_desc = ""
            opponent_desc = ""
            compatibilityA = ""
            mismatchesA = ""
            compatibilityB = ""
            mismatchesB = ""

            # # Extract relevant information from memory
            # for memory in memories:
            #     if memory.cause_by == "actions.read_product.ContextAwareProductReader":
            #         if memory.sent_from == self.name:
            #             own_desc = memory.content
            #         elif memory.sent_from == self.opponent_name:
            #             opponent_desc = memory.content
            #     elif memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer":
            #         if memory.sent_from == self.name:
            #             compatibilityA = memory.content
            #         elif memory.sent_from == self.opponent_name:
            #             compatibilityB = memory.content
            #     elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
            #         if memory.sent_from == self.name:
            #             mismatchesA = memory.content
            #         elif memory.sent_from == self.opponent_name:
            #             mismatchesB = memory.content

            # # Check if all required inputs are available
            # if all([own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB]):
            for memory in memories:
                if memory.cause_by == "actions.read_product.ContextAwareProductReader":
                    if memory.sent_from == self.name:
                        own_desc = memory.content
                    elif memory.sent_from == self.opponent_name:
                        opponent_desc = memory.content
                elif memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer" or memory.cause_by == "actions.assess_compatibility.SimpleDataProductComposer":
                    logger.debug(f"{self.name} - {memory.cause_by} - {memory.sent_from} - {memory.content}")
                    if memory.sent_from == self.name or memory.sent_from == self.predecessor:
                        compatibilityA = memory.content
                    elif memory.sent_from == self.opponent_name or memory.sent_from == self.opponent_predecessor:
                        compatibilityB = memory.content
                elif memory.cause_by == "actions.analyze_mismatch.MismatchIdentifier":
                    if memory.sent_from == self.name or memory.sent_from == self.predecessor:
                        mismatchesA = memory.content
                    elif memory.sent_from == self.opponent_name or memory.sent_from == self.opponent_predecessor:
                        mismatchesB = memory.content
                if own_desc != "" and opponent_desc != "" and compatibilityA != "" and mismatchesA != "" and compatibilityB != "" and mismatchesB != "":
                    break

            # Check if all required inputs are available
            if all([own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB]):
                result = await todo.run(own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB)

                result = await todo.run(own_desc, opponent_desc, compatibilityA, mismatchesA, compatibilityB, mismatchesB)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.assess_compatibility.ContextAwareProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name, self.name]
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
                    cause_by="actions.assess_compatibility.ContextAwareProductComposer",
                    sent_from=self.name,
                    send_to=[self.opponent_name]
                )

                
        elif isinstance(todo, MismatchIdentifier):
            # Get compatibility assessment
            memories = self.get_memories()
            assessmentA = ""
            assessmentB = ""
            
            
            for memory in memories:
                if memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer" and memory.sent_from == self.name:
                    assessmentA = memory.content
                elif memory.cause_by == "actions.assess_compatibility.ContextAwareProductComposer" and memory.sent_from == self.opponent_name:
                    assessmentB = memory.content
                if assessmentA != "" and assessmentB !="":
                    break
            
            if assessmentA and assessmentB:
                result = await todo.run(assessmentA = assessmentA, assessmentB = assessmentB)
                msg = Message(
                    content=result,
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name]
                )
            else:
                msg = Message(
                    content="Waiting for compatibility assessment...",
                    role=self.profile,
                    cause_by="actions.analyze_mismatch.MismatchIdentifier",
                    sent_from=self.name,
                    send_to=[self.opponent_name]
                )
        
        else:
            msg = Message(
                content="I don't know how to handle this action.", 
                role=self.profile, 
                cause_by=str(type(todo)),
                sent_from=self.name,
                send_to=[self.opponent_name]
            )
        
        self.rc.memory.add(msg)
        return msg