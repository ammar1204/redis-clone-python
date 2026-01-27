"""
Educational Redis Clone - Streaming RESP, Asyncio, TTL, Persistence
Commands: PING, SET, GET, EXPIRE, TTL, DEL, KEYS
"""

import asyncio
import json
import os
import time

data = {}
PERSISTENCE_FILE = "dump.json"


# Streaming RESP Parser
# TCP is a byte stream, not messages. We buffer until we have complete data.
class RESPParser:
    def __init__(self):
        self.buffer = b""
    
    def feed(self, data: bytes):
        self.buffer += data
    
    def get_command(self):
        if not self.buffer:
            return None
        if self.buffer[0:1] == b"*":
            return self._parse_array()
        return self._parse_inline()
    
    def _parse_array(self):
        end = self.buffer.find(b"\r\n")
        if end == -1:
            return None
        
        try:
            count = int(self.buffer[1:end])
        except ValueError:
            self.buffer = self.buffer[1:]
            return None
        
        pos = end + 2
        args = []
        
        for _ in range(count):
            result = self._parse_bulk_string_at(pos)
            if result is None:
                return None
            value, new_pos = result
            args.append(value)
            pos = new_pos
        
        self.buffer = self.buffer[pos:]
        return args
    
    def _parse_bulk_string_at(self, start):
        if start >= len(self.buffer) or self.buffer[start:start+1] != b"$":
            return None
        
        end = self.buffer.find(b"\r\n", start)
        if end == -1:
            return None
        
        try:
            length = int(self.buffer[start+1:end])
        except ValueError:
            return None
        
        data_start = end + 2
        data_end = data_start + length
        
        if len(self.buffer) < data_end + 2:
            return None
        
        return (self.buffer[data_start:data_end].decode(), data_end + 2)
    
    def _parse_inline(self):
        end = self.buffer.find(b"\r\n")
        if end == -1:
            return None
        line = self.buffer[:end].decode()
        self.buffer = self.buffer[end+2:]
        return line.split()


# RESP responses
def simple_string(msg):
    return f"+{msg}\r\n".encode()

def error(msg):
    return f"-{msg}\r\n".encode()

def bulk_string(val):
    if val is None:
        return b"$-1\r\n"
    return f"${len(val)}\r\n{val}\r\n".encode()

def integer(val):
    return f":{val}\r\n".encode()


# Key expiration (lazy deletion - keys deleted when accessed)
def is_expired(key):
    if key not in data:
        return True
    value, expires_at = data[key]
    if expires_at and time.time() > expires_at:
        del data[key]
        return True
    return False

def get_value(key):
    if is_expired(key):
        return None
    return data[key][0]

def set_value(key, value, expires_at=None):
    data[key] = (value, expires_at)


# Command handlers
def handle_command(args):
    if not args:
        return error("ERR empty command")
    
    cmd = args[0].upper()
    
    if cmd == "PING":
        return simple_string("PONG")
    
    elif cmd == "SET":
        if len(args) < 3:
            return error("ERR wrong number of arguments for 'SET'")
        set_value(args[1], args[2])
        return simple_string("OK")
    
    elif cmd == "GET":
        if len(args) < 2:
            return error("ERR wrong number of arguments for 'GET'")
        return bulk_string(get_value(args[1]))
    
    elif cmd == "EXPIRE":
        if len(args) < 3:
            return error("ERR wrong number of arguments for 'EXPIRE'")
        try:
            seconds = int(args[2])
        except ValueError:
            return error("ERR value is not an integer")
        
        key = args[1]
        if key not in data or is_expired(key):
            return integer(0)
        
        value, _ = data[key]
        data[key] = (value, time.time() + seconds)
        return integer(1)
    
    elif cmd == "TTL":
        if len(args) < 2:
            return error("ERR wrong number of arguments for 'TTL'")
        key = args[1]
        
        if key not in data:
            return integer(-2)
        
        value, expires_at = data[key]
        if expires_at is None:
            return integer(-1)
        
        remaining = int(expires_at - time.time())
        if remaining < 0:
            del data[key]
            return integer(-2)
        return integer(remaining)
    
    elif cmd == "DEL":
        if len(args) < 2:
            return error("ERR wrong number of arguments for 'DEL'")
        count = sum(1 for k in args[1:] if k in data and not data.pop(k, None) is None or k in data and data.pop(k))
        count = 0
        for key in args[1:]:
            if key in data:
                del data[key]
                count += 1
        return integer(count)
    
    elif cmd == "KEYS":
        keys = [k for k in data.keys() if not is_expired(k)]
        result = f"*{len(keys)}\r\n"
        for k in keys:
            result += f"${len(k)}\r\n{k}\r\n"
        return result.encode()
    
    else:
        return error(f"ERR unknown command '{cmd}'")


# Asyncio server (single-threaded, non-blocking, no locks needed)
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"connected: {addr}")
    
    parser = RESPParser()
    
    try:
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                break
            
            parser.feed(chunk)
            
            while True:
                command = parser.get_command()
                if command is None:
                    break
                writer.write(handle_command(command))
                await writer.drain()
    except ConnectionResetError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"disconnected: {addr}")


# Persistence (JSON file, saved on shutdown, loaded on startup)
def save_data():
    to_save = {}
    for key, (value, expires_at) in data.items():
        if expires_at and time.time() > expires_at:
            continue
        to_save[key] = {"value": value, "expires_at": expires_at}
    
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(to_save, f)
    print(f"saved {len(to_save)} keys")

def load_data():
    if not os.path.exists(PERSISTENCE_FILE):
        return
    
    with open(PERSISTENCE_FILE, "r") as f:
        saved = json.load(f)
    
    now = time.time()
    for key, entry in saved.items():
        expires_at = entry.get("expires_at")
        if expires_at and now > expires_at:
            continue
        data[key] = (entry["value"], expires_at)
    
    print(f"loaded {len(data)} keys")


async def main():
    load_data()
    
    server = await asyncio.start_server(handle_client, "127.0.0.1", 6379)
    print("redis clone running on 127.0.0.1:6379")
    print("commands: PING, SET, GET, EXPIRE, TTL, DEL, KEYS")
    
    try:
        async with server:
            await server.serve_forever()
    finally:
        save_data()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nshutting down")
        save_data()
