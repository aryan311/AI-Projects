import sqlglot
import sqlglot.expressions as exp
from app.core.config import settings

class SqlValidator:
    def __init__(self, max_row_limit: int = settings.max_row_limit):
        self.max_row_limit = max_row_limit

    def validate_and_format(self, sql: str) -> str:
        """
        Validates the SQL to ensure it's a single read-only SELECT statement.
        Enforces a LIMIT.
        Returns the safe, formatted SQL string.
        Raises ValueError if unsafe.
        """
        # Parse the SQL. This automatically fails on many invalid syntaxes.
        # It also returns a list of expressions if there are multiple statements separated by `;`.
        try:
            parsed = sqlglot.parse(sql, read="postgres")
        except sqlglot.errors.ParseError as e:
            raise ValueError(f"SQL parsing failed: {e}")

        if not parsed:
            raise ValueError("No SQL statement found.")

        # Block multi-statement queries
        if len(parsed) > 1:
            raise ValueError("Multiple SQL statements are not allowed.")

        ast = parsed[0]
        
        if not ast:
            raise ValueError("Empty SQL statement.")

        # Ensure it's a SELECT statement
        if not isinstance(ast, exp.Select):
            raise ValueError("Only SELECT statements are allowed.")

        # Further safety check: iterate over all nodes to ensure no mutating operations sneaked in
        # sqlglot usually handles this by the root type, but just in case of weird ASTs:
        for node in ast.walk():
            if isinstance(node[0], (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Command)):
                raise ValueError("Mutating operations are not allowed.")

        # Check and enforce LIMIT
        limit_expr = ast.args.get("limit")
        if limit_expr:
            # If there's a limit, ensure it doesn't exceed max_row_limit
            # Some limits are complex expressions, try to evaluate if it's a simple number
            try:
                limit_val = int(limit_expr.expression.name)
                if limit_val > self.max_row_limit:
                    ast.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))
            except (ValueError, AttributeError):
                # If we can't easily parse it as an int, overwrite it for safety
                ast.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))
        else:
            # No limit found, apply default limit
            ast.set("limit", exp.Limit(expression=exp.Literal.number(self.max_row_limit)))

        # Generate the safe SQL (without comments, standardized formatting)
        safe_sql = ast.sql(dialect="postgres")
        return safe_sql
