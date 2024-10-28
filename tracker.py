class Tracker:
    def __init__(self):
        self.file_registry = {}

    def register_file(self, peer_address, file_name):
        if file_name not in self.file_registry:
            self.file_registry[file_name] = []
        if peer_address not in self.file_registry[file_name]:
            self.file_registry[file_name].append(peer_address)

    def get_peers_with_file(self, file_name):
        return self.file_registry.get(file_name, [])

    def process_command(self, command, args):
        if command == "REGISTER":
            peer_address, file_name = args
            self.register_file(peer_address, file_name)
            return f"File {file_name} registered by {peer_address}"
        elif command == "REQUEST":
            file_name = args[0]
            peers = self.get_peers_with_file(file_name)
            return ','.join(peers) if peers else "No peers found"
        elif command == "LIST":
            return ', '.join(self.file_registry.keys())
        return "Invalid Command"
