import socket

class FeedbackSender:
    def __init__(self, wsl_ip, port=5005):
        self.wsl_ip = wsl_ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_feedback(self, feedback_data):
        """
        feedback_data: string (e.g., "J1,J2,J3,J4,J5")
        """
        try:
            if isinstance(feedback_data, str):
                feedback_data = feedback_data.encode('utf-8')
            self.sock.sendto(feedback_data, (self.wsl_ip, self.port))
        except Exception as e:
            print(f"Feedback send error: {e}")

    def close(self):
        self.sock.close()