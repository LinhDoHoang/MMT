import socket
import threading
from tracker import Tracker

class TrackerServer:
    def __init__(self, host='0.0.0.0', port=65432):
        self.tracker = Tracker()
        self.host = host
        self.port = port

    def handle_client(self, conn, addr):
        print(f"New connection from {addr}")
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                command, *args = data.split()
                response = self.tracker.process_command(command, args)
                conn.send(response.encode())
        except ConnectionResetError:
            print(f"Connection reset by peer {addr}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
            print(f"Connection with {addr} closed.")

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Tracker Server running on {self.host}:{self.port}")
        
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    tracker_server = TrackerServer()
    tracker_server.start()
