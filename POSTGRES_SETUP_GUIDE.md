# PostgreSQL Setup Guide - ConvoInsight Backend

Complete guide untuk setup PostgreSQL dari download sampai siap pakai.

---

## 🐳 Option 1: Docker Setup (RECOMMENDED) ⭐

Paling mudah dan konsisten, sudah termasuk Redis juga.

### Prerequisites
- Docker Desktop installed
- Docker Compose installed (biasanya sudah include di Docker Desktop)

### Step 1: Check Docker Installation

```bash
# Cek Docker version
docker --version
# Output: Docker version 24.x.x, build xxxxx

# Cek Docker Compose
docker compose version
# Output: Docker Compose version v2.x.x
```

**Jika belum ada Docker:**
- **Windows/Mac**: Download Docker Desktop dari https://www.docker.com/products/docker-desktop
- **Linux**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install docker.io docker-compose-plugin

  # Start Docker
  sudo systemctl start docker
  sudo systemctl enable docker
  ```

### Step 2: Start PostgreSQL & Redis

```bash
# Navigate to project directory
cd /path/to/convoinsight-be-flask-prod

# Start services in background (-d = detached mode)
docker compose up -d

# Expected output:
# [+] Running 3/3
#  ✔ Network convoinsight-network     Created
#  ✔ Container convoinsight-postgres  Started
#  ✔ Container convoinsight-redis     Started
```

### Step 3: Verify Services Running

```bash
# Check container status
docker compose ps

# Expected output:
# NAME                      STATUS          PORTS
# convoinsight-postgres     Up 10 seconds   0.0.0.0:5432->5432/tcp
# convoinsight-redis        Up 10 seconds   0.0.0.0:6379->6379/tcp
```

### Step 4: Test PostgreSQL Connection

```bash
# Connect to PostgreSQL container
docker compose exec postgres psql -U convoinsight -d convoinsight

# You should see PostgreSQL prompt:
# psql (16.x)
# Type "help" for help.
#
# convoinsight=#
```

**Test queries:**
```sql
-- List databases
\l

-- List tables
\dt

-- Check sample data
SELECT * FROM sample_data;

-- Expected output:
--  id |     name     | value  |       created_at
-- ----+--------------+--------+-------------------------
--   1 | Test Item 1  | 100.50 | 2025-12-16 10:30:00
--   2 | Test Item 2  | 250.75 | 2025-12-16 10:30:00
--   3 | Test Item 3  | 300.00 | 2025-12-16 10:30:00

-- Exit psql
\q
```

### Step 5: Configure Application

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # atau code .env (VSCode) / vim .env
```

Set PostgreSQL URL:
```env
# For Docker setup
DEPLOYMENT_MODE=local
LOCAL_POSTGRES_URL=postgresql://convoinsight:dev_password_change_in_production@localhost:5432/convoinsight
REDIS_URL=redis://localhost:6379/0
```

### Step 6: Test from Python

Create test file `test_postgres_connection.py`:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from config.settings import get_postgres_url

def test_connection():
    try:
        # Get PostgreSQL URL from config
        pg_url = get_postgres_url()
        print(f"Connecting to: {pg_url}")

        # Create engine
        engine = create_engine(pg_url)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Connected successfully!")
            print(f"  PostgreSQL version: {version}")

            # Test sample data
            result = conn.execute(text("SELECT COUNT(*) FROM sample_data"))
            count = result.scalar()
            print(f"  Sample data rows: {count}")

        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

Run test:
```bash
python test_postgres_connection.py
```

Expected output:
```
Connecting to: postgresql://convoinsight:***@localhost:5432/convoinsight
✓ Connected successfully!
  PostgreSQL version: PostgreSQL 16.1 on x86_64-pc-linux-musl, compiled by gcc (Alpine 13.2.1_git20231014) 13.2.1 20231014, 64-bit
  Sample data rows: 3
```

### Step 7: Management Commands

```bash
# View logs
docker compose logs postgres
docker compose logs redis

# Follow logs (real-time)
docker compose logs -f postgres

# Stop services
docker compose stop

# Start services again
docker compose start

# Restart services
docker compose restart

# Stop and remove containers (data preserved in volumes)
docker compose down

# Stop and remove containers + volumes (⚠️ deletes data)
docker compose down -v

# Backup database
docker compose exec postgres pg_dump -U convoinsight convoinsight > backup.sql

# Restore database
docker compose exec -T postgres psql -U convoinsight convoinsight < backup.sql
```

---

## 💻 Option 2: Native PostgreSQL Installation

Untuk yang ingin install PostgreSQL langsung di OS.

### Windows

#### Step 1: Download PostgreSQL
1. Visit https://www.postgresql.org/download/windows/
2. Download **PostgreSQL 16.x** installer (recommended)
3. Run installer `postgresql-16.x-windows-x64.exe`

