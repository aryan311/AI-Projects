from psycopg import AsyncConnection
from app.core.llm import LLMClient
from app.services.schema import SchemaService
from app.services.generator import SqlGenerator
from app.services.validator import SqlValidator
from app.services.executor import QueryExecutor
from app.services.summarizer import Summarizer
from app.api.models import QueryRequest, QueryResponse

class QueryPipelineService:
    def __init__(self, conn: AsyncConnection, llm_client: LLMClient):
        self.conn = conn
        self.llm_client = llm_client
        
    async def process_question(self, request: QueryRequest) -> QueryResponse:
        # 1. Get Schema Context
        schema_service = SchemaService(self.conn)
        schema_context = await schema_service.get_schema_context()
        
        # 2. Generate SQL
        generator = SqlGenerator(self.llm_client)
        raw_sql = await generator.generate(schema_context, request.question)
        
        # 3. Validate SQL
        validator = SqlValidator()
        safe_sql = validator.validate_and_format(raw_sql)
        
        # 4. Execute Query
        executor = QueryExecutor(self.conn)
        rows = await executor.execute(safe_sql)
        
        # 5. Summarize Results
        summarizer = Summarizer(self.llm_client)
        summary = await summarizer.summarize(request.question, safe_sql, rows)
        warnings = summarizer.generate_warnings(rows)
        
        return QueryResponse(
            sql=safe_sql,
            rows=rows,
            summary=summary,
            warnings=warnings
        )
