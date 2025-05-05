from dataclasses import dataclass
from datetime import datetime
import serial
import serial.tools.list_ports
import time

# Constants
CHUNK_SIZE = 256
SECTOR_SIZE = 4096
EOT = b'\x04'

@dataclass
class ProtocolInfo:
    device_name: str
    git_commit_sha: str
    protocol_version: str
    build_date: datetime
    flash_size: int
    bootloader_size: int

def find_serial_port(target_vid: int, target_pid: int):
    """
    Scan available serial ports and return the device name of the first port
    whose USB VID/PID match the targets. Returns None if not found.
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # On some systems port.vid/pid may be None
        if port.vid is None or port.pid is None:
            continue
        if (port.vid, port.pid) == (target_vid, target_pid):
            return port.device
    return None

class ProtocolClient:
    def __init__(self, baudrate=115200):
        port = find_serial_port(0xCAFE, 0x6940)
        if port is None:
            raise ConnectionRefusedError("No Eternity bootloader found")
        self.serial = serial.Serial(port, baudrate, timeout=1)

    def send_command(self, cmd):
        if isinstance(cmd, str):
            cmd = cmd.encode('ascii')
        self.serial.write(cmd + EOT)
        self.serial.flush()

    def readline(self):
        line = self.serial.readline()
        return line.decode(errors='ignore').strip()

    def read(self, address):
        """Read a page of the flash"""

        command = f"read {hex(address)}"
        self.send_command(command)

        chunk = self.serial.read(CHUNK_SIZE)
        return chunk

    def write(self, address, data):
        """Write a page of the flash"""

        if (address % CHUNK_SIZE) != 0:
            raise ValueError("Address must be block aligned")

        if len(data) != CHUNK_SIZE:
            raise ValueError("Data must be exactly one page")

        self.send_command(f"write {hex(address)}")

        resp = self.readline()
        if not resp or not resp.startswith('ack'):
            return False, resp

        self.serial.write(data)
        return True, resp

    def erase(self, address):
        """Erase a sector of the flash"""

        if (address % SECTOR_SIZE) != 0:
            raise ValueError("Address must be sector aligned")

        self.send_command(f"erase {hex(address)}")

        resp = self.readline()
        if not resp or not resp.startswith('ack'):
            return False, resp

        return True, resp

    def jump(self):
        """Jumps to the main app - BREAKS THE CONNECTION"""
        self.send_command("jump")
        time.sleep(0.01)
        self.serial.close() # Close the serial connection
        del(self) # Delete itself

    def info(self):
        """Get information about the device"""

        self.send_command("info")
        data = self.readline().split(" ")
        build_date, flash_size, bootloader_size = data[3:]
        parsed_data = data[0:3]
        return ProtocolInfo(*parsed_data, build_date = datetime.strptime(build_date, "%Y-%m-%d,%H:%M:%S"), flash_size = int(flash_size), bootloader_size = int(bootloader_size))

    def reset(self):
        """Reset the device to bootloader - BREAKS THE CONNECTION"""
        self.send_command("reset")
        time.sleep(0.01)
        self.serial.close() # Close the serial connection
        del(self) # Delete itself

if __name__ == "__main__":
    device = ProtocolClient()

    print(device.info())
