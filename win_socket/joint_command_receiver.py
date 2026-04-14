import socket

class CommandReceiver:
    def __init__(self, host='0.0.0.0', port=5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.sock.settimeout(0.01)  # Non-blocking behavior

        print("Initialized Command Receiver")

    def check_for_command(self):
        """
        Non-blocking check for incoming command.
        Returns:
            str command if received
            None if no data available
        """
        try:
            conn, addr = self.sock.accept()
        except socket.timeout:
            return None  # No connection waiting

        with conn:
            try:
                data = conn.recv(1024)
            except socket.timeout:
                return None

            if not data:
                return None

            return data.decode('utf-8')

    def close(self):
        self.sock.close()