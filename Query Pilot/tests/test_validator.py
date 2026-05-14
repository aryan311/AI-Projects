import pytest
from app.services.validator import SqlValidator

def test_safe_select_with_limit():
    validator = SqlValidator(max_row_limit=100)
    sql = "SELECT id, name FROM customers LIMIT 10;"
    safe_sql = validator.validate_and_format(sql)
    assert "LIMIT 10" in safe_sql
    assert "SELECT" in safe_sql.upper()

def test_select_without_limit_injects_limit():
    validator = SqlValidator(max_row_limit=50)
    sql = "SELECT * FROM orders"
    safe_sql = validator.validate_and_format(sql)
    assert "LIMIT 50" in safe_sql

def test_select_with_limit_exceeding_max():
    validator = SqlValidator(max_row_limit=100)
    sql = "SELECT * FROM orders LIMIT 1000"
    safe_sql = validator.validate_and_format(sql)
    assert "LIMIT 100" in safe_sql

def test_reject_insert():
    validator = SqlValidator()
    with pytest.raises(ValueError, match="Only SELECT statements are allowed"):
        validator.validate_and_format("INSERT INTO customers (name) VALUES ('Test')")

def test_reject_update():
    validator = SqlValidator()
    with pytest.raises(ValueError, match="Only SELECT statements are allowed"):
        validator.validate_and_format("UPDATE customers SET name = 'Test'")

def test_reject_delete():
    validator = SqlValidator()
    with pytest.raises(ValueError, match="Only SELECT statements are allowed"):
        validator.validate_and_format("DELETE FROM customers")

def test_reject_drop():
    validator = SqlValidator()
    with pytest.raises(ValueError, match="Only SELECT statements are allowed"):
        validator.validate_and_format("DROP TABLE customers")

def test_reject_multi_statement():
    validator = SqlValidator()
    with pytest.raises(ValueError, match="Multiple SQL statements are not allowed"):
        validator.validate_and_format("SELECT * FROM customers; DROP TABLE orders;")

def test_reject_comments_hiding_statements():
    validator = SqlValidator()
    # sqlglot strips comments or parses them correctly, so a multi statement hidden by trickery should still fail
    # or fail parsing.
    with pytest.raises(ValueError, match="Multiple SQL statements are not allowed"):
        validator.validate_and_format("SELECT * FROM customers; -- DROP TABLE orders;\n SELECT 1;")

def test_complex_select_is_allowed():
    validator = SqlValidator(max_row_limit=100)
    sql = """
    WITH top_customers AS (
        SELECT customer_id, SUM(total_amount) as spent 
        FROM orders 
        GROUP BY customer_id 
        ORDER BY spent DESC 
        LIMIT 5
    )
    SELECT c.name, tc.spent 
    FROM customers c 
    JOIN top_customers tc ON c.id = tc.customer_id
    """
    safe_sql = validator.validate_and_format(sql)
    assert "LIMIT 100" in safe_sql # The outer query gets the limit injected
    assert "LIMIT 5" in safe_sql # The inner CTE limit should be preserved
