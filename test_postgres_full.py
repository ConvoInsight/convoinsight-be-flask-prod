#!/usr/bin/env python3
"""
Complete PostgreSQL setup test
Tests connection, operations, and Polars integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_connection():
    """Test basic SQLAlchemy connection"""
    print("\n[1/4] Testing Basic Connection...")
    try:
        from sqlalchemy import create_engine, text
        from config.settings import get_postgres_url

        pg_url = get_postgres_url()
        if not pg_url:
            print("✗ No PostgreSQL URL configured")
            print("  Set LOCAL_POSTGRES_URL or POSTGRES_URL in .env file")
            return False

        print(f"  Connecting to: {pg_url.split('@')[1] if '@' in pg_url else pg_url}")
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            assert result.scalar() == 1

            # Get version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            version_short = version.split(',')[0] if version else "Unknown"

        print(f"✓ Basic connection works")
        print(f"  {version_short}")
        return True
    except Exception as e:
        print(f"✗ Basic connection failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Check if PostgreSQL is running: docker compose ps")
        print("  2. Verify connection URL in .env file")
        print("  3. Test connection: psql -U convoinsight -d convoinsight")
        return False

def test_sample_data():
    """Test reading sample data"""
    print("\n[2/4] Testing Sample Data...")
    try:
        from sqlalchemy import create_engine, text
        from config.settings import get_postgres_url

        pg_url = get_postgres_url()
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'sample_data'
                )
            """))
            table_exists = result.scalar()

            if not table_exists:
                print("⚠ Table 'sample_data' does not exist")
                print("  Run: psql -U convoinsight -d convoinsight -f scripts/init_db.sql")
                return False

            # Count rows
            result = conn.execute(text("SELECT COUNT(*) FROM sample_data"))
            count = result.scalar()

            if count >= 3:
                print(f"✓ Sample data exists ({count} rows)")

                # Show sample
                result = conn.execute(text("SELECT * FROM sample_data LIMIT 3"))
                rows = result.fetchall()
                print("\n  Sample rows:")
                for row in rows:
                    print(f"    {dict(row._mapping)}")

                return True
            else:
                print(f"⚠ Sample data incomplete ({count} rows, expected >= 3)")
                print("  Run: psql -U convoinsight -d convoinsight -f scripts/init_db.sql")
                return False
    except Exception as e:
        print(f"✗ Sample data test failed: {e}")
        return False

def test_polars_integration():
    """Test Polars DataFrame integration"""
    print("\n[3/4] Testing Polars Integration...")
    try:
        import polars as pl
        from sqlalchemy import create_engine
        from config.settings import get_postgres_url

        pg_url = get_postgres_url()
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            # Read with Polars
            try:
                df = pl.read_database("SELECT * FROM sample_data", conn)
                method = "Polars native"
            except Exception as e:
                # Fallback to pandas
                import pandas as pd
                pdf = pd.read_sql("SELECT * FROM sample_data", conn)
                df = pl.from_pandas(pdf)
                method = "Pandas fallback"

            print(f"✓ Polars DataFrame created ({method})")
            print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"  Columns: {', '.join(df.columns)}")
            print(f"\n  First row:")
            print(f"    {df.row(0, named=True)}")

        return True
    except Exception as e:
        print(f"✗ Polars integration failed: {e}")
        return False

def test_write_operation():
    """Test write operation"""
    print("\n[4/4] Testing Write Operation...")
    try:
        from sqlalchemy import create_engine, text
        from config.settings import get_postgres_url
        import time

        pg_url = get_postgres_url()
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            # Create test table
            conn.execute(text("""
                DROP TABLE IF EXISTS test_temp
            """))
            conn.execute(text("""
                CREATE TABLE test_temp (
                    id SERIAL PRIMARY KEY,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

            # Insert data
            test_message = f"Test from Python at {time.time()}"
            conn.execute(text("""
                INSERT INTO test_temp (message) VALUES (:msg)
            """), {"msg": test_message})
            conn.commit()

            # Read back
            result = conn.execute(text("SELECT message FROM test_temp LIMIT 1"))
            message = result.scalar()

            # Cleanup
            conn.execute(text("DROP TABLE test_temp"))
            conn.commit()

            if message == test_message:
                print("✓ Write operation successful")
                print(f"  Created table, inserted data, and cleaned up")
                return True
            else:
                print("✗ Write operation failed: data mismatch")
                return False

    except Exception as e:
        print(f"✗ Write operation failed: {e}")
        # Try to cleanup if table exists
        try:
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS test_temp"))
                conn.commit()
        except:
            pass
        return False

def main():
    print("="*60)
    print("PostgreSQL Setup Verification")
    print("="*60)

    tests = [
        ("Basic Connection", test_basic_connection),
        ("Sample Data", test_sample_data),
        ("Polars Integration", test_polars_integration),
        ("Write Operation", test_write_operation),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! PostgreSQL is ready to use.")
        print("\nNext steps:")
        print("  1. Run: python tests/test_middleware_basic.py")
        print("  2. Continue to Phase 2: Prompt Externalization")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("\nTroubleshooting:")
        print("  1. Check POSTGRES_SETUP_GUIDE.md for detailed setup")
        print("  2. Verify PostgreSQL is running: docker compose ps")
        print("  3. Check .env file configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
