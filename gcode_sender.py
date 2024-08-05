import serial
import time
import os

class MarlinPrinter:
    def __init__(self, port, baud_rate=250000, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        try:
            print(f"Connecting to printer on {self.port} at {self.baud_rate} baud...")
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            time.sleep(2)  # Wait for connection to stabilize
            print("Connected successfully")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to printer: {e}")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            print("Disconnecting from printer...")
            self.ser.close()
            print("Disconnected")

    def send_command(self, command, wait_for_ok=True):
        if not self.ser or not self.ser.is_open:
            print("Printer is not connected")
            return False

        print(f"Sending command: {command}")
        self.ser.write(f"{command}\n".encode())
        self.ser.flush()

        responses = []
        if wait_for_ok:
            while True:
                response = self.ser.readline().decode().strip()
                if response:
                    print(f"Received: {response}")
                    responses.append(response)
                    if response.startswith("ok"):
                        return True, responses
                    elif "error" in response.lower():
                        print(f"Error: {response}")
                        return False, responses
                else:
                    # No more data to read
                    break

        return True, responses

    def init_sd_card(self):
        print("Initializing SD card...")
        result, responses = self.send_command("M21")
        if result:
            print("SD card initialized successfully")
        else:
            print("Failed to initialize SD card")
        return result

    def start_file_write(self, filename):
        print(f"Starting file write: {filename}")
        result, responses = self.send_command(f"M28 {filename}")
        if result:
            print("File write started successfully")
        else:
            print("Failed to start file write")
        return result

    def end_file_write(self):
        print("Ending file write...")
        result, responses = self.send_command("M29")
        if result:
            print("File write ended successfully")
        else:
            print("Failed to end file write")
        return result

    def send_gcode_to_sd(self, gcode_file):
        if not self.connect():
            return False

        try:
            # Initialize SD card
            if not self.init_sd_card():
                return False

            # Start file write
            filename = os.path.basename(gcode_file)
            if not self.start_file_write(filename):
                return False

            # Read and send G-code file content
            print(f"Sending file: {filename}")
            total_lines = sum(1 for line in open(gcode_file))
            sent_lines = 0

            with open(gcode_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith(';'):  # Ignore comments and empty lines
                        result, _ = self.send_command(line, wait_for_ok=True)
                        if not result:
                            print(f"Failed to send command: {line}")
                            return False
                    
                    sent_lines += 1
                    if sent_lines % 100 == 0:  # Update progress every 100 lines
                        progress = (sent_lines / total_lines) * 100
                        print(f"Progress: {progress:.2f}% ({sent_lines}/{total_lines})")

            # End file write
            if not self.end_file_write():
                return False

            print(f"Successfully sent {filename} to printer's SD card")
            return True

        finally:
            self.disconnect()

# Example usage
if __name__ == "__main__":
    printer = MarlinPrinter("COM7")  # Adjust port as necessary
    gcode_file = "test.gcode"
    printer.send_gcode_to_sd(gcode_file)