from pydantic import BaseModel
from typing import Callable, TypeVar, Generic, Type
import httpx
from core.models import BaseMessage
import asyncio

T_In = TypeVar('T_In', bound=BaseMessage)
T_Out = TypeVar('T_Out', bound=BaseMessage)

class AgentCard(BaseModel):
    name: str
    description: str
    url: str

class Executor(Generic[T_In, T_Out]):
    """
    Agent Executor wraps the core business logic of the agent.
    It handles deserializing the incoming A2A message, executing the logic,
    and returning the typed response.
    """
    def __init__(self, name: str, func: Callable[[T_In], T_Out], input_type: Type[T_In]):
        self.name = name
        self.func = func
        self.input_type = input_type

    def execute(self, payload: dict) -> dict:
        input_data = self.input_type.model_validate(payload)
        # Execute the agent logic
        result = self.func(input_data)
        # Return serialized dictionary
        return result.model_dump()

class Client:
    """
    Client is responsible for discovering an agent (via AgentCard) 
    and executing tasks by sending typed payloads.
    """
    @staticmethod
    async def execute_agent(card: AgentCard, payload: BaseMessage) -> dict:
        async with httpx.AsyncClient() as client:
            # We assume the agent exposes an /execute endpoint on its base url
            endpoint = f"{card.url.rstrip('/')}/execute"
            response = await client.post(
                endpoint,
                json=payload.model_dump(mode='json'),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