#### Step 2: Installation Wizard
1. Click **Next** through welcome screen
2. **Installation Directory**: Default OK (`C:\Program Files\PostgreSQL\16`)
3. **Select Components**: Check all (PostgreSQL Server, pgAdmin 4, Command Line Tools)
4. **Data Directory**: Default OK (`C:\Program Files\PostgreSQL\16\data`)
5. **Password**: Set superuser (postgres) password → **REMEMBER THIS!**
6. **Port**: `5432` (default)
7. **Locale**: Default
8. Click **Next** → **Install**

#### Step 3: Post-Installation
```bash
# Add to PATH (if not added automatically)
# Windows: Search "Environment Variables" → Edit System Variables → PATH
# Add: C:\Program Files\PostgreSQL\16\bin

# Test installation (Command Prompt / PowerShell)
psql --version
# Output: psql (PostgreSQL) 16.x
```

#### Step 4: Create Database and User
```bash
# Connect as superuser
psql -U postgres

# In psql prompt:
CREATE USER convoinsight WITH PASSWORD 'your_secure_password';
CREATE DATABASE convoinsight OWNER convoinsight;
GRANT ALL PRIVILEGES ON DATABASE convoinsight TO convoinsight;

# Connect to new database
\c convoinsight

# Run initialization script
\i 'C:/path/to/convoinsight-be-flask-prod/scripts/init_db.sql'

# Exit
\q
```

#### Step 5: Configure Application
```env
# .env file
DEPLOYMENT_MODE=local
LOCAL_POSTGRES_URL=postgresql://convoinsight:your_secure_password@localhost:5432/convoinsight
```

### macOS

#### Step 1: Install via Homebrew (Recommended)
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@16

# Start PostgreSQL service
brew services start postgresql@16

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Step 2: Create Database and User
```bash
# Connect to PostgreSQL
psql postgres

# Create user and database
CREATE USER convoinsight WITH PASSWORD 'your_secure_password';
CREATE DATABASE convoinsight OWNER convoinsight;
GRANT ALL PRIVILEGES ON DATABASE convoinsight TO convoinsight;

\q

# Initialize database
psql -U convoinsight -d convoinsight -f scripts/init_db.sql
```

#### Step 3: Configure Application
```env
# .env file
DEPLOYMENT_MODE=local
LOCAL_POSTGRES_URL=postgresql://convoinsight:your_secure_password@localhost:5432/convoinsight
```

### Linux (Ubuntu/Debian)

#### Step 1: Install PostgreSQL
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

#### Step 2: Create Database and User
```bash
# Switch to postgres user
sudo -i -u postgres

# Open PostgreSQL prompt
psql

# Create user and database
CREATE USER convoinsight WITH PASSWORD 'your_secure_password';
CREATE DATABASE convoinsight OWNER convoinsight;
GRANT ALL PRIVILEGES ON DATABASE convoinsight TO convoinsight;

\q
exit

# Initialize database
sudo -u postgres psql -U convoinsight -d convoinsight -f scripts/init_db.sql
```

#### Step 3: Allow Local Connections
```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/16/main/pg_hba.conf

# Add line (or change 'peer' to 'md5'):
# local   all             convoinsight                            md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Step 4: Configure Application
```env
# .env file
DEPLOYMENT_MODE=local
LOCAL_POSTGRES_URL=postgresql://convoinsight:your_secure_password@localhost:5432/convoinsight
```

---

## 🌐 Option 3: Cloud PostgreSQL (Supabase)

Untuk production atau jika tidak ingin install lokal.

### Step 1: Create Supabase Account
1. Go to https://supabase.com
2. Sign up / Sign in
3. Click **"New Project"**

### Step 2: Create Project
1. **Name**: `convoinsight`
2. **Database Password**: Generate strong password → **SAVE THIS!**
3. **Region**: Pilih yang terdekat (e.g., `Southeast Asia (Singapore)`)
4. Click **"Create new project"**
5. Wait ~2 minutes for provisioning

### Step 3: Get Connection String
1. Go to **Project Settings** (gear icon)
2. Click **Database** tab
3. Scroll to **Connection String** section
4. Copy **Connection pooling** → **Transaction Mode** string:
   ```
   postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```

### Step 4: Initialize Database
```bash
# Install psql if not available
# Windows: Include in PostgreSQL installation
# Mac: brew install libpq
# Linux: sudo apt install postgresql-client

# Connect to Supabase
psql "postgresql://postgres.xxx:YOUR-PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# Run initialization script
\i scripts/init_db.sql

