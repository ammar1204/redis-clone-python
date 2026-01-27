# Educational Redis Clone

A learning-focused key-value store in Python. Demonstrates:
- Streaming RESP protocol parsing
- Asyncio concurrency (single-threaded)
- Key expiration (TTL)
- Basic persistence

## Commands

| Command | Description |
|---------|-------------|
| `PING` | Test connection → `PONG` |
| `SET key value` | Store a value → `OK` |
| `GET key` | Retrieve value → `"value"` or `(nil)` |
| `EXPIRE key seconds` | Set TTL → `1` or `0` |
| `TTL key` | Get remaining seconds → `n`, `-1` (no expiry), `-2` (missing) |
| `DEL key ...` | Delete keys → count deleted |
| `KEYS` | List all keys |

## Usage

```bash
python server.py
```

Then connect with `redis-cli`:
```
127.0.0.1:6379> SET name Alice
OK
127.0.0.1:6379> EXPIRE name 60
(integer) 1
127.0.0.1:6379> TTL name
(integer) 59
```

## Architectural Tradeoffs

This section documents the design decisions I made and why — the kind of reasoning expected in FAANG system design discussions.

### 1. Single-threaded Asyncio vs Multi-threading

**Choice:** Asyncio (single thread with event loop)

| Approach | Pros | Cons |
|----------|------|------|
| **Threading** | True parallelism on multi-core | GIL contention, need locks, race conditions |
| **Asyncio** | No locks needed, lower memory per connection | Can't use multiple cores, one slow handler blocks all |

**Why asyncio here:** Redis operations are CPU-light (dict lookups). The bottleneck is network I/O, not computation. A single thread can saturate network bandwidth while avoiding lock overhead. Real Redis uses this same model.

**When I'd use threading:** CPU-bound work like image processing or ML inference.

---

### 2. Lazy vs Active Expiration

**Choice:** Lazy expiration (delete keys when accessed)

| Approach | Pros | Cons |
|----------|------|------|
| **Lazy** | Zero CPU overhead until access, simple code | Memory grows with expired keys |
| **Active** | Bounded memory usage | Background thread complexity, CPU spikes |

**Why lazy here:** Simplicity. For learning, it's clearer to check expiration at read time.

**Production improvement:** Redis uses lazy + probabilistic active expiration — a background task randomly samples keys and deletes expired ones. This bounds memory without scanning everything.

---

### 3. JSON Persistence vs Write-Ahead Log (WAL)

**Choice:** Full JSON dump on shutdown

| Approach | Pros | Cons |
|----------|------|------|
| **JSON dump** | Simple, human-readable | Loses data on crash, slow for large datasets |
| **WAL/AOF** | Durable, append-only is fast | Complex recovery, file grows unbounded |
| **Snapshotting** | Point-in-time recovery | Periodic data loss window |

**Why JSON here:** Educational clarity. You can `cat dump.json` and see exactly what's stored.

**Production improvement:** Real Redis offers both RDB (periodic snapshots) and AOF (append-only log). AOF with `fsync` on every write gives durability at the cost of throughput.

---

### 4. In-Memory Dict vs LSM Tree / B-Tree

**Choice:** Python dict (hash table)

| Approach | Time Complexity | Use Case |
|----------|-----------------|----------|
| **Hash table** | O(1) get/set | Key-value, no range queries |
| **B-Tree** | O(log n) | Range queries, sorted iteration |
| **LSM Tree** | O(1) write, O(log n) read | Write-heavy workloads |

**Why hash table here:** Redis is a key-value store — O(1) access is the priority. We don't need sorted iteration or range queries for basic operations.

**When I'd use B-Tree:** Building a database index or filesystem.

---

### 5. No Connection Pooling

**Choice:** New parser per connection, no pooling

**Tradeoff:** Simple code vs potential memory pressure under high connection churn.

**Production improvement:** Limit max connections, reuse buffers, implement connection timeouts.

---

### Summary: What I'd Tell an Interviewer

> "I built this to understand the core mechanics of Redis. I chose asyncio because Redis is I/O-bound, not CPU-bound — a single thread avoids lock overhead while handling thousands of connections. I used lazy expiration for simplicity, knowing that production systems add probabilistic background cleanup. Persistence is a JSON dump because durability wasn't the learning goal, but I understand how WAL and fsync provide crash safety at the cost of write throughput."

## Files

- `server.py` - Complete server (~230 lines)
- `client.py` - Simple CLI client
- `dump.json` - Persisted data (created on shutdown)
