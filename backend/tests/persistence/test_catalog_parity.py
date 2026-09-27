"""Exact reference-SQL versus migration catalogs; never compare PostgreSQL OIDs."""

import os
from collections import Counter

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.models import Base

CATALOG_QUERIES = {
    "schemas": "SELECT nspname FROM pg_namespace WHERE nspname='dogfood'",
    "tables": "SELECT tablename FROM pg_tables WHERE schemaname='dogfood' ORDER BY tablename",
    "columns": """SELECT c.relname, a.attname, a.attnum,
        format_type(a.atttypid,a.atttypmod), a.attnotnull, a.attidentity,
        a.attgenerated, pg_get_expr(d.adbin,d.adrelid), col.collname
        FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
        LEFT JOIN pg_collation col ON col.oid=a.attcollation
        WHERE n.nspname='dogfood' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped
        ORDER BY c.relname,a.attnum""",
    "constraints": """SELECT c.relname, x.conname, x.contype,
        x.condeferrable, x.condeferred, x.convalidated, x.confupdtype,
        x.confdeltype, x.confmatchtype, pg_get_constraintdef(x.oid)
        FROM pg_constraint x JOIN pg_class c ON c.oid=x.conrelid
        WHERE x.connamespace='dogfood'::regnamespace
        ORDER BY c.relname,x.conname""",
    "indexes": """SELECT c.relname, i.relname, x.indisunique, x.indisprimary,
        x.indisvalid, pg_get_indexdef(i.oid), pg_get_expr(x.indpred,x.indrelid)
        FROM pg_index x JOIN pg_class c ON c.oid=x.indrelid
        JOIN pg_class i ON i.oid=x.indexrelid
        WHERE c.relnamespace='dogfood'::regnamespace ORDER BY c.relname,i.relname""",
    "functions": """SELECT proname, pg_get_functiondef(oid)
        FROM pg_proc WHERE pronamespace='dogfood'::regnamespace ORDER BY proname""",
    "triggers": """SELECT c.relname, t.tgname, t.tgenabled, pg_get_triggerdef(t.oid)
        FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        WHERE c.relnamespace='dogfood'::regnamespace AND NOT t.tgisinternal
        ORDER BY c.relname,t.tgname""",
    "enums": """SELECT t.typname,e.enumlabel,e.enumsortorder FROM pg_type t
        LEFT JOIN pg_enum e ON e.enumtypid=t.oid WHERE t.typnamespace='dogfood'::regnamespace AND t.typtype='e'
        ORDER BY t.typname,e.enumsortorder""",
}


def catalog(connection):
    return {
        name: connection.execute(text(query)).all()
        for name, query in CATALOG_QUERIES.items()
    }


@pytest.fixture(scope="module")
def catalogs(persistence_engine):
    reference = os.environ.get("T2_REFERENCE_DATABASE_URL")
    if not reference:
        pytest.skip("Set T2_REFERENCE_DATABASE_URL to a database built from frozen SQL")
    engine = create_engine(reference)
    try:
        with engine.connect() as ref, persistence_engine.connect() as migrated:
            ref.exec_driver_sql("SET TRANSACTION READ ONLY")
            migrated.exec_driver_sql("SET TRANSACTION READ ONLY")
            assert (
                int(ref.exec_driver_sql("SHOW server_version_num").scalar_one())
                >= 160000
            )
            yield catalog(ref), catalog(migrated)
    finally:
        engine.dispose()


@pytest.mark.parametrize("kind", list(CATALOG_QUERIES))
def test_reference_migration_catalog_parity(catalogs, kind):
    reference, migrated = catalogs
    assert reference[kind] == migrated[kind], f"Frozen schema mismatch in {kind}"


def test_frozen_structural_counts(catalogs):
    for database in catalogs:
        assert {
            key: len(database[key])
            for key in (
                "schemas",
                "tables",
                "columns",
                "indexes",
                "functions",
                "triggers",
                "enums",
            )
        } == {
            "schemas": 1,
            "tables": 33,
            "columns": 311,
            "indexes": 81,
            "functions": 11,
            "triggers": 49,
            "enums": 0,
        }
        assert Counter(row[2] for row in database["constraints"]) == {
            "p": 33,
            "u": 27,
            "c": 97,
            "f": 92,
        }


def test_model_metadata_catalog_parity(catalogs):
    """Verify CHECKs and index predicates that autogenerate may not compare."""
    url = os.environ.get("T2_METADATA_DATABASE_URL")
    if not url:
        pytest.skip(
            "Set T2_METADATA_DATABASE_URL to an empty disposable dogfood_t2_* database"
        )
    parsed = make_url(url)
    assert parsed.drivername == "postgresql+psycopg"
    assert (parsed.database or "").startswith("dogfood_t2_")
    engine = create_engine(url)
    try:
        # PostgreSQL DDL is transactional; leave the dedicated database empty.
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                assert (
                    int(
                        connection.exec_driver_sql(
                            "SHOW server_version_num"
                        ).scalar_one()
                    )
                    >= 160000
                )
                assert not connection.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema'))"
                    )
                ).scalar_one(), "Metadata verification requires an empty database"
                connection.exec_driver_sql("CREATE SCHEMA dogfood")
                Base.metadata.create_all(connection)
                actual = catalog(connection)
                reference, _ = catalogs
                for kind in (
                    "schemas",
                    "tables",
                    "columns",
                    "constraints",
                    "indexes",
                    "enums",
                ):
                    assert (
                        actual[kind] == reference[kind]
                    ), f"Model metadata mismatch: {kind}"
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
