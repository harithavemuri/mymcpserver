"""
Conversation example demonstrating text transformations using the MCP host.
This script shows how to maintain a conversation context and apply transformations.
"""
import asyncio
import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add the host directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_transform import MCPTextTransformClient

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class Message:
    role: MessageRole
    content: str
    transformed_text: Optional[str] = None
    transformations: Optional[List[str]] = None

class Conversation:
    """A class to manage conversation state and transformations."""
    
    def __init__(self):
        self.client = MCPTextTransformClient(base_url="http://localhost:8002")
        self.messages: List[Message] = []
        
    async def add_message(self, role: MessageRole, content: str) -> Message:
        """Add a message to the conversation."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        return message
    
    async def transform_text(self, text: str, operations: List[str]) -> str:
        """Apply a series of transformations to the text."""
        current_text = text
        applied_transforms = []
        
        for operation in operations:
            try:
                result = await self.client.transform(current_text, operation=operation)
                current_text = result.transformed
                applied_transforms.append(operation)
            except Exception as e:
                print(f"Error applying {operation}: {e}")
        
        return current_text, applied_transforms
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input and generate a response with transformations."""
        # Add user message to conversation
        user_message = await self.add_message(MessageRole.USER, user_input)
        
        # Check for transformation commands
        if "to uppercase" in user_input.lower():
            transformed_text, transforms = await self.transform_text(
                user_input, ["uppercase"]
            )
            user_message.transformed_text = transformed_text
            user_message.transformations = transforms
            
            # Add assistant response
            response = f"I've transformed your text to uppercase: {transformed_text}"
            await self.add_message(MessageRole.ASSISTANT, response)
            return response
            
        elif "reverse" in user_input.lower():
            transformed_text, transforms = await self.transform_text(
                user_input, ["reverse"]
            )
            user_message.transformed_text = transformed_text
            user_message.transformations = transforms
            
            response = f"Here's your reversed text: {transformed_text}"
            await self.add_message(MessageRole.ASSISTANT, response)
            return response
            
        elif "title case" in user_input.lower() or "capitalize" in user_input.lower():
            transformed_text, transforms = await self.transform_text(
                user_input, ["title"]
            )
            user_message.transformed_text = transformed_text
            user_message.transformations = transforms
            
            response = f"Title case version: {transformed_text}"
            await self.add_message(MessageRole.ASSISTANT, response)
            return response
            
        elif "chain" in user_input.lower() or "multiple" in user_input.lower():
            # Example of chaining multiple transformations
            operations = []
            if "uppercase" in user_input.lower():
                operations.append("uppercase")
            if "reverse" in user_input.lower():
                operations.append("reverse")
            if "title" in user_input.lower():
                operations.append("title")
                
            if not operations:
                operations = ["uppercase", "reverse"]  # Default chain
                
            transformed_text, transforms = await self.transform_text(
                user_input, operations
            )
            user_message.transformed_text = transformed_text
            user_message.transformations = transforms
            
            response = (
                f"Applied transformations: {', '.join(transforms)}. "
                f"Result: {transformed_text}"
            )
            await self.add_message(MessageRole.ASSISTANT, response)
            return response
            
        else:
            # Default response
            response = (
                "I can help you transform text! Try asking me to:"
                "\n- Convert text to UPPERCASE"
                "\n- Reverse text"
                "\n- Convert to Title Case"
                "\n- Chain multiple transformations (e.g., 'make it uppercase and then reverse it')"
            )
            await self.add_message(MessageRole.ASSISTANT, response)
            return response
    
    def get_conversation_history(self) -> str:
        """Get the conversation history as a formatted string."""
        history = []
        for i, message in enumerate(self.messages, 1):
            role = message.role.value.upper()
            content = message.content
            
            history.append(f"{i}. {role}: {content}")
            
            if message.transformed_text:
                transforms = ", ".join(message.transformations) if message.transformations else "unknown"
                history.append(f"   → Transformed ({transforms}): {message.transformed_text}")
                
        return "\n".join(history)

async def main():
    """Run the conversation example."""
    conversation = Conversation()
    
    # Initial greeting
    print("\n" + "="*50)
    print("Welcome to the Text Transformation Assistant!")
    print("Type 'exit' to end the conversation.")
    print("="*50 + "\n")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ('exit', 'quit', 'bye'):
                print("\nConversation ended. Here's the full history:")
                print("-" * 50)
                print(conversation.get_conversation_history())
                print("-" * 50)
                break
                
            # Process the input
            response = await conversation.process_user_input(user_input)
            print(f"\nAssistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    # Close the client
    await conversation.client.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
