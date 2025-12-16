# pgAdmin4 Setup Guide - Visual PostgreSQL Management

Guide lengkap untuk setup dan menggunakan pgAdmin4 untuk manage PostgreSQL database ConvoInsight.

---

## 🎨 Overview

**pgAdmin4** adalah web-based GUI tool untuk manage PostgreSQL database dengan mudah:
- ✅ Visual query builder
- ✅ Table browser & editor
- ✅ SQL query tool dengan syntax highlighting
- ✅ Database monitoring & statistics
- ✅ Backup & restore
- ✅ User management

**Access URL**: http://localhost:5050

---

## 🚀 Quick Start

### Step 1: Start pgAdmin4

```bash
# Start all services (Redis, PostgreSQL, pgAdmin)
docker compose up -d

# Verify pgAdmin is running
docker compose ps

# Expected output:
# NAME                      STATUS          PORTS
# convoinsight-pgadmin      Up              0.0.0.0:5050->80/tcp
# convoinsight-postgres     Up              0.0.0.0:5432->5432/tcp
# convoinsight-redis        Up              0.0.0.0:6379->6379/tcp
```

### Step 2: Open pgAdmin4

1. Buka browser
2. Go to: **http://localhost:5050**
3. Login dengan credentials:
   - **Email**: `admin@convoinsight.local`
   - **Password**: `admin123`

### Step 3: Add PostgreSQL Server Connection

#### 3.1 Click "Add New Server"
- Klik kanan pada "Servers" di sidebar kiri
- Pilih **"Register" → "Server..."**

#### 3.2 General Tab
- **Name**: `ConvoInsight Local`
- **Server Group**: `Servers` (default)
- **Comments**: `Local development database`

#### 3.3 Connection Tab
Masukkan detail koneksi PostgreSQL:

| Field | Value |
|-------|-------|
| **Host name/address** | `postgres` |
| **Port** | `5432` |
| **Maintenance database** | `convoinsight` |
| **Username** | `convoinsight` |
| **Password** | `dev_password_change_in_production` |
| **Save password?** | ✓ Check this |

**IMPORTANT**:
- Gunakan hostname `postgres` (bukan `localhost`)
- Ini karena pgAdmin dan PostgreSQL dalam Docker network yang sama

#### 3.4 Click "Save"

✅ Server connected! Kamu sekarang bisa explore database.

---

## 📊 Using pgAdmin4

### Browse Tables

1. Di sidebar kiri, expand:
   ```
   Servers
   └── ConvoInsight Local
       └── Databases
           └── convoinsight
               └── Schemas
                   └── public
                       └── Tables
   ```

2. Klik pada table (e.g., `sample_data`)
3. Klik kanan → **View/Edit Data** → **All Rows**

### Run SQL Queries

1. Klik kanan pada database `convoinsight`
2. Pilih **"Query Tool"**
3. Tulis SQL query:
   ```sql
   SELECT * FROM sample_data;
   ```
4. Click **Execute** (⚡ icon) atau tekan `F5`

### Create New Table

1. Klik kanan pada **Tables**
2. Pilih **Create** → **Table...**
3. **General Tab**:
   - Name: `users`
4. **Columns Tab**:
   - Click **+** untuk add column
   - Name: `id`, Data type: `integer`, Not NULL: ✓
   - Name: `email`, Data type: `character varying(255)`
   - Name: `created_at`, Data type: `timestamp`, Default: `CURRENT_TIMESTAMP`
5. Click **Save**

### Import Data (CSV)

1. Klik kanan pada table
2. Pilih **Import/Export Data...**
3. **Import/Export**: Import
4. **Filename**: Browse ke CSV file
5. **Format**: csv
6. **Header**: ✓ (jika CSV ada header)
7. Click **OK**

### Export Data

1. Klik kanan pada table
2. Pilih **Import/Export Data...**
3. **Import/Export**: Export
4. **Filename**: `/tmp/export.csv`
5. **Format**: csv
6. Click **OK**
7. Download dari container:
   ```bash
   docker compose cp pgadmin:/tmp/export.csv ./export.csv
   ```

### Backup Database

1. Klik kanan pada database `convoinsight`
2. Pilih **Backup...**
3. **Filename**: `/tmp/backup.sql`
4. **Format**: Plain (SQL)
5. Click **Backup**
6. Download:
   ```bash
   docker compose cp pgadmin:/tmp/backup.sql ./backup.sql
   ```

### Restore Database

1. Klik kanan pada database
2. Pilih **Restore...**
3. **Filename**: Upload backup file
4. **Format**: Plain
5. Click **Restore**

---

## 🔧 Configuration

### Default Credentials

**pgAdmin Login**:
- Email: `admin@convoinsight.local`
- Password: `admin123`

**PostgreSQL Connection**:
- Host: `postgres` (di Docker network)
- Port: `5432`
- Database: `convoinsight`
- User: `convoinsight`
- Password: `dev_password_change_in_production`

### Change pgAdmin Password

Edit `docker-compose.yml`:
```yaml
pgadmin:
  environment:
    PGADMIN_DEFAULT_EMAIL: your-email@example.com
    PGADMIN_DEFAULT_PASSWORD: your-secure-password
```

Restart:
```bash
docker compose down
docker compose up -d
```

### Change Port

Edit `docker-compose.yml`:
```yaml
pgadmin:
  ports:
    - "8080:80"  # Access on http://localhost:8080
```

---

## 📱 Features Tour

### 1. Dashboard
- Database statistics
- Server activity
- Session info
- Database size

### 2. Query Tool
- **Syntax Highlighting**: Color-coded SQL
- **Auto-complete**: Ctrl+Space untuk suggestions
- **Explain Plans**: Analyze query performance
- **History**: View previous queries
- **Download Results**: Export ke CSV/JSON

