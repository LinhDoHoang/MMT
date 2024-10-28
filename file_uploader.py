class FileUploader:
    def __init__(self):
        self.peer_list = {}

    def upload_to_peer(self, peer, file_name, piece_index):
        print(f"Uploading {file_name} piece {piece_index} to {peer}")
        # Logic upload file
