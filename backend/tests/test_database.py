
def test_database_connection(test_engine):
    from sqlalchemy import text

    with test_engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


def test_required_tables_exist(test_engine):
    from sqlalchemy import inspect

    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "users",
        "suppliers",
        "documents",
        "invoices",
        "invoice_line_items",
        "processing_jobs",
        "validation_results",
        "audit_logs",
    }

    assert expected_tables.issubset(set(tables))
