import socket
import threading
import os
import shutil
import time
from file_downloader import FileDownloader
from magnet import MetainfoFile, MagnetText

TRACKER_HOST = '127.0.0.1'
TRACKER_PORT = 65432

class Peer:
    def __init__(self, peer_name, host='127.0.0.1', port=0):
        self.peer_name = peer_name
        self.host = host
        self.port = port
        self.repo_path = f"peer_files/{peer_name}/"
        self.shared_files = {}  # Lưu các file và các phần đã có để chia sẻ
        self.peer_scores = {}  # Điểm để đánh giá các peer dựa trên tit-for-tat
        self.neighbors = {}  # Ghi lại peer và các file mà neighbor có


        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)

    def register_file(self, file_path):
        if not os.path.isfile(file_path):
            print("File not found, please check the path.")
            return

        file_name = os.path.basename(file_path)
        dest_path = os.path.join(self.repo_path, file_name)
        shutil.copy(file_path, dest_path)
        print(f"File {file_name} has been copied to {self.repo_path}")

        tracker_address = f"{TRACKER_HOST}:{TRACKER_PORT}"
        metainfo = MetainfoFile(dest_path, tracker_address)
        metainfo.save()
        
        self.shared_files[file_name] = metainfo.pieces

        magnet_link = MagnetText.generate_magnet_link(dest_path)
        print(f"Magnet link for {file_name}: {magnet_link}")

        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))
        tracker_socket.send(f"REGISTER {self.host}:{self.port} {file_name}".encode())
        tracker_socket.close()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        self.port = server_socket.getsockname()[1]
        server_socket.listen(5)
        print(f"Peer {self.peer_name} running on {self.host}:{self.port}")
        
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn,)).start()

    def handle_client(self, conn):
        file_name = conn.recv(1024).decode()
        file_path = os.path.join(self.repo_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                piece = f.read(512 * 1024)
                while piece:
                    conn.send(piece)
                    piece = f.read(512 * 1024)
        conn.close()

    def list_files(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))
        tracker_socket.send("LIST".encode())
        data = tracker_socket.recv(1024).decode()
        tracker_socket.close()
        print("Available files on server:", data)

    def download_file(self, file_name):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))
        tracker_socket.send(f"REQUEST {file_name}".encode())
        data = tracker_socket.recv(1024).decode()
        tracker_socket.close()

        if data == "No peers found":
            print("File not found on any peer.")
            return

        peers = data.split(',')
        downloader = FileDownloader(file_name, peers, self.repo_path)
        downloader.start()

    def tit_for_tat(self):
        while True:
            time.sleep(10)
            for peer, score in list(self.peer_scores.items()):
                if score < 1:
                    print(f"Disconnecting from free-rider peer {peer}")
                    del self.peer_scores[peer]
                    
    def report_to_tracker(self):
        while True:
            time.sleep(60)  # Mỗi phút gửi báo cáo về tracker
            tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))
            tracker_socket.send(f"REPORT {self.host}:{self.port} has files {list(self.shared_files.keys())}".encode())
            tracker_socket.close()

    def track_peers(self):
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.connect((TRACKER_HOST, TRACKER_PORT))
        tracker_socket.send("TRACK".encode())
        neighbors = tracker_socket.recv(1024).decode()
        tracker_socket.close()
        print(f"Connected neighbors: {neighbors}")

if __name__ == "__main__":
    peer_name = input("Enter peer name: ")
    peer = Peer(peer_name, port=0)
    threading.Thread(target=peer.start_server).start()
    threading.Thread(target=peer.tit_for_tat).start()
    threading.Thread(target=peer.track_peers).start()

    while True:
        action = input("Choose action: [upload, list, download, exit]: ").strip().lower()
        if action == "upload":
            file_path = input("Enter the path of the file to upload: ").strip()
            peer.register_file(file_path)
        elif action == "list":
            peer.list_files()
        elif action == "download":
            file_name = input("Enter file name to download: ")
            peer.download_file(file_name)
        elif action == "exit":
            break
