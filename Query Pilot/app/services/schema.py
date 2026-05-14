from psycopg import AsyncConnection

class SchemaService:
    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    async def get_schema_context(self) -> str:
        """
        Retrieves the public schema of the database to provide context to the LLM.
        Formats it as a DDL-like string or a list of tables and columns.
        """
        query = """
            SELECT 
                table_name, 
                column_name, 
                data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position;
        """
        
        async with self.conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()
            
        schema_dict = {}
        for row in rows:
            t_name = row['table_name']
            c_name = row['column_name']
            d_type = row['data_type']
            if t_name not in schema_dict:
                schema_dict[t_name] = []
            schema_dict[t_name].append(f"{c_name} ({d_type})")
            
        context_lines = []
        for table, cols in schema_dict.items():
            context_lines.append(f"Table {table}: " + ", ".join(cols))
            
        return "\n".join(context_lines)
