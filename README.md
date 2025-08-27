# Redis Fibonacci API

A Flask application with Redis that computes Fibonacci numbers using iterative algorithm with intelligent caching.

## Prerequisites

- Python 3.12+
- Redis server running (default: localhost:6379)

## Running the Application

### Option 1: Using Docker Compose (Recommended)

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Polar Signals token (optional):
```bash
POLAR_SIGNALS_TOKEN=your_actual_token_here
```

3. Run with Docker Compose:
```bash
docker-compose up --build
```

This will start Redis, the Flask app, and Parca agent for continuous profiling. The application will be available at `http://localhost:5000`

### Option 2: Local Development

1. Make sure Redis is running on your system
2. Install dependencies and activate the virtual environment:
```bash
poetry install
poetry shell
```
3. Run the Flask app:
```bash
python app.py
```

The application will start on `http://localhost:5000`

## API Endpoints

### GET /fibonacci/{n}
Computes the nth Fibonacci number using iterative algorithm with Redis caching.

**Limits:** n must be between 0 and 100,000 (supports very large Fibonacci numbers).

**Response:**
```json
{
  "n": 10,
  "fibonacci": 55,
  "computation_time_ms": 0.15,
  "stats": {
    "cache_hits": 8,
    "cache_misses": 2,
    "cache_miss_rate_percent": 20.0
  }
}
```

### GET /fibonacci/cache
Returns statistics about cached Fibonacci values.

**Response:**
```json
{
  "total_cached_entries": 3,
  "entries": [
    {
      "n": 10,
      "fibonacci": 55,
      "ttl_seconds": 3542
    }
  ]
}
```

### DELETE /fibonacci/cache
Clears all cached Fibonacci values.

**Response:**
```json
{
  "message": "Cleared 5 cache entries"
}
```

### GET /
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "Flask + Redis Fibonacci API"
}
```

## Environment Variables

- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)
- `POLAR_SIGNALS_TOKEN`: Bearer token for Polar Signals continuous profiling (optional)

## Example Usage

```bash
# Compute Fibonacci number
curl http://localhost:5000/fibonacci/10

# Compute larger Fibonacci number
curl http://localhost:5000/fibonacci/35

# Get cache statistics
curl http://localhost:5000/fibonacci/cache

# Clear cache
curl -X DELETE http://localhost:5000/fibonacci/cache

# Health check
curl http://localhost:5000/
```

## How Caching Works

1. **Iterative Algorithm**: Uses iterative Fibonacci implementation (no recursion depth limits)
2. **Smart Cache Lookup**: Searches for the highest cached intermediate value to start computation from
3. **Redis Caching**: Each computed value is automatically cached in Redis with 1-hour TTL
4. **Cache Benefits**: Computation starts from the highest cached value, not from F(0)
5. **Performance**: Very large Fibonacci numbers (e.g., F(100000)) are computed efficiently
6. **Automatic Optimization**: Computing F(1000) caches all intermediate values (F(2), F(3), ..., F(999))
7. **Cache Statistics**: Each request reports:
   - `cache_hits`: Number of values found in cache
   - `cache_misses`: Number of values computed and stored
   - `cache_miss_rate_percent`: Percentage of cache misses (lower is better)

## Continuous Profiling

The application includes Parca agent for continuous profiling with Polar Signals:

- **CPU Profiling**: Samples at 19Hz to capture performance characteristics
- **Memory Profiling**: Tracks memory allocation patterns
- **Performance Insights**: Identify bottlenecks in Fibonacci computation and caching
- **Production Ready**: Low overhead profiling suitable for production environments

To enable profiling, set the `POLAR_SIGNALS_TOKEN` environment variable with your Polar Signals API token.
