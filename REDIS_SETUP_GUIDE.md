# Redis Setup Guide - ConvoInsight Backend

Simple guide untuk setup Redis (cache & rate limiting).

---

## 🎯 Overview

Redis digunakan untuk:
- ✅ **Caching**: Dataset list, query results, session state (70% cost reduction)
- ✅ **Rate Limiting**: Per-user/per-IP request throttling (20 req/min for queries)
- ✅ **Session Storage**: Fast session state management

---

## 🐳 Option 1: Docker (RECOMMENDED) ⭐

Redis **sudah included** di `docker-compose.yml`!

### Quick Start

```bash
# Start Redis + PostgreSQL
docker compose up -d

# Check if running
docker compose ps

# Expected output:
# NAME                      STATUS          PORTS
# convoinsight-redis        Up X seconds    0.0.0.0:6379->6379/tcp
# convoinsight-postgres     Up X seconds    0.0.0.0:5432->5432/tcp
```

### Test Redis Connection

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# In redis-cli:
127.0.0.1:6379> PING
PONG

127.0.0.1:6379> SET test "Hello Redis"
OK

127.0.0.1:6379> GET test
"Hello Redis"

127.0.0.1:6379> DEL test
(integer) 1

127.0.0.1:6379> EXIT
```

### Management Commands

```bash
# View Redis logs
docker compose logs redis

# Follow logs (real-time)
docker compose logs -f redis

# Restart Redis
docker compose restart redis

# Stop Redis
docker compose stop redis

# Monitor Redis activity (real-time)
docker compose exec redis redis-cli MONITOR

# Check Redis info
docker compose exec redis redis-cli INFO

# Flush all data (⚠️ clears cache)
docker compose exec redis redis-cli FLUSHALL
```

---

## 💻 Option 2: Native Redis Installation

### Windows

#### Using WSL2 (Recommended)
```bash
# Install WSL2 first (if not installed)
wsl --install

# In WSL Ubuntu terminal:
sudo apt update
sudo apt install redis-server

# Start Redis
sudo service redis-server start

# Test
redis-cli ping
# Output: PONG
```

#### Using Memurai (Redis for Windows)
1. Download from: https://www.memurai.com/get-memurai
2. Run installer
3. Start Memurai service
4. Test: `memurai-cli ping`

### macOS

```bash
# Install via Homebrew
brew install redis

# Start Redis as a service
brew services start redis

# Or run in foreground
redis-server

# Test connection
redis-cli ping
# Output: PONG

# Stop service
brew services stop redis
```

### Linux (Ubuntu/Debian)

```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Check status
sudo systemctl status redis-server

# Test connection
redis-cli ping
# Output: PONG
```

### Configure for Application

```bash
# Edit .env file
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
RATE_LIMIT_ENABLED=true
```

---

## 🌐 Option 3: Cloud Redis

### Redis Cloud (Free Tier Available)

1. **Sign up**: https://redis.com/try-free/
2. **Create database**:
   - Select "Free" plan (30 MB)
   - Choose region closest to you
   - Copy endpoint & password
3. **Configure**:
   ```env
   # .env
   REDIS_URL=redis://default:YOUR_PASSWORD@redis-xxxxx.cloud.redislabs.com:12345/0
   ```

### Upstash (Serverless Redis)

1. **Sign up**: https://upstash.com/
2. **Create database**:
   - Select region
   - Copy REST URL or Redis URL
3. **Configure**:
   ```env
   # .env
   REDIS_URL=redis://default:YOUR_TOKEN@us1-moral-xxxxxx.upstash.io:6379
   ```

### AWS ElastiCache / GCP Memorystore

For production deployments:
- AWS ElastiCache for Redis
- GCP Memorystore for Redis
- Azure Cache for Redis

---

## 🧪 Test Redis Setup

### Quick Test

Run this command:
```bash
python test_redis_connection.py
```

### Manual Test (redis-py)

```python
import redis

# Connect
r = redis.from_url("redis://localhost:6379/0")

# Test PING
print(r.ping())  # True

# Set value
r.set("test_key", "test_value", ex=10)  # expires in 10 seconds

# Get value
value = r.get("test_key")
print(value)  # b'test_value'

# Delete
r.delete("test_key")
```

---

## 🔧 Configuration

### Cache TTL Settings

In `config/settings.py`:
```python
CACHE_TTL = {
    "dataset_list": 60,           # 1 minute
    "dataset_content": 300,       # 5 minutes
    "query_result": 300,          # 5 minutes
    "session_state": 1800,        # 30 minutes
    "pg_connection": 600,         # 10 minutes
    "llm_models": 3600,           # 1 hour
}
```

### Rate Limit Settings

```python
RATE_LIMITS = {
    "default": "100/hour",        # General endpoints
    "query": "20/minute",         # Heavy LLM operations
    "upload": "50/hour",          # File uploads
    "dataset_ops": "200/hour",    # Dataset CRUD
    "auth": "10/minute",          # Authentication
}
```

### Environment Variables

```env
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Feature toggles
CACHE_ENABLED=true
RATE_LIMIT_ENABLED=true

# Optional: Custom TTL values
CACHE_TTL_DATASET_LIST=60
CACHE_TTL_QUERY_RESULT=300
```

---

## 📊 Monitoring Redis

### Check Memory Usage

```bash
# Docker
docker compose exec redis redis-cli INFO memory

# Native
redis-cli INFO memory
```

Key metrics:
- `used_memory_human`: Current memory usage
- `maxmemory`: Max memory limit
- `eviction_policy`: How Redis handles memory limit

### Monitor Commands

```bash
# Real-time monitoring
redis-cli MONITOR

# Stats
redis-cli INFO stats