\q
```

### Step 5: Configure Application
```env
# .env file
DEPLOYMENT_MODE=cloud
POSTGRES_URL=postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
```

---

## 🧪 Test PostgreSQL Setup

### Python Test Script

Create `test_postgres_full.py`:
```python
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
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            assert result.scalar() == 1

        print("✓ Basic connection works")
        return True
    except Exception as e:
        print(f"✗ Basic connection failed: {e}")
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
            result = conn.execute(text("SELECT COUNT(*) FROM sample_data"))
            count = result.scalar()

            if count >= 3:
                print(f"✓ Sample data exists ({count} rows)")

                # Show sample
                result = conn.execute(text("SELECT * FROM sample_data LIMIT 3"))
                rows = result.fetchall()
                print("\n  Sample rows:")
                for row in rows:
                    print(f"    {row}")

                return True
            else:
                print(f"⚠ Sample data incomplete ({count} rows, expected >= 3)")
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
            except:
                # Fallback to pandas
                import pandas as pd
                pdf = pd.read_sql("SELECT * FROM sample_data", conn)
                df = pl.from_pandas(pdf)

            print(f"✓ Polars DataFrame created")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {df.columns}")

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

        pg_url = get_postgres_url()
        engine = create_engine(pg_url)

        with engine.connect() as conn:
            # Create test table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_temp (
                    id SERIAL PRIMARY KEY,
                    message TEXT
                )
            """))
            conn.commit()

            # Insert data
            conn.execute(text("""
                INSERT INTO test_temp (message) VALUES ('Test from Python')
            """))
            conn.commit()

            # Read back
            result = conn.execute(text("SELECT message FROM test_temp LIMIT 1"))
            message = result.scalar()

            # Cleanup
            conn.execute(text("DROP TABLE test_temp"))
            conn.commit()

            if message == "Test from Python":
                print("✓ Write operation successful")
                return True
            else:
                print("✗ Write operation failed: data mismatch")
                return False

    except Exception as e:
        print(f"✗ Write operation failed: {e}")
        return False

def main():
    print("="*60)
    print("PostgreSQL Setup Test")
    print("="*60)

    tests = [
        test_basic_connection,
        test_sample_data,
        test_polars_integration,
        test_write_operation,
    ]

    results = [test() for test in tests]

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"\n✓ All {total} tests passed! PostgreSQL is ready to use.")
        return 0
    else:
        print(f"\n⚠ {passed}/{total} tests passed. Please fix issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Run test:
```bash
python test_postgres_full.py
```

---

## 🔧 Troubleshooting

### Error: "psql: command not found"
**Solution**: Add PostgreSQL bin directory to PATH or use full path.
```bash
# Windows
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres

# Mac
/opt/homebrew/opt/postgresql@16/bin/psql postgres

# Linux
sudo apt install postgresql-client
```

### Error: "connection refused"
**Solution**: Check if PostgreSQL is running.
```bash
# Docker
docker compose ps

# Native - Windows
services.msc → PostgreSQL 16 Server → Start

# Native - Mac
brew services list
brew services start postgresql@16

# Native - Linux
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Error: "password authentication failed"
**Solution**:
1. Check password in `.env` file
2. For Docker: password is `dev_password_change_in_production`
3. For native: use password you set during installation

### Error: "database does not exist"
**Solution**: Create database first.
```bash
# Connect as superuser
psql -U postgres  # or docker compose exec postgres psql -U postgres

# Create database
CREATE DATABASE convoinsight;
```

### Docker: "port already allocated"
**Solution**: Another service using port 5432.
```bash
# Find process using port
# Windows
netstat -ano | findstr :5432

# Mac/Linux
lsof -i :5432

# Change port in docker-compose.yml
# ports:
#   - "5433:5432"  # Use host port 5433 instead
```

---

## 📋 Quick Reference

### Connection URLs

**Docker (default)**:
```
postgresql://convoinsight:dev_password_change_in_production@localhost:5432/convoinsight
```

**Native (custom password)**:
```
postgresql://convoinsight:YOUR_PASSWORD@localhost:5432/convoinsight
```

**Supabase (transaction pooler)**:
```
postgresql://postgres.xxx:PASSWORD@host.pooler.supabase.com:6543/postgres?sslmode=require
```

### Common Commands

```bash
# Connect to database
psql -U convoinsight -d convoinsight

# List databases
psql -U postgres -l

# List tables in database
psql -U convoinsight -d convoinsight -c "\dt"

# Execute SQL file
psql -U convoinsight -d convoinsight -f scripts/init_db.sql

# Dump database
pg_dump -U convoinsight convoinsight > backup.sql

# Restore database
psql -U convoinsight -d convoinsight < backup.sql
```

---

## ✅ Next Steps

Once PostgreSQL is working:

1. ✅ Test connection: `python test_postgres_full.py`
2. ✅ Verify `.env` configuration
3. ✅ Run middleware tests: `python tests/test_middleware_basic.py`
4. 🚀 Ready for Phase 2: Prompt Externalization

---

**Need help?** Check specific error messages in troubleshooting section above.
