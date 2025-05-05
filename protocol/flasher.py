import os
import sys
import math
import argparse
from protocol import ProtocolClient
import time

rich_available = False
try:
    from rich.console import Console
    from rich.progress import Progress
    console = Console()

    rich_available = True

    def print_yellow(text):
        console.print(f"[yellow]{text}[/yellow]")

    def print_red(text):
        console.print(f"[bold red]{text}[/bold red]")

    def print_green(text):
        console.print(f"[green]{text}[/green]")

except ImportError:
    # ANSI fallback
    def print_yellow(text):
        print(f"\033[33m{text}\033[0m")  # Yellow

    def print_red(text):
        print(f"\033[1;31m{text}\033[0m")  # Bold Red

    def print_green(text):
        print(f"\033[32m{text}\033[0m")  # Green


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flash a binary to an Eternity device.")
    parser.add_argument("eternity_bin", help="Path to the binary you wish to flash")
    args = parser.parse_args()

    device = ProtocolClient()

    binfile = args.eternity_bin

    if not os.path.isfile(binfile):
        print_red(f"File not found: {binfile}")
        sys.exit(1)
    size = os.path.getsize(binfile)

    page_num = math.ceil(size / 256)
    sector_num = math.ceil(size / 4096)

    if rich_available:
        progress = Progress()
        task = progress.add_task("[cyan]Erasing data...", total=sector_num)

    if rich_available:
        progress.start()
    for sector in range(sector_num):
        status, resp = device.erase(sector * 4096)
        if not status:
            print_red(f"Error on address {address}: {resp}")
            sys.exit(1)

        if rich_available:
            progress.update(task, completed=sector+1)
        else:
            print(f"\033[33mErased {sector+1}/{sector_num} sectors\033[0m", end='\r')
    if rich_available:
        progress.stop()

    print_yellow(f"Uploading {binfile} ({size} bytes, across {page_num} pages) as a new main program...")

    if rich_available:
        progress = Progress()
        task = progress.add_task("[cyan]Transferring program...", total=page_num)

    def update_progress(transferred, speed):
        speed_str = f"Speed: {speed:.2f} KB/s"
        if rich_available:
            progress.update(task, completed=transferred, description=f"[cyan]{speed_str}")
        else:
            print(f"\033[33mTransferred {(transferred/page_num)*100:.2f}% of pages ({speed_str})\033[0m", end='\r')

    if rich_available:
        progress.start()
    with open(binfile,'rb') as f:
        for page in range(page_num):
            data = f.read(256)
            data += b'\xFF' * (256 - len(data)) # Basically just to pad the last one

            start = time.time()
            status, resp = device.write(page * 256, data)
            end = time.time()

            if not status:
                print_red(f"Error on page {page}: {resp}")
                sys.exit(1)
            speed = len(data) / (end - start) / 1024

            speed_str = f"Speed: {speed:.2f} KB/s"
            update_progress(page + 1, speed)
    if rich_available:
        progress.stop()

    print_green(f"Program {binfile} uploaded to device")

    device.jump()
