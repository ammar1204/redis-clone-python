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

## Key Concepts

### 1. Streaming RESP Parser
TCP is a byte stream - data arrives in chunks. The parser maintains a buffer per connection and only parses when complete messages are available.

### 2. Asyncio vs Threading
- Single thread with event loop
- Cooperative multitasking at `await` points
- No locks needed for shared state
- Lower overhead than threads

### 3. Lazy Expiration
Keys are deleted when accessed, not proactively. Simple but uses more memory.

### 4. Persistence
JSON saved on shutdown, loaded on startup. Not durable - crashes lose data.

## Files

- `server.py` - Complete server (~320 lines with comments)
- `client.py` - Simple CLI client
- `dump.json` - Persisted data (created on shutdown)
