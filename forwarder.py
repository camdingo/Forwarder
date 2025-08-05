import socket
import threading
import configparser
import time


def handle_remote_connection(remote_host, remote_port, local_port):
    clients = []
    clients_lock = threading.Lock()

    def broadcast_to_clients(data):
        with clients_lock:
            for client in clients[:]:
                try:
                    client.sendall(data)
                except Exception:
                    clients.remove(client)
                    client.close()

    def listen_for_local_clients():
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('127.0.0.1', local_port))
        server_sock.listen()
        print(f"[+] Listening on localhost:{local_port} for local clients")

        while True:
            client_sock, _ = server_sock.accept()
            print(f"[+] Local client connected to port {local_port}")
            with clients_lock:
                clients.append(client_sock)

            # Optional: relay client data back to remote (disabled by default)
            def relay_from_client(sock):
                try:
                    while True:
                        data = sock.recv(4096)
                        if not data:
                            break
                        # To enable sending client data to remote, uncomment:
                        # remote_sock.sendall(data)
                finally:
                    with clients_lock:
                        if sock in clients:
                            clients.remove(sock)
                    sock.close()

            threading.Thread(target=relay_from_client, args=(client_sock,), daemon=True).start()

    def receive_from_remote(remote_sock):
        try:
            while True:
                data = remote_sock.recv(4096)
                if not data:
                    print(f"[-] Connection to {remote_host}:{remote_port} closed.")
                    break
                broadcast_to_clients(data)
        finally:
            remote_sock.close()

    while True:
        try:
            print(f"[+] Connecting to SPOTS {remote_host}:{remote_port}")
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.connect((remote_host, remote_port))
            print(f"[+] Connected to {remote_host}:{remote_port}")

            threading.Thread(target=receive_from_remote, args=(remote_sock,), daemon=True).start()
            listen_for_local_clients()
        except Exception as e:
            print(f"[!] Failed to connect to {remote_host}:{remote_port}: {e}")
            time.sleep(5)


def main():
    config = configparser.ConfigParser()
    config.read('connections.ini')

    # Iterate config file, and create a thread per forwarded data feed
    for section in config.sections():
        remote_host = config[section].get('remote_host')
        remote_port = config[section].getint('remote_port')
        local_port = config[section].getint('local_port')

        threading.Thread(
            target=handle_remote_connection,
            args=(remote_host, remote_port, local_port),
            daemon=True
        ).start()

    # Keep main thread alive
    while True:
        time.sleep(10)


if __name__ == '__main__':
    main()

