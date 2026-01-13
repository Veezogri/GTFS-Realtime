# GTFS-RT Analytics

A professional-grade real-time transit data analytics platform that ingests GTFS-Realtime feeds, stores raw and normalized data, and provides statistical insights through a REST API and web dashboard.

## Overview

This system provides:

- **Real-time data ingestion** from GTFS-RT feeds (live HTTP polling or offline file reading)
- **Dual-layer storage** with raw protobuf archives and normalized relational tables
- **Statistical API** for delay analysis with time-series and aggregation endpoints
- **Web dashboard** with interactive charts and filtering capabilities
- **Complete containerization** via Docker Compose for easy deployment

## Architecture

```
┌─────────────────┐
│   Frontend      │  React + Vite + Recharts
│   (Port 3000)   │  Dashboard with filters and charts
└────────┬────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│   Backend       │  FastAPI
│   (Port 8000)   │  REST API with statistics endpoints
└────────┬────────┘
         │
         │ SQL
         ▼
┌─────────────────┐
│   PostgreSQL    │  Raw feeds + normalized events
│   (Port 5432)   │  rt_feed_raw, trip_update_events, vehicle_positions
└─────────────────┘
         ▲
         │
┌────────┴────────┐
│   Ingestion     │  Python worker
│   Worker        │  Fetches, parses, stores GTFS-RT data
└─────────────────┘
```

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 5GB disk space recommended

## Quick Start

1. **Clone and configure**

```bash
cd GTFS-Realtime
cp .env.example .env
```

2. **Edit `.env` file**

For offline mode (recommended for testing):
```env
INGESTION_MODE=offline
GTFS_RT_FILE_PATH=/app/samples/tripupdates.pb
FEED_TYPE=trip_updates
SOURCE_ID=my_agency
POLL_INTERVAL=60
```

For live mode:
```env
INGESTION_MODE=live
GTFS_RT_URL=https://your-transit-agency.com/gtfs-rt/trip-updates
FEED_TYPE=trip_updates
SOURCE_ID=your_agency
POLL_INTERVAL=60
```

3. **Add sample data (offline mode only)**

Place a GTFS-Realtime protobuf file in the `samples/` directory:
```bash
mkdir -p samples
# Copy your .pb file to samples/tripupdates.pb
```

4. **Launch the application**

```bash
docker compose up --build
```

5. **Access the services**

- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Project Structure

```
GTFS-Realtime/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main.py          # Application entry point
│   │   ├── config.py        # Settings management
│   │   ├── db.py            # Database session management
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── logger.py        # Structured logging setup
│   │   ├── routers/         # API route handlers
│   │   │   ├── health.py    # Health check endpoint
│   │   │   └── stats.py     # Statistics endpoints
│   │   └── services/        # Business logic
│   │       └── stats_service.py
│   ├── alembic/             # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── tests/               # Backend tests
│   │   └── test_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
│
├── ingestion/               # Data ingestion worker
│   ├── worker.py            # Main worker loop
│   ├── parser.py            # GTFS-RT protobuf parser
│   ├── config.py            # Worker configuration
│   ├── logger.py            # Logging setup
│   ├── tests/               # Ingestion tests
│   │   └── test_parser.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                # React dashboard
│   ├── src/
│   │   ├── main.jsx         # React entry point
│   │   ├── App.jsx          # Main application component
│   │   └── components/      # Dashboard components
│   │       ├── Dashboard.jsx
│   │       ├── DateRangeFilter.jsx
│   │       ├── KpiCards.jsx
│   │       ├── TopStops.jsx
│   │       └── TimeSeriesChart.jsx
│   ├── Dockerfile
│   ├── nginx.conf           # Production web server config
│   ├── package.json
│   └── vite.config.js
│
├── samples/                 # Sample GTFS-RT files (offline mode)
│   └── .gitkeep
│
├── docker-compose.yml       # Container orchestration
├── .env.example             # Environment variables template
└── README.md
```

## Database Schema

