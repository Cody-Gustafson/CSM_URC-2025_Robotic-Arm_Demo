import zmq
import struct

class RobotZMQHub:
    def __init__(self):
        """Initializes the ZMQ sockets. Call this before your specific loop starts."""
        self.context = zmq.Context()
        
        self.command_receiver = self.context.socket(zmq.PULL)
        self.command_receiver.bind("tcp://0.0.0.0:5000")
        
        self.feedback_sender = self.context.socket(zmq.PUB)
        self.feedback_sender.bind("tcp://0.0.0.0:5005")
        
        print("ZMQ Hub Initialized. Ready for communication.")

    def step(self, current_feedback_tuple):
        """
        Call this function inside your specific loop.
        current_feedback_tuple: A tuple/list of your feedback floats.
        Returns: A tuple of command floats if a command was received, else None.
        """
        # --- 1. RECEIVE COMMANDS (Non-blocking) ---
        cmd_data = None
        try:
            # We expect raw bytes now, not strings
            cmd_bytes = self.command_receiver.recv(flags=zmq.NOBLOCK)
            
            # Unpack the bytes into 5 floats (format '<5f')
            cmd_data = struct.unpack('<5f', cmd_bytes)
        except zmq.Again:
            pass # No command waiting

        # --- 2. SEND FEEDBACK ---
        if current_feedback_tuple:
            # Pack the 15 floats into raw bytes (format '<15f')
            feedback_bytes = struct.pack('<15f', *current_feedback_tuple)
            self.feedback_sender.send(feedback_bytes)

        return cmd_data

    def close(self):
        """Cleans up sockets. Call this when exiting your specific loop."""
        self.command_receiver.close()
        self.feedback_sender.close()
        self.context.term()
        print("ZMQ Hub Closed.")