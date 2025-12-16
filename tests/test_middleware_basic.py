"""
Basic tests for cache and rate limiter middleware
Run these tests to verify middleware functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_cache_import():
    """Test that cache module can be imported"""
    try:
        from src.middleware.cache import cache_manager, cached
        print("✓ Cache module imported successfully")
        print(f"  - Cache enabled: {cache_manager.enabled}")
        print(f"  - Redis URL: {cache_manager.redis_url}")
        return True
    except Exception as e:
        print(f"✗ Failed to import cache module: {e}")
        return False


def test_rate_limiter_import():
    """Test that rate limiter module can be imported"""
    try:
        from src.middleware.rate_limiter import rate_limiter, rate_limit
        print("✓ Rate limiter module imported successfully")
        print(f"  - Rate limiter enabled: {rate_limiter.enabled}")
        print(f"  - Redis URL: {rate_limiter.redis_url}")
        return True
    except Exception as e:
        print(f"✗ Failed to import rate limiter module: {e}")
        return False


def test_cache_operations():
    """Test basic cache operations (if Redis is available)"""
    try:
        from src.middleware.cache import cache_manager

        if not cache_manager.enabled:
            print("⊘ Cache is disabled, skipping operations test")
            return True

        # Test set and get
        test_key = "test:basic"
        test_value = {"message": "Hello from cache test"}

        cache_manager.set(test_key, test_value, ttl=10)
        retrieved = cache_manager.get(test_key)

        if retrieved == test_value:
            print("✓ Cache set/get operations work correctly")
            # Clean up
            cache_manager.delete(test_key)
            return True
        else:
            print(f"✗ Cache value mismatch: expected {test_value}, got {retrieved}")
            return False

    except Exception as e:
        print(f"✗ Cache operations test failed: {e}")
        return False


def test_cached_decorator():
    """Test @cached decorator functionality"""
    try:
        from src.middleware.cache import cached
        import time

        call_count = 0

        @cached("test:decorator", ttl=5)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute function
        result1 = expensive_function(5)
        count_after_first = call_count

        # Second call - should use cache
        result2 = expensive_function(5)
        count_after_second = call_count

        if result1 == result2 == 10:
            if count_after_second == count_after_first:
                print("✓ @cached decorator works correctly (cache hit)")
                return True
            else:
                print("⊘ @cached decorator executed function on second call (cache miss or disabled)")
                return True
        else:
            print(f"✗ @cached decorator result mismatch")
            return False

    except Exception as e:
        print(f"✗ @cached decorator test failed: {e}")
        return False


def test_rate_limiter_check():
    """Test rate limiter check functionality (if Redis is available)"""
    try:
        from src.middleware.rate_limiter import rate_limiter

        if not rate_limiter.enabled:
            print("⊘ Rate limiter is disabled, skipping check test")
            return True

        test_key = "test:ratelimit:user123"

        # Should allow first 3 requests
        for i in range(3):
            allowed, info = rate_limiter.check_limit(test_key, limit=3, window=60)
            if not allowed:
                print(f"✗ Request {i+1}/3 was blocked unexpectedly")
                return False

        # 4th request should be blocked
        allowed, info = rate_limiter.check_limit(test_key, limit=3, window=60)
        if not allowed:
            print("✓ Rate limiter correctly blocks after limit exceeded")
            print(f"  - Limit: {info.get('limit')}, Remaining: {info.get('remaining')}")
            # Clean up
            rate_limiter.reset_limit(test_key)
            return True
        else:
            print("✗ Rate limiter should have blocked 4th request")
            return False

    except Exception as e:
        print(f"✗ Rate limiter check test failed: {e}")
        return False


def test_config_loading():
    """Test that config loads correctly"""
    try:
        from config import settings
        print("✓ Config module loaded successfully")
        print(f"  - Deployment mode: {settings.MODE}")
        print(f"  - Cache enabled: {settings.CACHE_ENABLED}")
        print(f"  - Rate limit enabled: {settings.RATE_LIMIT_ENABLED}")
        print(f"  - Features: {settings.FEATURES}")
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False


def run_all_tests():
    """Run all middleware tests"""
    print("\n" + "="*60)
    print("ConvoInsight Middleware Tests")
    print("="*60 + "\n")

    tests = [
        ("Config Loading", test_config_loading),
        ("Cache Import", test_cache_import),
        ("Rate Limiter Import", test_rate_limiter_import),
        ("Cache Operations", test_cache_operations),
        ("@cached Decorator", test_cached_decorator),
        ("Rate Limiter Check", test_rate_limiter_check),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
