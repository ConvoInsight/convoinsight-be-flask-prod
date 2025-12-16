#!/usr/bin/env python3
"""
Quick PostgreSQL connection test
Simple script to verify PostgreSQL connectivity
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_connection():
    print("Testing PostgreSQL connection...")
    print("-" * 60)

    try:
        from sqlalchemy import create_engine, text
        from config.settings import get_postgres_url

        # Get PostgreSQL URL from config
        pg_url = get_postgres_url()

        if not pg_url:
            print("✗ No PostgreSQL URL configured")
            print("\nPlease set one of these in your .env file:")
            print("  - LOCAL_POSTGRES_URL (for local development)")
            print("  - POSTGRES_URL (for production)")
            print("\nExample:")
            print("  LOCAL_POSTGRES_URL=postgresql://convoinsight:password@localhost:5432/convoinsight")
            return False

        # Mask password in output
        display_url = pg_url
        if '@' in display_url:
            parts = display_url.split('@')
            user_pass = parts[0].split('://')[-1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                display_url = display_url.replace(user_pass, f"{user}:***")

        print(f"Connecting to: {display_url}")
        print()

        # Create engine and test connection
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

            # Get version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()

            # Get current database
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()

            # Get current user
            result = conn.execute(text("SELECT current_user"))
            user = result.scalar()

            # Count tables
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()

        print("✓ Connection successful!")
        print()
        print(f"Database: {db_name}")
        print(f"User: {user}")
        print(f"Tables: {table_count} in 'public' schema")
        print()
        print("PostgreSQL Version:")
        print(f"  {version.split(',')[0]}")
        print()

        # Check for sample_data table
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'sample_data'
                )
            """))
            has_sample = result.scalar()

            if has_sample:
                result = conn.execute(text("SELECT COUNT(*) FROM sample_data"))
                count = result.scalar()
                print(f"✓ Sample data table exists ({count} rows)")
            else:
                print("⚠ Sample data table not found")
                print("  Run: psql -U convoinsight -d convoinsight -f scripts/init_db.sql")

        print()
        print("-" * 60)
        print("✓ PostgreSQL is ready to use!")
        print()
        print("Next: Run full test suite")
        print("  python test_postgres_full.py")

        return True

    except ModuleNotFoundError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if PostgreSQL is running:")
        print("     - Docker: docker compose ps")
        print("     - Native: Check PostgreSQL service status")
        print()
        print("  2. Verify connection URL in .env file")
        print()
        print("  3. Test with psql command:")
        print("     psql -U convoinsight -d convoinsight")
        print()
        print("  4. See POSTGRES_SETUP_GUIDE.md for detailed setup instructions")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
