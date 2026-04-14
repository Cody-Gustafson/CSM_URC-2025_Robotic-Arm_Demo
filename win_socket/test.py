import time
import serial
from port_comm_win import RobotZMQHub

# ==========================================
# SERIAL CONFIGURATION
# ==========================================
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

# Initialize Serial Port
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to serial bus on {SERIAL_PORT}")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

# ==========================================
# MAIN PROGRAM SIMULATION
# ==========================================
if __name__ == "__main__":
    ros_comm = RobotZMQHub()
    
    print("Entering main loop. Press Ctrl+C to stop.")
    try:
        loop_counter = 0
        while True:
            # 1. Read feedback from serial
            current_feedback = None
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        # Convert CSV string back to tuple of floats
                        current_feedback = tuple(map(float, line.split(',')))
                except (ValueError, UnicodeDecodeError):
                    continue # Skip malformed packets
            
            # 2. Call the step function to exchange data with WSL (fall back to zeros if no data)
            if current_feedback and len(current_feedback) == 15:
                new_command = ros_comm.step(current_feedback)
            else:
                # Optional: send dummy if robot hasn't reported yet
                new_command = ros_comm.step((0.0,)*15)
            
            # 3. If WSL sent a command, act on it
            if new_command:
                # output to serial
                cmd_str = ",".join(map(str, new_command)) + "\n"
                ser.write(cmd_str.encode('utf-8'))
                print(f"\n[!] Sent to Serial: {cmd_str.strip()}")
                
            # Simulate your main loop doing other things
            time.sleep(0.01) # 100Hz loop

    except KeyboardInterrupt:
        print("\nExiting main loop...")
    finally:
        ros_comm.close()