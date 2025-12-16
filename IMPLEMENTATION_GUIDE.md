# Implementation Guide - ConvoInsight Modular Architecture

## 🎯 Ringkasan Eksekutif

### Current Issues (main.py 3,396 lines)
1. ❌ Monolithic - sulit maintain dan test
2. ❌ No caching - API call berulang ke LLM/GCS
3. ❌ No rate limiting - risiko abuse & biaya tinggi
4. ❌ Hard-coded prompts - sulit iterasi
5. ❌ PostgreSQL limited - hanya test connection
6. ❌ Cloud-only - tidak bisa local dev tanpa GCP

### Target (6 Weeks)
1. ✅ Modular - 15-20 file terpisah by concern
2. ✅ Redis caching - 70% cost reduction
3. ✅ Rate limiting - per user/endpoint
4. ✅ YAML prompts - easy tuning
5. ✅ PostgreSQL CRUD - seperti GCS
6. ✅ Hybrid mode - local + cloud

---

## 📂 New Structure (Overview)

```
├── main.py                    # Entry point (80 lines)
├── config/
│   ├── settings.py           # Config manager
│   └── prompts/              # ⭐ YAML prompt templates
│       ├── orchestrator.yaml
│       ├── router.yaml
│       ├── data_manipulator.yaml
│       ├── data_visualizer.yaml
│       ├── data_analyzer.yaml
│       └── response_compiler.yaml
├── src/
│   ├── app.py                # Flask factory
│   ├── middleware/           # ⭐ Cache, rate limit, auth
│   ├── routes/               # API blueprints (RESTful)
│   ├── services/             # Business logic
│   ├── storage/              # Storage abstraction
│   └── utils/                # Helpers
├── tests/
├── docker-compose.yml        # ⭐ Local dev (Postgres+Redis)
└── requirements.txt
```

---

## 🚀 Phase 1: Setup Infrastructure (Week 1)

### Step 1.1: Add Redis Support

**requirements.txt** (tambahkan):
```
redis==5.0.1
flask-caching==2.1.0
```

**docker-compose.yml** (buat baru):
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: convoinsight
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: convoinsight
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

**Run**:
```bash
docker-compose up -d
```

### Step 1.2: Create Config Structure

**config/settings.py**:
```python
import os

# Deployment mode
MODE = os.getenv("DEPLOYMENT_MODE", "cloud")  # local | cloud | hybrid

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = {
    "dataset_list": 60,
    "dataset_content": 300,
    "query_result": 300,
    "session_state": 1800,
}

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMITS = {
    "default": "100/hour",
    "query": "20/minute",
    "upload": "50/hour",
}

# Storage
STORAGE_MODE = MODE  # which backend to use
POSTGRES_URL = os.getenv("POSTGRES_URL") or os.getenv("LOCAL_POSTGRES_URL")

# Existing configs
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCS_BUCKET = os.getenv("GCS_BUCKET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FERNET_KEY = os.getenv("FERNET_KEY")
```

### Step 1.3: Create Middleware

**src/middleware/cache.py**:
```python
import redis
import json
import hashlib
from functools import wraps
from config.settings import REDIS_URL, CACHE_ENABLED

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.enabled = CACHE_ENABLED

    def get(self, key: str):
        if not self.enabled:
            return None
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, key: str, value, ttl: int = 300):
        if not self.enabled:
            return
        self.redis.setex(key, ttl, json.dumps(value, default=str))

    def delete(self, key: str):
        self.redis.delete(key)

    def invalidate_pattern(self, pattern: str):
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)

# Global instance
cache = CacheManager(REDIS_URL)

def cached(key_prefix: str, ttl: int = 300):
    """Decorator untuk cache function result"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            key_data = f"{args}:{kwargs}"
            cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute
            result = func(*args, **kwargs)

            # Cache
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

**src/middleware/rate_limiter.py**:
```python
import redis
import time
from flask import request, jsonify
from functools import wraps
from config.settings import REDIS_URL, RATE_LIMIT_ENABLED, RATE_LIMITS

class RateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.enabled = RATE_LIMIT_ENABLED

    def check_limit(self, key: str, limit: int, window: int) -> tuple[bool, dict]:
        if not self.enabled:
            return True, {}

        now = int(time.time())
        window_start = now - window

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {now: now})
        pipe.expire(key, window + 1)

        results = pipe.execute()
        count = results[1]

        return count < limit, {
            "limit": limit,
            "remaining": max(0, limit - count - 1),
            "reset": now + window
        }

# Global instance
rate_limiter = RateLimiter(REDIS_URL)

def rate_limit(limit_key: str = "default"):
    """Decorator untuk rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user identifier
            user_id = None
            if request.is_json:
                user_id = request.json.get("userId")
            identifier = user_id or request.remote_addr

            # Parse limit
            limit_str = RATE_LIMITS.get(limit_key, "100/hour")
            limit, period = limit_str.split("/")
            window = {"minute": 60, "hour": 3600}[period]

            # Check
            rate_key = f"ratelimit:{limit_key}:{identifier}"
            allowed, info = rate_limiter.check_limit(rate_key, int(limit), window)

            if not allowed:
                return jsonify({"error": "Rate limit exceeded", **info}), 429

            # Execute
            response = func(*args, **kwargs)

            # Add headers
            if isinstance(response, tuple):
                resp, status = response
            else:
                resp, status = response, 200

            if hasattr(resp, 'headers') and info:
                resp.headers['X-RateLimit-Limit'] = str(info['limit'])
                resp.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                resp.headers['X-RateLimit-Reset'] = str(info['reset'])

            return resp, status
        return wrapper
    return decorator
```

### Step 1.4: Test Middleware

**Test cache**:
```python
from src.middleware.cache import cache

# Set
cache.set("test", {"value": 123}, ttl=60)

# Get
result = cache.get("test")
print(result)  # {"value": 123}
```

**Test rate limiter** (tambahkan ke route):
```python
from src.middleware.rate_limiter import rate_limit

@app.route("/api/test")
@rate_limit("query")
def test():
    return jsonify({"ok": True})
```

---

## 🔧 Phase 2: Extract Prompts (Week 2)

### Step 2.1: Create Prompt Templates

**config/prompts/orchestrator.yaml**:
```yaml
name: orchestrator
version: "1.0.0"

system_prompt: |
  You are the Orchestrator for ConvoInsight.

  PRECEDENCE RULES:
  1. Direct user prompt (highest)
  2. Domain-specific config
  3. User-specific config
  4. System defaults (lowest)

  OUTPUT FORMAT:
  Return STRICT JSON with keys:
  - manipulator_prompt: string
  - visualizer_prompt: string
  - analyzer_prompt: string
  - compiler_instruction: string

user_prompt_template: |
  User Prompt: {user_prompt}
  Domain: {domain}

  Data Info: {data_info}
  Data Summary: {data_describe}
  Router Context: {router_context}
  Visualization Hint: {visual_hint}

parameters:
  model: "gemini/gemini-2.5-pro"
  temperature: 0.1
  seed: 1
  reasoning_effort: "high"
```

**config/prompts/data_manipulator.yaml**:
```yaml
name: data_manipulator
version: "1.0.0"

system_prompt: |
  You are the Data Manipulator agent.

  RESPONSIBILITIES:
  1. Enforce data hygiene
  2. Parse dates to Polars datetime
  3. Create period columns (day/week/month)
  4. Standardize dtypes
  5. Handle missing values
  6. Produce analysis-ready dataframe

  OUTPUT:
  result = {"type":"dataframe","value": <FINAL_DF>}

parameters:
  model: "gemini/gemini-2.5-pro"
  temperature: 0.0
  seed: 1
```

Buat file serupa untuk:
- `router.yaml`
- `data_visualizer.yaml`
- `data_analyzer.yaml`
- `response_compiler.yaml`

### Step 2.2: Create Prompt Manager

**src/services/prompt_manager.py**:
```python
import yaml
from pathlib import Path
from typing import Dict

class PromptManager:
    def __init__(self, prompts_dir: str = "config/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, dict] = {}

    def load(self, name: str) -> dict:
        """Load prompt config"""
        if name in self._cache:
            return self._cache[name]

        file = self.prompts_dir / f"{name}.yaml"
        if not file.exists():
            raise FileNotFoundError(f"Prompt not found: {name}")

        with open(file, 'r') as f:
            config = yaml.safe_load(f)

        self._cache[name] = config
        return config

    def get_system_prompt(self, name: str, domain_config: str = "", user_config: str = "") -> str:
        """Get system prompt with configs"""
        config = self.load(name)
        prompt = config["system_prompt"]

        if domain_config:
            prompt += f"\n\nDOMAIN CONFIG:\n{domain_config}"
        if user_config:
            prompt += f"\n\nUSER CONFIG:\n{user_config}"

        return prompt

    def render_user_prompt(self, name: str, **context) -> str:
        """Render user prompt template"""
        config = self.load(name)
        template = config.get("user_prompt_template", "")
        return template.format(**context)

    def get_params(self, name: str) -> dict:
        """Get LLM parameters"""
        config = self.load(name)
        return config.get("parameters", {})

# Global instance
prompts = PromptManager()
```

### Step 2.3: Update Orchestrator to Use Prompts

**Before** (di main.py):
```python
orchestrator_system_configuration = f"""1. You are the Orchestrator...
{data_manipulator_system_configuration}
{data_visualizer_system_configuration}
..."""
```

**After** (dengan PromptManager):
```python
from src.services.prompt_manager import prompts

# Load prompts
system_prompt = prompts.get_system_prompt(
    "orchestrator",
    domain_config=domain_specific_configuration,
    user_config=user_specific_configuration
)

user_content = prompts.render_user_prompt(
    "orchestrator",
    user_prompt=user_prompt,
    domain=domain,
    data_info=data_info,
    data_describe=data_describe,
    router_context=router_context,
    visual_hint=visual_hint
)

params = prompts.get_params("orchestrator")

# Call LLM
response = completion(
    model=params["model"],
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ],
    **{k: v for k, v in params.items() if k != "model"}
)
```

---

## 🗄️ Phase 3: PostgreSQL CRUD (Week 3)

### Step 3.1: Storage Abstraction

**src/storage/base.py**:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import polars as pl

class StorageBackend(ABC):
    @abstractmethod
    def list_items(self, prefix: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_item(self, key: str) -> pl.DataFrame:
        pass

    @abstractmethod
    def put_item(self, key: str, data: pl.DataFrame):
        pass

    @abstractmethod
    def delete_item(self, key: str):
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
```

### Step 3.2: PostgreSQL Implementation

**src/storage/postgres.py**:
```python
from typing import List, Dict, Any, Optional
import polars as pl
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool
from .base import StorageBackend

class PostgreSQLStorage(StorageBackend):
    def __init__(self, url: str):
        self.engine = create_engine(url, poolclass=NullPool)

    def list_items(self, prefix: str = "public") -> List[Dict[str, Any]]:
        """List tables in schema"""
        schema = prefix or "public"

        with self.engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names(schema=schema)

            items = []
            for table in tables:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table}"'))
                count = result.scalar()

                items.append({
                    "name": f"{schema}.{table}",
                    "type": "table",
                    "rows": count,
                })

            return items

    def get_item(self, key: str, limit: Optional[int] = None) -> pl.DataFrame:
        """Get table as DataFrame"""
        # Parse key: "schema.table" or "table"
        parts = key.split(".", 1)
        schema = parts[0] if len(parts) == 2 else "public"
        table = parts[1] if len(parts) == 2 else parts[0]

        query = f'SELECT * FROM "{schema}"."{table}"'
        if limit:
            query += f" LIMIT {limit}"

        with self.engine.connect() as conn:
            try:
                df = pl.read_database(query, conn)
            except:
                import pandas as pd
                df = pl.from_pandas(pd.read_sql(query, conn))

            return df

    def put_item(self, key: str, data: pl.DataFrame, if_exists: str = "replace"):
        """Create/replace table"""
        parts = key.split(".", 1)
        schema = parts[0] if len(parts) == 2 else "public"
        table = parts[1] if len(parts) == 2 else parts[0]

        pdf = data.to_pandas()
        with self.engine.connect() as conn:
            pdf.to_sql(table, conn, schema=schema, if_exists=if_exists, index=False)

    def delete_item(self, key: str):
        """Drop table"""
        parts = key.split(".", 1)
        schema = parts[0] if len(parts) == 2 else "public"
        table = parts[1] if len(parts) == 2 else parts[0]

        with self.engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE'))
            conn.commit()

    def exists(self, key: str) -> bool:
        """Check if table exists"""
        parts = key.split(".", 1)
        schema = parts[0] if len(parts) == 2 else "public"
        table = parts[1] if len(parts) == 2 else parts[0]

        with self.engine.connect() as conn:
            inspector = inspect(conn)
            return table in inspector.get_table_names(schema=schema)

    def execute_query(self, sql: str) -> pl.DataFrame:
        """Run arbitrary SQL"""
        with self.engine.connect() as conn:
            try:
                return pl.read_database(sql, conn)
            except:
                import pandas as pd
                return pl.from_pandas(pd.read_sql(sql, conn))
```

### Step 3.3: Add PostgreSQL Routes

**src/routes/postgres.py**:
```python
from flask import Blueprint, request, jsonify
from src.storage.postgres import PostgreSQLStorage
from src.middleware.rate_limiter import rate_limit
from src.middleware.cache import cached
from config.settings import POSTGRES_URL

postgres_bp = Blueprint('postgres', __name__, url_prefix='/postgres')

# Initialize storage
pg_storage = PostgreSQLStorage(POSTGRES_URL) if POSTGRES_URL else None

@postgres_bp.route('/tables', methods=['GET'])
@rate_limit("dataset_ops")
@cached("pg:tables", ttl=60)
def list_tables():
    """GET /api/v1/postgres/tables?schema=public"""
    schema = request.args.get('schema', 'public')
    items = pg_storage.list_items(schema)
    return jsonify(items)

@postgres_bp.route('/tables/<table>', methods=['GET'])
@rate_limit("dataset_ops")
def get_table(table):
    """GET /api/v1/postgres/tables/my_table?limit=100"""
    limit = request.args.get('limit', type=int)
    df = pg_storage.get_item(table, limit=limit)
    return jsonify(df.to_dicts())

@postgres_bp.route('/tables', methods=['POST'])
@rate_limit("upload")
def create_table():
    """POST /api/v1/postgres/tables
    Body: {"name": "my_table", "data": [...]}
    """
    body = request.json
    name = body.get('name')
    data = body.get('data')

    df = pl.DataFrame(data)
    pg_storage.put_item(name, df, if_exists='replace')

    return jsonify({"message": f"Table {name} created"}), 201

@postgres_bp.route('/tables/<table>', methods=['DELETE'])
@rate_limit("dataset_ops")
def delete_table(table):
    """DELETE /api/v1/postgres/tables/my_table"""
    pg_storage.delete_item(table)
    return jsonify({"message": f"Table {table} deleted"})

@postgres_bp.route('/query', methods=['POST'])
@rate_limit("query")
def execute_query():
    """POST /api/v1/postgres/query
    Body: {"sql": "SELECT ..."}
    """
    sql = request.json.get('sql')
    df = pg_storage.execute_query(sql)
    return jsonify(df.to_dicts())
```

---

## 📦 Phase 4: Modularize Main.py (Week 4)

### Step 4.1: Create Flask App Factory

**src/app.py**:
```python
from flask import Flask
from flask_cors import CORS
from config.settings import CORS_ORIGINS

def create_app():
    app = Flask(__name__)

    # CORS
    CORS(app, origins=CORS_ORIGINS, supports_credentials=True)

    # Register blueprints
    from src.routes import register_blueprints
    register_blueprints(app)

    # Error handlers
    from src.middleware.error_handler import register_error_handlers
    register_error_handlers(app)

    return app
```

### Step 4.2: Register Blueprints

**src/routes/__init__.py**:
```python
def register_blueprints(app):
    # Health
    from .health import health_bp
    app.register_blueprint(health_bp, url_prefix='/api/v1')

    # Datasets
    from .datasets import datasets_bp
    app.register_blueprint(datasets_bp, url_prefix='/api/v1')

    # Query
    from .query import query_bp
    app.register_blueprint(query_bp, url_prefix='/api/v1')

    # PostgreSQL
    from .postgres import postgres_bp
    app.register_blueprint(postgres_bp, url_prefix='/api/v1')

    # LLM
    from .llm import llm_bp
    app.register_blueprint(llm_bp, url_prefix='/api/v1')

    # Legacy routes (backward compatibility)
    from .legacy import legacy_bp
    app.register_blueprint(legacy_bp)
```

### Step 4.3: New Main.py

**main.py** (simplified):
```python
import os
from src.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
```

---

## 🧪 Testing

**tests/conftest.py**:
```python
import pytest
from src.app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()
```

**tests/test_cache.py**:
```python
from src.middleware.cache import cache

def test_cache_set_get():
    cache.set("test", {"val": 123}, ttl=10)
    result = cache.get("test")
    assert result == {"val": 123}
```

**tests/test_query.py**:
```python
def test_query_endpoint(client):
    response = client.post('/api/v1/queries', json={
        "domain": "test",
        "prompt": "Show data",
        "userId": "user123",
        "provider": "google",
        "model": "gemini-2.5-pro",
        "apiKey": "test_key"
    })

    assert response.status_code in [200, 400]
```

---

## 📊 Impact Metrics

### Performance
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Dataset list latency | 800ms | 50ms (cached) | 94% |
| Query repeat latency | 15s | 200ms (cached) | 98% |
| LLM API calls | 100% | 30% (70% cached) | 70% cost reduction |

### Code Quality
| Metric | Before | After |
|--------|--------|-------|
| Lines per file | 3,396 | 150-300 avg |
| Test coverage | 0% | 80%+ |
| Cyclomatic complexity | High | Low-Medium |

---

## 🔄 Migration Checklist

### Week 1: Infrastructure
- [ ] Add Redis to docker-compose
- [ ] Create config/settings.py
- [ ] Implement cache middleware
- [ ] Implement rate limiter middleware
- [ ] Test cache & rate limiter

### Week 2: Prompts
- [ ] Extract all prompts to YAML
- [ ] Create PromptManager
- [ ] Update orchestrator to use PromptManager
- [ ] Update all agents to use PromptManager
- [ ] Test prompt hot-reload

### Week 3: PostgreSQL
- [ ] Implement StorageBackend abstract class
- [ ] Implement PostgreSQLStorage
- [ ] Create postgres routes blueprint
- [ ] Test PostgreSQL CRUD
- [ ] Update query endpoint to support PG datasets

### Week 4: Modularization
- [ ] Create src/app.py factory
- [ ] Move routes to blueprints
- [ ] Extract services layer
- [ ] Simplify main.py
- [ ] Update imports

### Week 5: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Setup CI/CD
- [ ] Load testing

### Week 6: Documentation & Deploy
- [ ] API documentation (OpenAPI)
- [ ] Setup guide
- [ ] Deploy to staging
- [ ] Smoke tests
- [ ] Deploy to production

---

## 🚨 Quick Wins (dapat dilakukan sekarang)

### 1. Add Basic Caching (30 menit)
```bash
pip install redis flask-caching
```

```python
# Tambahkan di main.py
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

# Gunakan decorator
@app.route("/list-domains")
@cache.cached(timeout=60)
def list_domains():
    # ...
```

### 2. Extract 1 Prompt File (15 menit)
```bash
mkdir -p config/prompts
```

Buat `config/prompts/orchestrator.yaml` dan pindahkan orchestrator_system_configuration ke sana.

### 3. Add Rate Limiting (20 menit)
```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route("/query")
@limiter.limit("20 per minute")
def query():
    # ...
```

---

## 📞 Next Steps

1. **Review dokumen ini** dengan tim
2. **Setup local environment** (docker-compose)
3. **Mulai Phase 1** (infrastructure)
4. **Iterasi weekly** dengan testing

**Estimated Total Effort**: 6 weeks (1 engineer full-time)

---

END OF GUIDE