# Connected clients
redis-cli CLIENT LIST

# Keyspace info
redis-cli INFO keyspace
```

### Useful Commands

```bash
# Count keys
redis-cli DBSIZE

# List all keys (⚠️ slow on large dataset)
redis-cli KEYS "*"

# List keys by pattern
redis-cli KEYS "ratelimit:*"
redis-cli KEYS "cache:dataset:*"

# Check key TTL
redis-cli TTL "cache:dataset:xxx"

# Check key type
redis-cli TYPE "cache:dataset:xxx"

# Delete by pattern (⚠️ careful!)
redis-cli --scan --pattern "cache:*" | xargs redis-cli DEL
```

---

## 🚨 Troubleshooting

### Error: "Connection refused"

**Docker**:
```bash
# Check if container running
docker compose ps

# If not running
docker compose up -d

# Check logs
docker compose logs redis
```

**Native**:
```bash
# Check service status
# macOS
brew services list

# Linux
sudo systemctl status redis-server

# If not running, start it
brew services start redis              # macOS
sudo systemctl start redis-server      # Linux
```

### Error: "Could not connect to Redis"

Check `.env` file:
```env
# For Docker
REDIS_URL=redis://localhost:6379/0

# For cloud
REDIS_URL=redis://default:password@host:port/0
```

Test connection:
```bash
redis-cli -u redis://localhost:6379/0 ping
```

### Error: "MISCONF Redis is configured to save RDB snapshots"

Redis disk full. Solutions:
```bash
# Temporary: Disable persistence
redis-cli CONFIG SET stop-writes-on-bgsave-error no

# Permanent: Free up disk space or disable persistence
# Edit redis.conf:
# save ""  # Disable RDB snapshots
```

### Error: "OOM command not allowed"

Redis out of memory:
```bash
# Check memory
redis-cli INFO memory

# Flush old data
redis-cli FLUSHDB

# Or increase maxmemory in redis.conf
# maxmemory 256mb
```

### Port 6379 Already in Use

```bash
# Find process using port
# Windows
netstat -ano | findstr :6379

# Mac/Linux
lsof -i :6379

# Option 1: Stop conflicting process
# Option 2: Change Redis port

# In docker-compose.yml:
# ports:
#   - "6380:6379"

# In .env:
# REDIS_URL=redis://localhost:6380/0
```

---

## 🔐 Security (Production)

### Enable Authentication

**Docker**: Edit `docker-compose.yml`:
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass your_secure_password
  # ...
```

**Native**: Edit `/etc/redis/redis.conf`:
```conf
requirepass your_secure_password
```

**Update connection URL**:
```env
REDIS_URL=redis://:your_secure_password@localhost:6379/0
```

### Disable Dangerous Commands

In `redis.conf`:
```conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""
```

### Network Security

```conf
# Bind to localhost only (not internet-accessible)
bind 127.0.0.1

# Or specific IP
bind 127.0.0.1 192.168.1.100
```

---

## ⚡ Performance Tips

### 1. Use Appropriate Data Structures

```python
# String for simple cache
cache.set("key", "value")

# Hash for objects
r.hset("user:123", mapping={"name": "John", "age": 30})

# Sorted Set for rankings
r.zadd("leaderboard", {"user1": 100, "user2": 200})
```

### 2. Set Appropriate TTLs

- Short TTL (1-5 min): Frequently changing data
- Medium TTL (5-30 min): Dataset lists, configs
- Long TTL (1-24 hours): Static data, LLM models

### 3. Use Pipelining for Bulk Operations

```python
pipe = r.pipeline()
for i in range(100):
    pipe.set(f"key:{i}", f"value:{i}")
pipe.execute()
```

### 4. Monitor Hit Rate

```bash
redis-cli INFO stats | grep keyspace
# keyspace_hits: High is good
# keyspace_misses: Low is good
```

Good hit rate: > 80%

---

## 📋 Quick Reference

### Connection URLs

**Local (Docker)**:
```
redis://localhost:6379/0
```

**Local (Native)**:
```
redis://localhost:6379/0
```

**With Password**:
```
redis://:password@localhost:6379/0
redis://username:password@localhost:6379/0
```

**Cloud**:
```
redis://default:token@host.cloud.provider.com:6379
```

### Common Commands

```bash
# Ping
redis-cli ping

# Set/Get
redis-cli SET key value
redis-cli GET key

# Delete
redis-cli DEL key

# Flush database
redis-cli FLUSHDB

# Info
redis-cli INFO

# Monitor
redis-cli MONITOR

# List keys
redis-cli KEYS "*"

# Check TTL
redis-cli TTL key
```

---

## ✅ Checklist

After Redis setup:

- [ ] Redis running: `docker compose ps` or `redis-cli ping`
- [ ] Connection test pass: `python test_redis_connection.py`
- [ ] Cache test pass: `python tests/test_middleware_basic.py`
- [ ] `.env` configured with `REDIS_URL`
- [ ] `CACHE_ENABLED=true` and `RATE_LIMIT_ENABLED=true`

---

## 🎯 Next Steps

Once Redis is running:

1. ✅ Test connection: `python test_redis_connection.py`
2. ✅ Test middleware: `python tests/test_middleware_basic.py`
3. ✅ Verify cache working in app
4. 🚀 Ready for Phase 2: Prompt Externalization

---

## 📚 Resources

- Redis Documentation: https://redis.io/docs/
- redis-py Documentation: https://redis-py.readthedocs.io/
- Redis Commands Reference: https://redis.io/commands/
- Redis Best Practices: https://redis.io/docs/manual/patterns/

---

**Need help?** Check troubleshooting section or test with `redis-cli ping`.
