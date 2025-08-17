import socket
import ssl
import threading

buffer_size = 1024

certfile = "server.crt"
keyfile = "server.key"


def start_cli_server(port) -> None:
    hostname = "localhost"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.bind((hostname, port))
    sock.listen()
    print(f"Socket listening at {hostname}:{port}...")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    with context.wrap_socket(sock, server_side=True) as ssock:
        while True:
            conn, addr = ssock.accept()

            threading.Thread(target=handle_client, args=(conn, addr)).start()


def handle_client(conn: ssl.SSLSocket, addr: tuple[str, int]) -> None:
    with conn:
        buffer = ""

        while True:
            chunk = conn.recv(buffer_size).decode()
            if not chunk:
                break

            buffer += chunk

            dataBlock = None
            if "\0" in buffer:
                dataBlock, buffer = buffer.split("\0", 1)

            if dataBlock:
                print(f"[{addr[0]}:{addr[1]}] {dataBlock}") # simple echo
