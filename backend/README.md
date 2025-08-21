# Fulfil → ShipHero Mediator

A Python service that polls Fulfil products and syncs them to ShipHero, while maintaining a local Postgres record for auditing and idempotency.

## Features

- Polling-based delta sync using Fulfil `write_date`
- ShipHero GraphQL upserts (create/update) with unit conversion
- Idempotent pushes via payload hashing
- APScheduler for periodic jobs
- Flask health endpoint
- Postgres persistence with SQLAlchemy + Alembic
- Dockerized dev stack
- **NEW**: Automatic ShipHero token refresh with OAuth
- **NEW**: Retry logic with exponential backoff
- **NEW**: Enhanced error handling and logging
- **NEW**: On-demand product sync capability

## Quick Start

### 1) Prereqs

- Docker & Docker Compose (or Podman equivalents)
- Fulfil API credentials
- ShipHero OAuth credentials (client ID, client secret, refresh token)

### 2) Configure

Copy `.env.example` → `.env` and fill values:

```bash
# Required: Fulfil credentials
FULFIL_SUBDOMAIN=your-subdomain
FULFIL_API_KEY=your-api-key

# Required: ShipHero OAuth credentials
SHIPHERO_REFRESH_TOKEN=your-refresh-token

# Optional: Initial access token (will be auto-refreshed)
SHIPHERO_ACCESS_TOKEN=your-initial-access-token
SHIPHERO_TOKEN_EXPIRES_IN=3600

# Optional: ShipHero API configuration (defaults to production)
SHIPHERO_API_BASE_URL=https://public-api.shiphero.com
SHIPHERO_OAUTH_URL=https://public-api.shiphero.com/oauth

# Database
DATABASE_URL=postgresql://user:pass@localhost/fulfil_shiphero

# Sync settings
POLL_INTERVAL_MINUTES=5
```

### 3) Initialize Database and Tokens

```bash
# Initialize database tables and ShipHero tokens
python init_tokens.py
```

### 4) Run (Docker)

```bash
docker compose up --build
```

App starts on `http://localhost:8000`.

### 5) Initialize DB (Alembic)

In a new shell:

```bash
docker compose exec app alembic upgrade head
```

### 6) Health Check

```bash
curl http://localhost:8000/health
```

### 7) Scheduler Status

The service automatically starts a background scheduler that runs delta sync operations every `POLL_INTERVAL_MINUTES` (default: 5 minutes). The scheduler will:

- Automatically sync products from Fulfil to ShipHero
- Handle errors gracefully and log them
- Ensure only one sync job runs at a time
- Combine missed runs if the service is temporarily unavailable
- **NEW**: Automatically refresh ShipHero access tokens before expiration
- **NEW**: Retry failed API calls with exponential backoff

## Local Dev (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Initialize database and tokens
python init_tokens.py

# Run migrations
alembic upgrade head

# Start the service
FLASK_APP=mediator.app:app flask run --port 8000
```

## Advanced Features

### On-Demand Product Sync

You can trigger immediate sync of a specific product:

```python
from mediator.sync_logic import SyncService

# This will fetch the product from Fulfil and sync to ShipHero immediately
product = sync_service.fetch_and_sync_product("SKU123")
```

### Enhanced Error Handling

The service now includes:

- **Automatic retry**: Failed API calls are retried with exponential backoff
- **Token refresh**: ShipHero access tokens are automatically refreshed before expiration
- **SKU exists handling**: Better error handling when products already exist in ShipHero
- **Comprehensive logging**: Detailed logs for debugging and monitoring

### Configuration Options

Additional environment variables for fine-tuning:

```bash
# Retry settings
MAX_RETRIES=3
RETRY_BASE_DELAY=1.0

# Sync settings
BATCH_SIZE=100
SYNC_TIMEOUT=300
```

## Migrations

- Autogenerate after model changes:

```bash
alembic revision --autogenerate -m "changes"
alembic upgrade head
```

## Notes

- Units stored in DB as SI (kg/cm). Converted to lb/in for ShipHero payload.
- `sync_run`/`sync_error` tables provide auditability.
- If ShipHero `product_create` reports SKU exists, we fallback to `product_update`.
- The scheduler runs automatically in the background and doesn't require manual intervention.
- **NEW**: ShipHero tokens are now stored in the database and automatically refreshed.
- **NEW**: The service includes comprehensive retry logic for improved reliability.
