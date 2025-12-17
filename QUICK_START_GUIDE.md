# 🚀 ConvoInsight Backend - Quick Start Guide

**One-page setup guide dari nol sampai ready to code!**

Waktu setup: ~15 menit

---

## 📋 Prerequisites

Yang perlu diinstall dulu:
- **Docker Desktop** - untuk Redis, PostgreSQL, pgAdmin4
- **Python 3.8-3.11** - untuk aplikasi Flask

---

## ⚡ Step 1: Install Docker Desktop

### Windows & Mac
1. Download dari https://www.docker.com/products/docker-desktop
2. Install dan restart komputer
3. Buka Docker Desktop
4. Tunggu sampai Docker running (icon hijau)

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
```

**Test Docker:**
```bash
docker --version
# Output: Docker version 24.x.x
```

✅ Docker ready!

---

## 🐳 Step 2: Clone & Start Infrastructure

```bash
# 1. Clone repository (atau navigate ke existing folder)
cd /path/to/convoinsight-be-flask-prod

# 2. Start SEMUA services (Redis + PostgreSQL + pgAdmin)
docker compose up -d

# 3. Verify services running
docker compose ps
```

**Expected output:**
```
NAME                      STATUS          PORTS
convoinsight-redis        Up              0.0.0.0:6379->6379/tcp
convoinsight-postgres     Up              0.0.0.0:5432->5432/tcp
convoinsight-pgadmin      Up              0.0.0.0:5050->80/tcp
```

✅ Semua services running!

---

## 🔧 Step 3: Configure Environment

```bash
# 1. Copy template
cp .env.example .env

# 2. File .env sudah OK untuk local development!
# Tidak perlu edit apapun untuk basic setup
```

**Isi .env (sudah configured by default):**
```env
DEPLOYMENT_MODE=local
REDIS_URL=redis://localhost:6379/0
LOCAL_POSTGRES_URL=postgresql://convoinsight:dev_password_change_in_production@localhost:5432/convoinsight
CACHE_ENABLED=true
RATE_LIMIT_ENABLED=true
```

✅ Environment configured!

---

## 🐍 Step 4: Install Python Dependencies

```bash
# Recommended: Pakai virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Wait ~2-3 minutes** untuk install semua packages (26 packages).

✅ Dependencies installed!

---

## ✅ Step 5: Verify Everything Works

### 5.1 Test Redis
```bash
python test_redis_connection.py
```

**Expected output:**
```
✓ Connection successful!
Redis Version: 7.2.4
✓ Redis is ready to use!
```

### 5.2 Test PostgreSQL
```bash
python test_postgres_connection.py
```

**Expected output:**
```
✓ Connection successful!
Database: convoinsight
✓ Sample data table exists (3 rows)
✓ PostgreSQL is ready to use!
```

### 5.3 Test Middleware (Cache + Rate Limiter)
```bash
python tests/test_middleware_basic.py
```

**Expected output:**
```
✓ PASS: Config Loading
✓ PASS: Cache Import
✓ PASS: Rate Limiter Import
✓ PASS: Cache Operations
✓ PASS: @cached Decorator
✓ PASS: Rate Limiter Check

Total: 6/6 tests passed
🎉 All tests passed!
```

✅ **All systems operational!**

---

## 🎨 Step 6: Access pgAdmin4 (Web GUI)

### 6.1 Open Browser
Go to: **http://localhost:5050**

### 6.2 Login
- **Email**: `admin@convoinsight.local`
- **Password**: `admin123`

### 6.3 PostgreSQL Already Connected!
Di sidebar kiri, expand:
```
Servers
└── ConvoInsight Local  ← Already connected!
    └── Databases
        └── convoinsight
            └── Schemas
                └── public
                    └── Tables
                        └── sample_data  ← Your data here
```

### 6.4 Test Query
1. Right-click on database `convoinsight`
2. Click **"Query Tool"**
3. Run:
   ```sql
   SELECT * FROM sample_data;
   ```
4. Press **F5** atau click ⚡ Execute

**Lihat 3 rows data!**

✅ pgAdmin4 working!

---

## 🎯 You're Ready!