### `rt_feed_raw`
Stores raw GTFS-RT feed data with metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger | Primary key |
| fetched_at | Timestamp (UTC) | When the feed was fetched |
| feed_type | String(50) | trip_updates, vehicle_positions, or service_alerts |
| source | String(100) | Source identifier (configured in .env) |
| payload | LargeBinary | Raw protobuf bytes |
| http_status | Integer | HTTP status code (live mode only) |
| error | Text | Error message if fetch failed |

**Indexes:** fetched_at, feed_type, source, (fetched_at, source)

### `trip_update_events`
Normalized trip update data with stop-level granularity.

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger | Primary key |
| fetched_at | Timestamp (UTC) | Feed fetch time |
| trip_id | String(255) | GTFS trip identifier |
| route_id | String(255) | GTFS route identifier (optional) |
| direction_id | Integer | Trip direction (0 or 1) |
| stop_id | String(255) | GTFS stop identifier |
| stop_sequence | Integer | Stop sequence in trip |
| arrival_delay | Integer | Arrival delay in seconds (negative = early) |
| departure_delay | Integer | Departure delay in seconds |
| arrival_time | Timestamp (UTC) | Predicted/actual arrival time |
| departure_time | Timestamp (UTC) | Predicted/actual departure time |

**Indexes:** fetched_at, trip_id, route_id, stop_id, (fetched_at, route_id), (fetched_at, stop_id), (trip_id, stop_id)

### `vehicle_positions`
Real-time vehicle location and movement data.

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger | Primary key |
| fetched_at | Timestamp (UTC) | Feed fetch time |
| vehicle_id | String(255) | Vehicle identifier |
| trip_id | String(255) | Associated trip (optional) |
| latitude | Float | WGS84 latitude |
| longitude | Float | WGS84 longitude |
| bearing | Float | Compass bearing in degrees (optional) |
| speed | Float | Speed in meters/second (optional) |

**Indexes:** fetched_at, vehicle_id, trip_id, (fetched_at, vehicle_id)

## API Endpoints

### Health

**GET** `/health`

Returns system health status and database connectivity.

```json
{
  "status": "healthy",
  "timestamp": "2026-01-13T10:30:00Z",
  "database": "connected"
}
```

### Statistics

All statistics endpoints use **arrival_delay** as the primary metric (delay in seconds; negative values indicate early arrivals).

**GET** `/stats/delays/summary`

Summary statistics for a time range.

Query parameters:
- `from` (required): Start datetime (ISO 8601, UTC)
- `to` (required): End datetime (ISO 8601, UTC)
- `route_id` (optional): Filter by route

Response:
```json
{
  "mean_delay": 120.5,
  "median_delay": 95.0,
  "p95_delay": 380.0,
  "sample_count": 15234,
  "from_date": "2026-01-12T10:00:00Z",
  "to_date": "2026-01-13T10:00:00Z",
  "route_id": null
}
```

**GET** `/stats/delays/by-route`

Delay statistics grouped by route.

Query parameters:
- `from`, `to` (required)

Response:
```json
{
  "routes": [
    {
      "route_id": "Route_1",
      "mean_delay": 145.2,
      "median_delay": 120.0,
      "p95_delay": 420.0,
      "sample_count": 5432
    }
  ],
  "from_date": "...",
  "to_date": "..."
}
```

**GET** `/stats/delays/by-stop`

Top delayed stops, ordered by mean delay descending.

Query parameters:
- `from`, `to` (required)
- `limit` (optional, default 10, max 100)

Response:
```json
{
  "stops": [
    {
      "stop_id": "STOP_456",
      "mean_delay": 230.5,
      "median_delay": 180.0,
      "p95_delay": 600.0,
      "sample_count": 823
    }
  ],
  "limit": 10,
  "from_date": "...",
  "to_date": "..."
}
```

**GET** `/stats/timeseries/delay`

Time-series delay data with configurable bucketing.

Query parameters:
- `from`, `to` (required)
- `route_id` (optional)
- `bucket` (optional, default "15m"): 5m, 15m, 30m, 1h, 6h, 1d

Response:
```json
{
  "timeseries": [
    {
      "timestamp": "2026-01-13T10:00:00Z",
      "mean_delay": 125.3,
      "median_delay": 105.0,
      "sample_count": 342
    }
  ],
  "bucket": "15m",
  "route_id": null,
  "from_date": "...",
  "to_date": "..."
}
```

