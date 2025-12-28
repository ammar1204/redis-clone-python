import socket

DATA_STORE = {}

def parse_resp(conn):
    data = conn.recv(1024)
    if not data.strip():
        return None

    # Fallback: plain text commands (Telnet-friendly)
    if not data.startswith(b"*"):
        return data.strip().decode().split()

    # RESP Parsing
    parts = data.split(b"\r\n")
    arg_count = int(parts[0][1:])
    args = []

    i = 1
    while i < len(parts):
        if parts[i].startswith(b"$"):
            length = int(parts[i][1:])
            args.append(parts[i+1].decode())
            i += 2
        else:
            i += 1

    return args


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 6379))
    server_socket.listen(1)

    while True:
        conn, addr = server_socket.accept()
        while True:
            args = parse_resp(conn)
            if not args:
                break

            command = args[0].upper()

            if command == "PING":
                conn.sendall(b"PONG\n")

            elif command == "ECHO" and len(args) > 1:
                response = " ".join(args[1:]).encode() + b"\n"
                conn.sendall(response)

            elif command == "SET" and len(args) > 2:
                key = args[1]
                value = args[2]
                DATA_STORE[key] = value
                conn.sendall(b"OK\n")

            elif command == "GET" and len(args) > 1:
                key = args[1]
                value = DATA_STORE.get(key)
                if value is not None:
                    conn.sendall(value.encode() + b"\n")
                else:
                    conn.sendall(b"(nil)\n")

            else:
                conn.sendall(b"ERR unknown command\n")

    conn.close()

if __name__ == "__main__":
    start_server()
