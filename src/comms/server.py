import socket
import ssl
import threading

from app_streams import AppEventStream, UserMessageEvent

buffer_size = 1024

certfile = "server.crt"
keyfile = "server.key"


def start_comms_server(port: int, event_stream: AppEventStream) -> None:
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

            threading.Thread(
                target=handle_client, args=(conn, addr, event_stream)
            ).start()


def handle_client(
    conn: ssl.SSLSocket, addr: tuple[str, int], event_stream: AppEventStream
) -> None:
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
                event = UserMessageEvent(dataBlock)
                event_stream.push(event)
