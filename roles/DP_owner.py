from metagpt.roles.role import Role, RoleReactMode
from actions.read_product import SimpleDataProductReader
from actions.assess_compatibility import SimpleDataProductComposer
from actions.analyze_mismatch import MismatchIdentifier
from metagpt.schema import Message
from metagpt.logs import logger
import json


class DPOwner(Role):
    name: str = "Alice"
    profile: str = "Data Product Analyst"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleDataProductReader, SimpleDataProductComposer, MismatchIdentifier])
        self._set_react_mode(react_mode=RoleReactMode.PLAN_AND_ACT.value)
        self.product1_description = None
        self.product2_description = None
        self.compatibility_assessment = None

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # Get the most recent message
        msg = self.get_memories(k=1)[0]
        
        # Process based on the current action
        if todo.name == "SimpleDataProductReader" and not self.product1_description:
            # Read the first data product
            input_data = json.loads(msg.content.replace("'", "\"")) if isinstance(msg.content, str) else msg.content
            result = await todo.run(input_data["data_product_1"])
            self.product1_description = result
            
            # Create response message
            response = f"Data Product 1 Description: {result}"
            
            # Schedule the same action to read the second product next
            self.rc.todo = self.actions[0]()
            
        elif todo.name == "SimpleDataProductReader" and self.product1_description and not self.product2_description:
            # Read the second data product
            input_data = json.loads(msg.content.replace("'", "\"")) if isinstance(msg.content, str) else msg.content
            result = await todo.run(input_data["data_product_2"])
            self.product2_description = result
            
            # Create response message
            response = f"Data Product 2 Description: {result}"
            
            # Move to the compatibility assessment action
            self.rc.todo = self.actions[1]()
            
        elif todo.name == "CompatibilityAssessment" and self.product1_description and self.product2_description:
            # Assess compatibility between the two products
            result = await todo.run(self.product1_description, self.product2_description)
            self.compatibility_assessment = result
            
            # Create response message
            response = f"Compatibility Assessment: {result}"
            
            # Move to the mismatch identification action
            self.rc.todo = self.actions[2]()
            
        elif todo.name == "MismatchIdentifier" and self.compatibility_assessment:
            # Analyze mismatches
            result = await todo.run(self.compatibility_assessment)
            
            # Create final response message
            response = f"Mismatch Analysis: {result}"
            
        else:
            response = "Error in processing sequence."

        # Create and store the message
        out_msg = Message(content=response, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(out_msg)
        return out_msg
        
    async def run(self, message):
        # Initialize the first action
        self.rc.todo = self.actions[0]()
        
        # Create and add the initial message to memory
        if isinstance(message, str):
            try:
                message = json.loads(message.replace("'", "\""))
            except:
                pass
                
        msg = Message(content=message)
        self.rc.memory.add(msg)
        
        # Process each action in sequence
        results = []
        for _ in range(4):  # We need 4 actions: read product 1, read product 2, assess compatibility, identify mismatches
            result = await self._act()
            results.append(result.content)
            
        return "\n\n".join(results)