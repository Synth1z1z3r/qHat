import socket
import threading

# Simple user database (in real apps, use hashing and a DB)
VALID_USERS = {
    "Ferenc": "17441566",
    "Bombabot": "bot",
    "NIGGER": "melon",
    "glub": "grug",
    "Bombastaff": "pass"
}

clients = {}  # Maps client socket -> username


def broadcast(message, sender_socket):
    for client in list(clients.keys()):
        if client != sender_socket:
            try:
                client.sendall(message)
            except:
                client.close()
                clients.pop(client, None)


def handle_client(client_socket):
    authenticated = False
    username = None
    buffer = ""

    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break

            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                # First check: authentication
                if not authenticated:
                    if line.startswith("AUTH@"):
                        try:
                            _, user, pwd = line.split("@", 2)
                            if VALID_USERS.get(user) == pwd:
                                authenticated = True
                                username = user
                                clients[client_socket] = username
                                client_socket.sendall(b"AUTH_OK\n")
                                print(f"[LOGIN] {username} authenticated.")
                                system_msg = f"TEXT@{username}@[SYSTEM] {username} приєднався до чату!\n"
                                broadcast(system_msg.encode(), client_socket)
                            else:
                                client_socket.sendall(b"AUTH_FAIL\n")
                                client_socket.close()
                                return
                        except ValueError:
                            client_socket.sendall(b"AUTH_FAIL\n")
                            client_socket.close()
                            return
                    else:
                        client_socket.sendall(b"AUTH_FAIL\n")
                        client_socket.close()
                        return
                else:
                    # Already authenticated, handle chat messages
                    broadcast((line + "\n").encode(), client_socket)

        except:
            break

    if authenticated and client_socket in clients:
        print(f"[DISCONNECT] {username} left.")
        broadcast(f"TEXT@{username}@[SYSTEM] {username} вийшов з чату.\n".encode(), client_socket)
        clients.pop(client_socket, None)
    client_socket.close()


def start_server(host='localhost', port=8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Сервер запущено на {host}:{port}")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"[CONNECT] {addr}")
            thread = threading.Thread(target=handle_client, args=(client_socket,))
            thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Зупинка сервера.")
        server.close()


if __name__ == "__main__":
    start_server()
