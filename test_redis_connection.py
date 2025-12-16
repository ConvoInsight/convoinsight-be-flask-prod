#!/usr/bin/env python3
"""
Quick Redis connection test
Simple script to verify Redis connectivity and basic operations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_connection():
    print("Testing Redis connection...")
    print("-" * 60)

    try:
        import redis
        from config.settings import REDIS_URL

        if not REDIS_URL:
            print("✗ No Redis URL configured")
            print("\nPlease set REDIS_URL in your .env file:")
            print("  REDIS_URL=redis://localhost:6379/0")
            return False

        # Mask password in output
        display_url = REDIS_URL
        if '@' in display_url and ':' in display_url.split('@')[0]:
            parts = display_url.split('@')
            user_pass = parts[0].split('://')[-1]
            user = user_pass.split(':')[0] if ':' in user_pass else user_pass
            display_url = display_url.replace(user_pass, f"{user}:***")

        print(f"Connecting to: {display_url}")
        print()

        # Create Redis client
        r = redis.from_url(REDIS_URL, decode_responses=True)

        # Test PING
        if r.ping():
            print("✓ Connection successful!")
        else:
            print("✗ PING failed")
            return False

        # Get Redis info
        info = r.info()

        print()
        print(f"Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"Mode: {info.get('redis_mode', 'Unknown')}")
        print(f"OS: {info.get('os', 'Unknown')}")
        print(f"Uptime: {info.get('uptime_in_seconds', 0)} seconds")
        print()

        # Memory info
        memory_used = info.get('used_memory_human', 'Unknown')
        memory_peak = info.get('used_memory_peak_human', 'Unknown')
        print(f"Memory Used: {memory_used}")
        print(f"Memory Peak: {memory_peak}")
        print()

        # Connected clients
        clients = info.get('connected_clients', 0)
        print(f"Connected Clients: {clients}")
        print()

        # Database info
        db_info = r.info('keyspace')
        if db_info:
            print("Database Info:")
            for db, stats in db_info.items():
                if db.startswith('db'):
                    print(f"  {db}: {stats}")
        else:
            print("Database: Empty (no keys)")

        print()

        # Test basic operations
        print("Testing basic operations...")
        test_key = "test:connection:check"
        test_value = "Hello from Redis test!"

        # SET
        r.set(test_key, test_value, ex=10)  # Expires in 10 seconds
        print(f"  SET {test_key} = \"{test_value}\" (TTL: 10s)")

        # GET
        retrieved = r.get(test_key)
        if retrieved == test_value:
            print(f"  GET {test_key} = \"{retrieved}\" ✓")
        else:
            print(f"  GET failed: expected '{test_value}', got '{retrieved}' ✗")
            return False

        # TTL
        ttl = r.ttl(test_key)
        print(f"  TTL {test_key} = {ttl} seconds")

        # DELETE
        r.delete(test_key)
        print(f"  DEL {test_key} ✓")

        print()
        print("-" * 60)
        print("✓ Redis is ready to use!")
        print()
        print("Features enabled:")
        print("  - Caching: Fast dataset & query result storage")
        print("  - Rate Limiting: Per-user request throttling")
        print("  - Session Storage: Fast session state management")
        print()
        print("Next: Test middleware integration")
        print("  python tests/test_middleware_basic.py")

        return True

    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install -r requirements.txt")
        return False

    except redis.ConnectionError as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if Redis is running:")
        print("     - Docker: docker compose ps")
        print("     - Native: redis-cli ping")
        print()
        print("  2. Verify connection URL in .env file:")
        print("     REDIS_URL=redis://localhost:6379/0")
        print()
        print("  3. Start Redis:")
        print("     - Docker: docker compose up -d")
        print("     - Native: brew services start redis (macOS)")
        print("               sudo systemctl start redis-server (Linux)")
        print()
        print("  4. See REDIS_SETUP_GUIDE.md for detailed setup instructions")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print("\nCheck REDIS_SETUP_GUIDE.md for troubleshooting")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
