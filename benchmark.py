import socket
import time
from concurrent.futures import ThreadPoolExecutor

HOST = '127.0.0.1'  # your Python Redis clone host
PORT = 6379          # your Python Redis clone port
REQUESTS = 1000      # total requests per command
CONCURRENCY = 50     # concurrent clients

def send_command(cmd_bytes):
    """Connect, send command, receive response, close."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(cmd_bytes)
            s.recv(1024)
    except Exception as e:
        print("Error:", e)

def run_benchmark(name, cmd_bytes):
    start = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        for _ in range(REQUESTS):
            executor.submit(send_command, cmd_bytes)
    end = time.time()
    elapsed = end - start
    print(f"{name}: {REQUESTS} requests in {elapsed:.2f}s ({REQUESTS/elapsed:.2f} req/sec)")

if __name__ == "__main__":
    # PING
    ping_cmd = b'*1\r\n$4\r\nPING\r\n'
    run_benchmark("PING", ping_cmd)

    # SET key value
    set_cmd = b'*3\r\n$3\r\nSET\r\n$1\r\na\r\n$2\r\n10\r\n'
    run_benchmark("SET", set_cmd)

    # GET key
    get_cmd = b'*2\r\n$3\r\nGET\r\n$1\r\na\r\n'
    run_benchmark("GET", get_cmd)