### 3. Schema Browser
- **Visual ERD**: Entity Relationship Diagram
- **Dependencies**: See table relationships
- **Permissions**: Manage user access

### 4. Monitoring
- **Server Status**: CPU, Memory usage
- **Active Sessions**: Current connections
- **Lock Info**: Table locks
- **Database Statistics**: Transaction counts

### 5. Tools
- **PSQL Tool**: Terminal access
- **Grant Wizard**: Easy permission management
- **Maintenance**: VACUUM, ANALYZE, REINDEX

---

## 💡 Useful SQL Queries

### List All Tables
```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public';
```

### Table Size
```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Active Connections
```sql
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'convoinsight';
```

### Database Size
```sql
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'convoinsight';
```

### Create Test Data
```sql
-- Insert sample users
INSERT INTO sample_data (name, value) VALUES
    ('Product A', 150.00),
    ('Product B', 275.50),
    ('Product C', 420.75);

-- Check inserted data
SELECT * FROM sample_data ORDER BY created_at DESC LIMIT 5;
```

### View Query Performance
```sql
-- In Query Tool, click "Explain" button (or F7)
-- This shows query execution plan
EXPLAIN ANALYZE
SELECT * FROM sample_data WHERE value > 100;
```

---

## 🚨 Troubleshooting

### Cannot Access http://localhost:5050

**Check if pgAdmin running:**
```bash
docker compose ps pgadmin
```

**If not running:**
```bash
docker compose up -d pgadmin
```

**Check logs:**
```bash
docker compose logs pgadmin
```

### Login Failed

**Reset pgAdmin:**
```bash
# Remove pgAdmin data (will reset login)
docker compose down
docker volume rm convoinsight-be-flask-prod_pgadmin_data
docker compose up -d
```

Default credentials:
- Email: `admin@convoinsight.local`
- Password: `admin123`

### Cannot Connect to PostgreSQL

**Error: "could not connect to server"**

Check hostname in connection settings:
- ✅ Use: `postgres` (Docker network hostname)
- ❌ NOT: `localhost` or `127.0.0.1`

**Verify PostgreSQL is running:**
```bash
docker compose ps postgres
docker compose exec postgres pg_isready -U convoinsight
```

### Port Already in Use (5050)

**Change pgAdmin port:**

Edit `docker-compose.yml`:
```yaml
pgadmin:
  ports:
    - "5051:80"  # Use port 5051 instead
```

Restart:
```bash
docker compose restart pgadmin
```

Access on: http://localhost:5051

### Slow Performance

pgAdmin can be slow on first load.

**Optimize:**
1. Disable automatic statistics collection:
   - File → Preferences → Dashboards
   - Uncheck "Show activity?"
2. Reduce refresh rate
3. Close unused query tabs

---

## 🎓 Pro Tips

### 1. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Execute query |
| `F7` | EXPLAIN query |
| `F8` | Execute EXPLAIN ANALYZE |
| `Ctrl + Space` | Auto-complete |
| `Ctrl + Shift + C` | Comment lines |
| `Ctrl + /` | Uncomment lines |

### 2. Save Favorite Queries

1. Write query in Query Tool
2. Click **Save** icon (💾)
3. Give it a name
4. Access later from **Macros** menu

### 3. Custom Dashboard

1. **Dashboard** tab
2. Click **⚙️ Configure**
3. Add/remove widgets
4. Rearrange layout

### 4. ERD Generation

1. Right-click on database
2. **Generate ERD**
3. Select tables
4. View visual schema diagram

### 5. Schema Diff

1. **Tools** → **Schema Diff**
2. Compare two databases
3. Generate migration SQL

---

## 🔐 Security Best Practices

### For Development
Current setup is OK (simple passwords, no encryption).

### For Production

**1. Use Strong Passwords**
```yaml
PGADMIN_DEFAULT_PASSWORD: generate_secure_password_here
POSTGRES_PASSWORD: use_env_variable_from_secrets
```

**2. Enable SSL/TLS**
```yaml
postgres:
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/var/lib/postgresql/server.crt
    -c ssl_key_file=/var/lib/postgresql/server.key
```

**3. Restrict Network Access**
```yaml
pgadmin:
  ports:
    - "127.0.0.1:5050:80"  # Only localhost
```

**4. Use Reverse Proxy (nginx)**
- Add HTTPS
- Add authentication
- Add rate limiting

---

## 📋 Quick Reference

### URLs
- **pgAdmin**: http://localhost:5050
- **PostgreSQL**: localhost:5432

### Credentials
| Service | Username | Password |
|---------|----------|----------|
| pgAdmin | admin@convoinsight.local | admin123 |
| PostgreSQL | convoinsight | dev_password_change_in_production |

### Docker Commands
```bash
# Start all services
docker compose up -d

# Stop pgAdmin only
docker compose stop pgadmin

# Restart pgAdmin
docker compose restart pgadmin

# View pgAdmin logs
docker compose logs -f pgadmin

# Access pgAdmin container shell
docker compose exec pgadmin sh

# Remove pgAdmin data (reset)
docker volume rm convoinsight-be-flask-prod_pgadmin_data
```

---

## 🎯 Next Steps

After connecting pgAdmin:

1. ✅ Explore `sample_data` table
2. ✅ Run test queries
3. ✅ Create test tables
4. ✅ Practice import/export
5. 🚀 Ready for development!

---

## 📚 Resources

- **pgAdmin Docs**: https://www.pgadmin.org/docs/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **SQL Tutorial**: https://www.postgresql.org/docs/current/tutorial.html

---

**Setup Status**: ✅ **pgAdmin4 READY**

**Last Updated**: 2025-12-16