## Example API Requests

```bash
# Health check
curl http://localhost:8000/health

# Get delay summary for last 24 hours
curl "http://localhost:8000/stats/delays/summary?from=2026-01-12T10:00:00Z&to=2026-01-13T10:00:00Z"

# Get delays by route
curl "http://localhost:8000/stats/delays/by-route?from=2026-01-12T00:00:00Z&to=2026-01-13T00:00:00Z"

# Get top 5 delayed stops
curl "http://localhost:8000/stats/delays/by-stop?from=2026-01-12T00:00:00Z&to=2026-01-13T00:00:00Z&limit=5"

# Get hourly time-series for a specific route
curl "http://localhost:8000/stats/timeseries/delay?from=2026-01-12T00:00:00Z&to=2026-01-13T00:00:00Z&route_id=Route_1&bucket=1h"
```

## Testing

### Run backend tests
```bash
cd backend
docker build -t gtfs-backend-test .
docker run gtfs-backend-test pytest
```

### Run ingestion tests
```bash
cd ingestion
docker build -t gtfs-ingestion-test .
docker run gtfs-ingestion-test pytest
```

## Configuration

All configuration is managed via environment variables (see `.env.example`).

### Key Settings

**Database:**
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

**Ingestion:**
- `INGESTION_MODE`: `live` or `offline`
- `GTFS_RT_URL`: HTTP endpoint for live feeds
- `GTFS_RT_FILE_PATH`: Path to protobuf file for offline mode
- `FEED_TYPE`: `trip_updates`, `vehicle_positions`, or `service_alerts`
- `SOURCE_ID`: Identifier for the data source (stored in `rt_feed_raw.source`)
- `POLL_INTERVAL`: Seconds between feed fetches (default 60)

**Logging:**
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_FORMAT`: `json` or `text`

## Obtaining GTFS-RT Sample Data

For offline mode, you need a GTFS-Realtime protobuf file:

1. Find a transit agency with public GTFS-RT feeds (e.g., MTA, BART, LA Metro)
2. Download a feed snapshot:
```bash
curl -o samples/tripupdates.pb https://example-agency.com/gtfs-rt/trip-updates
```
3. Ensure `.env` points to the file:
```env
GTFS_RT_FILE_PATH=/app/samples/tripupdates.pb
```

## Technical Decisions

### Time Handling
- All timestamps stored in UTC (PostgreSQL `TIMESTAMP WITH TIME ZONE`)
- API expects and returns ISO 8601 formatted UTC timestamps
- Frontend converts to local timezone for display

### Delay Metrics
- Primary metric: **arrival_delay** (seconds)
- Positive values = late, negative = early, null = no prediction
- Statistics calculated on non-null values only

### Database Design
- Raw storage (`rt_feed_raw`) preserves complete feed history for auditing
- Normalized tables optimize query performance for analytics
- Indexes designed for common query patterns (time ranges, route/stop filters)

### Ingestion Resilience
- Worker continues on parse failures (logs error, stores raw feed with error message)
- Database connection retries with exponential backoff
- HTTP errors in live mode stored but don't crash worker

### API Performance
- Connection pooling (10 base connections, 20 max overflow)
- Efficient SQL with aggregations pushed to database
- Date_bin used for time-series bucketing (PostgreSQL 14+ required)



## Troubleshooting

### Services won't start
```bash
docker compose down -v
docker compose up --build
```

### No data in dashboard
1. Check ingestion worker logs: `docker compose logs ingestion`
2. Verify sample file exists: `ls -l samples/`
3. Check database: `docker compose exec postgres psql -U gtfsuser -d gtfs_rt_analytics -c "SELECT COUNT(*) FROM rt_feed_raw;"`

### Database connection errors
- Ensure PostgreSQL is healthy: `docker compose ps postgres`
- Check credentials in `.env` match `docker-compose.yml`

### API returning 422 errors
- Verify date format (ISO 8601): `2026-01-13T10:00:00Z`
- Ensure `from` < `to`
- Check bucket parameter is valid: 5m, 15m, 30m, 1h, 6h, 1d

## License

This is a demonstration project. Use at your own discretion.

## Author

**RIAL Fares**

