from joint_command_receiver import CommandReceiver
from joint_feedback_sender import FeedbackSender

command_receiver = CommandReceiver()
feedback_sender = FeedbackSender("172.xx.xx.xx", 5005)  # WSL IP

print("Running Arm Communication")

try:
    while True:
        cmd = command_receiver.check_for_command()
        feedback_data = "J1,J2,J3,J4,J5"  # Replace with serial_port.read()

        if cmd:
            print(f"Command Received: {cmd}")
            # serial_port.write(cmd.encode('utf-8'))

        if feedback_data:
            feedback_sender.send_feedback(feedback_data)

except KeyboardInterrupt:
    print("Shutting down")

finally:
    command_receiver.close()
    feedback_sender.close()