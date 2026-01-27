import socket

def send(sock, *args):
    parts = [f"*{len(args)}"]
    for arg in args:
        parts.append(f"${len(str(arg))}")
        parts.append(str(arg))
    sock.sendall("\r\n".join(parts).encode() + b"\r\n")

def recv(sock):
    data = sock.recv(1024).decode()
    if not data:
        return "(no response)"
    
    c = data[0]
    if c == "+":
        return data[1:].strip()
    elif c == "-":
        return f"(error) {data[1:].strip()}"
    elif c == "$":
        lines = data.split("\r\n")
        if int(lines[0][1:]) == -1:
            return "(nil)"
        return f'"{lines[1]}"'
    return data.strip()

def main():
    host, port = "127.0.0.1", 6379
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"connected to {host}:{port}")
    except ConnectionRefusedError:
        print("connection refused - is the server running?")
        return
    
    while True:
        try:
            line = input(f"{host}:{port}> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not line:
            continue
        if line.lower() == "quit":
            break
        
        send(sock, *line.split())
        print(recv(sock))
    
    sock.close()
    print("bye")

if __name__ == "__main__":
    main()