### What You Have Now:
- ✅ **Redis** (localhost:6379) - Caching & rate limiting
- ✅ **PostgreSQL** (localhost:5432) - Database
- ✅ **pgAdmin4** (http://localhost:5050) - GUI management
- ✅ **Python dependencies** - Flask + all libraries
- ✅ **Tests passing** - Everything verified

### Services Status
```bash
# Check anytime dengan:
docker compose ps

# View logs:
docker compose logs redis
docker compose logs postgres
docker compose logs pgadmin

# Restart service:
docker compose restart redis
docker compose restart postgres
docker compose restart pgadmin

# Stop all:
docker compose stop

# Start all:
docker compose start
```

---

## 🚀 Next: Run Your Application

```bash
# Make sure virtual environment active
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run Flask app
python main.py
```

**Expected:**
```
 * Running on http://0.0.0.0:8080
 * Debug mode: off
```

Open: **http://localhost:8080**

---

## 📊 Quick Reference

### URLs
| Service | URL | Credentials |
|---------|-----|-------------|
| **pgAdmin4** | http://localhost:5050 | admin@convoinsight.local / admin123 |
| **Flask App** | http://localhost:8080 | - |
| **Redis** | localhost:6379 | (no auth) |
| **PostgreSQL** | localhost:5432 | convoinsight / dev_password_change_in_production |

### Docker Commands
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart all
docker compose restart

# View logs (real-time)
docker compose logs -f

# Remove all (including data)
docker compose down -v  # ⚠️ This deletes data!
```

### Python Commands
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Test connections
python test_redis_connection.py
python test_postgres_connection.py
python tests/test_middleware_basic.py

# Run app
python main.py
```

---

## 🐛 Troubleshooting

### Issue: "docker: command not found"
**Solution**: Install Docker Desktop dan pastikan running.

### Issue: "Port already in use"
**Solution**: Ada service lain pakai port yang sama.

```bash
# Check what's using port
# Windows:
netstat -ano | findstr :5432
netstat -ano | findstr :6379
netstat -ano | findstr :5050

# Mac/Linux:
lsof -i :5432
lsof -i :6379
lsof -i :5050

# Kill process atau change port di docker-compose.yml
```

### Issue: Docker containers not starting
**Solution**:
```bash
# Stop all
docker compose down

# Remove volumes (if corrupted)
docker compose down -v

# Start fresh
docker compose up -d
```

### Issue: "pip: command not found"
**Solution**: Install Python dari https://python.org

### Issue: pgAdmin login failed
**Default credentials:**
- Email: `admin@convoinsight.local`
- Password: `admin123`

**Reset pgAdmin:**
```bash
docker compose down
docker volume rm convoinsight-be-flask-prod_pgadmin_data
docker compose up -d
```

### Issue: Cannot connect to PostgreSQL from pgAdmin
**Important**: Use hostname `postgres` (NOT localhost!)
- Host: `postgres`
- Port: `5432`
- Database: `convoinsight`
- Username: `convoinsight`
- Password: `dev_password_change_in_production`

### Issue: Tests failing with "No module named..."
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

---

## 📝 Configuration Files Cheat Sheet

### docker-compose.yml
Defines 3 services:
- `redis` - Port 6379
- `postgres` - Port 5432
- `pgadmin` - Port 5050

### .env
Environment variables untuk aplikasi:
- `REDIS_URL` - Redis connection
- `LOCAL_POSTGRES_URL` - PostgreSQL connection
- `CACHE_ENABLED` - Enable caching
- `RATE_LIMIT_ENABLED` - Enable rate limiting

### requirements.txt
26 Python packages:
- Flask, Redis, PostgreSQL drivers
- Data processing (Polars, PandasAI)
- LLM integrations (LiteLLM)
- Visualization (Plotly)

---

## 🎓 What Each Service Does

### Redis (Port 6379)
- **Caching**: Stores frequently accessed data (70% faster)
- **Rate Limiting**: Prevents API abuse (20 req/min)
- **Session Storage**: Fast temporary data

### PostgreSQL (Port 5432)
- **Main Database**: Stores application data
- **Development**: Local data for testing
- **Production Ready**: Can connect to Supabase

### pgAdmin4 (Port 5050)
- **Visual Interface**: GUI for PostgreSQL
- **Query Tool**: Write SQL with syntax highlighting
- **Table Browser**: View/edit data visually
- **Monitoring**: Database statistics

---

## 🎯 Success Checklist

Before starting development, ensure:

- [ ] Docker Desktop running
- [ ] `docker compose ps` shows 3 services UP
- [ ] `python test_redis_connection.py` passes ✓
- [ ] `python test_postgres_connection.py` passes ✓
- [ ] `python tests/test_middleware_basic.py` passes ✓
- [ ] pgAdmin4 accessible at http://localhost:5050
- [ ] PostgreSQL server connected in pgAdmin
- [ ] Virtual environment activated
- [ ] Can import modules: `python -c "import redis, sqlalchemy"`

**All checked?** → **You're ready to code!** 🎉

---

## 📚 Additional Documentation

If you need more details:

- **POSTGRES_SETUP_GUIDE.md** - Advanced PostgreSQL setup
- **REDIS_SETUP_GUIDE.md** - Advanced Redis configuration
- **PGADMIN_SETUP_GUIDE.md** - pgAdmin4 features tour
- **SETUP_COMPLETE.md** - Complete setup summary
- **ARCHITECTURE_REVIEW.md** - System architecture
- **IMPLEMENTATION_GUIDE.md** - Development phases

**For most cases, this Quick Start Guide is enough!**

---

## 🆘 Need Help?

### Quick Diagnostics
```bash
# Check Docker
docker --version
docker compose ps

# Check Python
python --version
pip list | grep -E "(redis|flask|sqlalchemy)"

# Check services
curl -I http://localhost:5050  # pgAdmin
redis-cli ping  # Redis (if redis-cli installed)
```

### Common Issues

1. **Docker not running**: Start Docker Desktop
2. **Port conflicts**: Change ports in docker-compose.yml
3. **Permission denied**: Run with sudo (Linux) or as Administrator (Windows)
4. **Dependencies not installing**: Check Python version (3.8-3.11)
5. **Connection refused**: Ensure services running with `docker compose ps`

---

## 🎊 Summary

**What you did:**
1. ✅ Installed Docker Desktop
2. ✅ Started Redis + PostgreSQL + pgAdmin with one command
3. ✅ Configured environment variables
4. ✅ Installed Python dependencies
5. ✅ Verified all systems working
6. ✅ Accessed pgAdmin4 GUI

**Time taken:** ~15 minutes

**Result:** Fully functional development environment!

---

**Next:** Start coding! 🚀

**Questions?** Check troubleshooting section above.

---

**Last Updated**: 2025-12-16
**Status**: ✅ Production Ready
