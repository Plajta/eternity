#!/usr/bin/env python3
import cmd
import readline
import os
import sys
import math
import protocol
import time
from rich.console import Console
from rich.progress import Progress

console = Console()

class DeviceShell(cmd.Cmd):
    prompt = "\033[1;36mEternity>\033[0m "

    def __init__(self, device):
        super().__init__()
        self.device = device

    def preloop(self):
        readline.parse_and_bind('tab: complete')

    def do_write(self, arg):
        "push <binfile>     Upload a new main program to the device"

        parts = arg.split()
        if not parts or len(parts) != 1:
            console.print("[bold red]Usage: push <binary file>[/bold red]")
            return
        binfile = parts[0]

        if not os.path.isfile(binfile):
            console.print(f"[bold red]Local file not found: {binfile}[/bold red]")
            return
        size = os.path.getsize(binfile)

        page_num = math.ceil(size / 256)
        sector_num = math.ceil(size / 4096)

        self.erase(0, sector_num)

        console.print(f"[yellow]Uploading {binfile} ({size} bytes, across {page_num} pages) as a new main program...[/yellow]")

        progress = Progress()
        task = progress.add_task("[cyan]Transferring program...", total=page_num)

        def update_progress(transferred, speed):
            speed_str = f"Speed: {speed:.2f} KB/s"
            progress.update(task, completed=transferred, description=f"[cyan]{speed_str}")

        with progress:
            with open(binfile,'rb') as f:
                for page in range(page_num):
                    data = f.read(256)
                    data += b'\xFF' * (256 - len(data)) # Basically just to pad the last one

                    start = time.time()
                    status, resp = self.device.write(page * 256, data)
                    end = time.time()

                    if not status:
                        console.print(f"[bold red]Error on page {page}: {resp}[/bold red]")
                        return
                    speed = len(data) / (end - start) / 1024

                    speed_str = f"Speed: {speed:.2f} KB/s"
                    progress.update(task, completed=page+1, description=f"[cyan]{speed_str}")

        console.print(f"[green]Program [bold]{binfile}[/bold] uploaded to device")

    def do_read(self, arg):
        "read <address> <length> <filename>  Download data from the address"

        parts = arg.split()
        if not parts or len(parts) != 3:
            console.print("[bold red]Usage: read <address % 256==0> <length in pages> <filename>[/bold red]")
            return
        address = int(parts[0])
        length = int(parts[1])
        filename = parts[2]

        if address % 256 != 0:
            console.print("[bold red]Address must be aligned to 256 bytes (page size)[/bold red]")
            return

        progress = Progress()
        task = progress.add_task("[cyan]Transferring data...", total=length)

        with progress:
            with open(filename,'wb') as f:
                for page in range(length):
                    start = time.time()
                    data = self.device.read(address + page * 256)
                    end = time.time()
                    if data is None or len(data) != 256:
                        console.print(f"[bold red]Error: Failed to read page {page}[/bold red]")
                        return
                    speed = len(data) / (end - start) / 1024
                    f.write(data)

                    speed_str = f"Speed: {speed:.2f} KB/s"
                    progress.update(task, completed=page+1, description=f"[cyan]{speed_str}")

        console.print(f"[bold green]Data downloaded to file {filename}![/bold green]")

    def erase(self, address, length):
        progress = Progress()
        task = progress.add_task("[cyan]Erasing data...", total=length)

        with progress:
            for sector in range(length):
                status, resp = self.device.erase(address + sector * 4096)
                if not status:
                    console.print(f"[bold red]Error on address {address}: {resp}[/bold red]")
                    return

                progress.update(task, completed=sector+1)

    def do_erase(self, arg):
        "erase <address> <length>        Erase a sector of the device"

        parts = arg.split()
        if not parts or len(parts) != 2:
            console.print("[bold red]Usage: erase <address % 4096 != 0> <length in sectors>[/bold red]")
            return
        address = int(parts[0])
        length = int(parts[1])

        if address % 4096 != 0:
            console.print("[bold red]Address must be aligned to 4096 bytes (sector size)[/bold red]")
            return

        self.erase(address, length)

        console.print("[bold green]Data erased![/bold green]")

    def do_jump(self, arg):
        "jump        Jump to the main program"
        self.device.jump()
        return self.do_exit('')

    def do_info(self, arg):
        "info              Get information about the device"
        info = self.device.info()
        console.print(f"[yellow]Device Name: [/yellow][red]{info.device_name}[/red]")
        console.print(f"[yellow]Protocol version: [/yellow][red]{info.protocol_version}[/red]")
        console.print(f"[yellow]Git SHA: [/yellow][red]{info.git_commit_sha}[/red]")
        console.print(f"[yellow]Build date: [/yellow][red]{info.build_date}[/red]")
        console.print(f"[yellow]Flash size: [/yellow][red]{info.flash_size/1024} KB[/red]")
        console.print(f"[yellow]Bootloader size: [/yellow][red]{info.bootloader_size/1024} KB[/red]")

    def do_reset(self, arg):
        "reset              Reset the device to bootrom"
        self.device.reset()
        return self.do_exit('')

    def do_exit(self, arg):
        "exit                Exit shell"
        console.print("[bold cyan]Goodbye![/bold cyan]")
        return True
    do_quit = do_exit

if __name__ == '__main__':
    device = protocol.ProtocolClient()
    shell = DeviceShell(device)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("") # Just so it's on a new line :)
        shell.do_exit('')
        sys.exit(0)
