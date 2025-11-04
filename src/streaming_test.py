import socket

HOST = "localhost"
PORT = 9998

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")
    try:
        while True:
            data = s.recv(4096)
            if not data:
                break
            print(data.decode("utf-8").strip())
    except KeyboardInterrupt:
        print("\nClient disconnected.")

