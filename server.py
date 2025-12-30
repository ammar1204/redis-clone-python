import socket
import threading

DATA_STORE = {}

def parse_resp(conn):
    data = conn.recv(1024)
    if not data:
        return None

    parts = data.split(b"\r\n")

    if parts[0].startswith(b"*"):  
        arg_count = int(parts[0][1:])
        args = []
        idx = 1

        for _ in range(arg_count):
            if parts[idx].startswith(b"$"):
                length = int(parts[idx][1:])
                idx += 1
                args.append(parts[idx].decode())
                idx += 1
        return args

    return data.decode().strip().split()


# RESP Respond helpers
def send_simple_string(conn, msg):
    conn.sendall(b"+" + msg.encode() + b"\r\n")

def send_bulk_string(conn, msg):
    if msg is None:
        conn.sendall(b"$-1\r\n")
    else:
        encoded = msg.encode()
        conn.sendall(
            b"$" + str(len(encoded)).encode() + b"\r\n" + encoded + b"\r\n"
        )

def send_error(conn, msg):
    conn.sendall(b"-" + msg.encode() + b"\r\n")


def handle_client(conn, addr):
    print("Client connected:", addr)
    while True:
        args = parse_resp(conn)
        if not args:
            break

        command = args[0].upper()

        if command == "PING":
            send_simple_string(conn, "PONG")

        elif command == "ECHO" and len(args) > 1:
            send_bulk_string(conn, " ".join(args[1:]))

        elif command == "SET" and len(args) > 2:
            DATA_STORE[args[1]] = args[2]
            send_simple_string(conn, "OK")

        elif command == "GET" and len(args) > 1:
            value = DATA_STORE.get(args[1])
            send_bulk_string(conn, value)

        else:
            send_error(conn, "ERR unknown command")

    conn.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 6379))
    server_socket.listen()
    print("Server running on port 6379...")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
