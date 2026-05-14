from app.core.llm import LLMClient
from app.services.schema import SchemaService

class SqlGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def generate(self, schema_context: str, question: str) -> str:
        sql = await self.llm_client.generate_sql(schema_context, question)
        return sql
