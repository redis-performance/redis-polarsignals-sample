from flask import Flask, jsonify
import redis
import os
import time

app = Flask(__name__)

# Redis connection
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))

try:
    r = redis.Redis(
        host=redis_host, port=redis_port, db=redis_db, decode_responses=True
    )
    # Test connection
    r.ping()
    print(f"Connected to Redis at {redis_host}:{redis_port}")
except redis.ConnectionError:
    print("Failed to connect to Redis")
    raise

FIBONACCI_KEY_PREFIX = "fib:"


def fibonacci_iterative(n: int, stats: dict = None):
    """
    Compute Fibonacci number iteratively with Redis caching

    Args:
        n: The Fibonacci number to compute
        stats: Dictionary to track cache hits/misses (optional)

    Returns:
        The nth Fibonacci number
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")

    if n <= 1:
        return n

    # Check if final result is already cached
    final_cache_key = f"{FIBONACCI_KEY_PREFIX}{n}"
    cached_value = r.get(final_cache_key)
    if cached_value is not None:
        if stats is not None:
            stats['hits'] += 1
        return int(cached_value)

    # Find the highest cached value we can start from
    start_index = 2
    a, b = 0, 1  # F(0) = 0, F(1) = 1

    # Look for cached intermediate values, starting from the target and working backwards
    for i in range(n, 1, -1):
        cache_key = f"{FIBONACCI_KEY_PREFIX}{i}"
        cached_val = r.get(cache_key)
        if cached_val is not None:
            if stats is not None:
                stats['hits'] += 1
            # Found a cached value, now we need the previous one too
            prev_cache_key = f"{FIBONACCI_KEY_PREFIX}{i-1}"
            prev_cached_val = r.get(prev_cache_key)
            if prev_cached_val is not None:
                if stats is not None:
                    stats['hits'] += 1
                # Start from this point
                start_index = i + 1
                a, b = int(prev_cached_val), int(cached_val)
                break
            else:
                if stats is not None:
                    stats['misses'] += 1

    # Compute iteratively from start_index to n
    for i in range(start_index, n + 1):
        cache_key = f"{FIBONACCI_KEY_PREFIX}{i}"

        # Check if this intermediate value is already cached
        cached_val = r.get(cache_key)
        if cached_val is not None:
            if stats is not None:
                stats['hits'] += 1
            a, b = b, int(cached_val)
        else:
            # Compute and cache this value
            if stats is not None:
                stats['misses'] += 1
            next_fib = a + b
            r.setex(cache_key, 3600, next_fib)  # Cache for 1 hour
            a, b = b, next_fib

    return b


@app.route("/fibonacci/<int:n>", methods=["GET"])
def get_fibonacci(n: int):
    """Get the nth Fibonacci number"""
    if n < 0:
        return jsonify({"error": "Fibonacci is not defined for negative numbers"}), 400

    if n > 100000:  # Reasonable limit for very large numbers
        return jsonify({"error": "Number too large (max 100,000)"}), 400

    try:
        # Initialize cache statistics
        stats = {'hits': 0, 'misses': 0}

        start_time = time.time()
        result = fibonacci_iterative(n, stats)
        computation_time = time.time() - start_time

        # Calculate miss rate
        total_operations = stats['hits'] + stats['misses']
        miss_rate = (stats['misses'] / total_operations * 100) if total_operations > 0 else 0

        return jsonify(
            {
                "n": n,
                "fibonacci": result,
                "computation_time_ms": round(computation_time * 1000, 2),
                "stats": {
                    "cache_hits": stats['hits'],
                    "cache_misses": stats['misses'],
                    "cache_miss_rate_percent": round(miss_rate, 2)
                }
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/fibonacci/cache", methods=["DELETE"])
def clear_fibonacci_cache():
    """Clear all Fibonacci cache entries"""
    # Find all fibonacci cache keys
    keys = r.keys(f"{FIBONACCI_KEY_PREFIX}*")
    if keys:
        deleted_count = r.delete(*keys)
        return jsonify({"message": f"Cleared {deleted_count} cache entries"})
    else:
        return jsonify({"message": "No cache entries found"})


@app.route("/fibonacci/cache", methods=["GET"])
def get_cache_stats():
    """Get cache statistics"""
    keys = r.keys(f"{FIBONACCI_KEY_PREFIX}*")
    cache_entries = []

    for key in keys:
        value = r.get(key)
        ttl = r.ttl(key)
        n = int(key.replace(FIBONACCI_KEY_PREFIX, ""))
        cache_entries.append(
            {
                "n": n,
                "fibonacci": int(value) if value else None,
                "ttl_seconds": ttl if ttl > 0 else None,
            }
        )

    # Sort by n value
    cache_entries.sort(key=lambda x: x["n"])

    return jsonify(
        {"total_cached_entries": len(cache_entries), "entries": cache_entries}
    )


@app.route("/", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "message": "Flask + Redis Fibonacci API"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
