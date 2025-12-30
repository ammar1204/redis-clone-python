import socket

HOST = "172.31.128.1"
PORT = 6379

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(command.encode() + b"\n")
        response = s.recv(1024)
        print("Server response:", response.decode().strip())

if __name__ == "__main__":
    while True:
        cmd = input("Enter command (PING, ECHO, etc.): ")
        if cmd.lower() in ["exit", "quit"]:
            break
        send_command(cmd)
