#!/bin/python3

import os
import subprocess
import sys
import platform
from typing import Literal, Optional, List

# Detecting the operating system which was used just to be able to automatically install modules.
type: str = platform.system()
pip_type: str = ""

if type == "Windows":
    pip_type = "pip"
elif type == "Linux":
    pip_type = "pip3"
else:
    pip_type = "Unknown"

try:
    import psutil
    from colorama import Fore, Style, init
except ModuleNotFoundError:
    print("[!] Module 'psutil' not found in your local system. Installing it now...")
    if pip_type != "Unknown":
        subprocess.check_call([sys.executable, "-m", pip_type, "install", "psutil", "colorama"])
        import psutil  # re-importing the module after the installation.
        from colorama import Fore, Style, init
    else:
        print(f"[!] The type of Operating system was {type} and unknown to work with due to which the program is not proper functioning...\nExiting the program.")
        sys.exit(500)  # the 500 code of exit is for the error exit while working with OS.

# Constants for Windows System
GENERIC_READ: int = 0x80000000
GENERIC_WRITE: int = 0x40000000
FILE_SHARE_READ: int = 0x00000001
FILE_SHARE_WRITE: int = 0x00000002
OPEN_EXISTING: int = 3

# Defining the Pattern type for the safety while wipping of the disk.
PatternType: Literal = Literal['zeros', 'ones', 'random']

# Initializing the Colorama
init()

red_color: str = Fore.RED
green_color: str = Fore.GREEN
blue_color: str = Fore.BLUE
reset_color: str = Style.RESET_ALL

def WelcomeMessage() -> None:
    print(f'''{green_color}
________  .__        __     __      __.__                            
\______ \ |__| _____|  | __/  \    /  \__|_____ ______   ___________ 
 |    |  \|  |/  ___/  |/ /\   \/\/   /  \____ \\\\____ \_/ __ \_  __ \\
 |    `   \  |\___ \|    <  \        /|  |  |_> >  |_> >  ___/|  | \/
/_______  /__/____  >__|_ \  \__/\  / |__|   __/|   __/ \___  >__|   
        \/        \/     \/       \/     |__|   |__|        \/       
                                {blue_color}- By Rohan Thapa

{red_color}Note*: This program is dangerous while using carelessly so be careful while wipping the disk as it is irreversible process.
    {reset_color}''')

def list_disk_partitions() -> str:
    partitions: List[psutil._common.sdiskpart] = psutil.disk_partitions()

    for i, partition in enumerate(partitions):
        print(f"{blue_color}{i}.{reset_color} Device: {green_color}{partition.device}{reset_color}")
        print(f"\tMountpoint: {green_color}{partition.mountpoint}{reset_color}")
        print(f"\tFile system type: {green_color}{partition.fstype}{reset_color}\n")

    disk_choosen: str = input(f"{blue_color}Please Choose Disk Index (0|1|...|n): {reset_color}")

    if not disk_choosen.isdigit():
        print(f"{red_color}[!] The provided input should be digit denoting the index of the disk provided above as 0, 1, 2 and so on, not the other input as it was provided as `{blue_color}{disk_choosen}{red_color}` which is not a digit.{reset_color}")
        return "205"  # the exit code 205 is for not being the proper input type.

    disk_index: int = int(disk_choosen)

    if not ((disk_index >= 0) and (disk_index <= (len(partitions) - 1))):
        print(f"{red_color}[!] The index number of the disk was invalid as the indexed disk value does not exist.{reset_color}")
        return "208"  # the exit code 208 is for not being the proper input value.

    return partitions[int(disk_choosen)].device

def generate_pattern(size: int, pattern_type: PatternType = 'random') -> bytes:
    if pattern_type == 'zeros':
        return b'\x00' * size
    elif pattern_type == 'ones':
        return b'\xFF' * size
    elif pattern_type == 'random':
        return os.urandom(size)
    else:
        print(f"{red_color}[!] Unsupported Pattern Type Provided.{reset_color}")
        sys.exit(208)  # the exit code 208 is for the not being the proper input value.

def wipe_disk_windows(disk_name: str, pattern_type: PatternType = 'random', passes: int = 3) -> None:
    import ctypes  # this is for windows API calls

    # Open the disk with CreateFileW() system call of Windows
    h_disk = ctypes.windll.kernel32.CreateFileW(disk_name, GENERIC_READ | GENERIC_WRITE,
                                                FILE_SHARE_READ | FILE_SHARE_WRITE, None,
                                                OPEN_EXISTING, 0, None)

    if h_disk == -1:
        print(f"{red_color}[!] Failed to Open the provided Disk{reset_color}")
        sys.exit(430)  # The error code 430 is for the system to unable to open the file.

    # Setting the Buffer Size (512 bytes for one sector)
    buffer_size: int = 512
    buffer = generate_pattern(buffer_size, pattern_type)
    bytes_written = ctypes.c_uint(0)

    # Get the total number of sectors
    dg = ctypes.create_string_buffer(24)
    returned = ctype.c_uint(0)
    ctypes.windll.kernel32.DeviceIoControl(h_disk, 0x00070000, None, 0, dg, 24, ctypes.byref(returned), None)

    sectors_per_track: int = int.from_bytes(dg.raw[4:8], 'little')
    num_cylinders: int = int.from_bytes(dg.raw[0:8], 'little')
    num_sectors: int = num_cylinders * sectors_per_track

    for times in range(passes):
        for sector in range(num_sectors):
            success = ctypes.windll.kernel32.WriteFile(h_disk, buffer, buffer_size, ctypes.byref(bytes_written), None)
            if not success:
                print(f"{red_color}[!] Failed to Write to the provided Disk{reset_color}")
                sys.exit(503)  # Faild to write error code is 503
        print(f"{green_color}[+] Pass {times + 1} complete.{reset_color}")

    ctypes.windll.kernel32.FlushFileBuffers(h_disk)
    ctypes.windll.kernel32.CloseHandle(h_disk)
    print(f"\n{green_color}[+] The Disk Wipe was Completed.{reset_color}")

def wipe_disk_linux(disk_name: str, pattern_type: PatternType = 'random', passes: int = 3) -> None:
    # Open the disk provided for the wipping
    try:
        with open(disk_name, 'rb+') as disk:
            # Get the disk size in bytes
            disk.seek(0, os.SEEK_END)
            disk_size: int = disk.tell()
            disk.seek(0)

            buffer_size: int = 512  # Setting the buffer size to 512 bytes per sector
            num_sectors: int = disk_size // buffer_size

            for times in range(passes):
                for sector in range(num_sectors):
                    buffer: bytes = generate_pattern(buffer_size, pattern_type)
                    disk.write(buffer)
                print(f"{green_color}[+] Pass {times + 1} complete.{reset_color}")

            disk.flush()
            os.fsync(disk.fileno())
        print(f"{green_color}[+] The Disk Wipe was Completed.{reset_color}")
    except OSError as e:
        print(f"{red_color}[!] Failed to open or write to the disk: {e}{reset_color}")
        sys.exit(503)  # As this is realted to failed to write eventually but could also be 430.

def main() -> None:
    disk_info = list_disk_partitions()
    if disk_info == '205' or disk_info == '208':
        sys.exit(int(disk_info))
    print(f"\n{red_color}[^] While selecting the values the `green` value in the option are the default values.{reset_color}")
    print(f"\n{green_color}[+] You have choosen the disk `{disk_info}` for wiping...{reset_color}")

    pattern: str = input(f"{blue_color}Choose the Pattern Type you want to use while wipping the disk (zeros, ones, {green_color}random{blue_color}): {reset_color}").lower() or 'random'
    if pattern not in ['zeros', 'ones', 'random']:
        print(f"{red_color}[!] The selected Pattern Type `{blue_color}{pattern}{red_color}` is not valid.{reset_color}")
        sys.exit(208)  # Not valid input values

    try_times: str = input(f"{blue_color}Choose the times of passes you want (1, 2, {green_color}3{blue_color}, ..., n): {reset_color}") or '3'
    if not try_times.isdigit():
        print(f"{red_color}[!] As this was the number of times the drive would be written which sould be a number nothing else like `{blue_color}{try_times}{red_color}` you provided.{reset_color}")
        sys.exit(205)  # Not valid input types
    passes: int = int(try_times)

    sure_choice: str = input(f"{blue_color}Are you sure to wipe the disk ({green_color}Y{blue_color}|{red_color}N{blue_color}): {reset_color}").upper() or 'y'

    if sure_choice != 'Y':
        print(f"\n{red_color}[^] Thank God you stopped this process on time otherwise the whole drive would be wipped out and no remains of its content would have been left.{reset_color}")
        sys.exit(0)  # the 0 is the successful exit without any error as the wipping of the disk was not needed so the program was terminated.

    # Wiping of the disk.
    print(f"\n{green_color}[+] Starting to wipe the disk of {type} named as: {disk_info}...{reset_color}")
    print(f"{red_color}[^] Choosing the pattern type `{blue_color}{pattern}{red_color}` and passes value `{blue_color}{str(passes)}{red_color}`.{reset_color}")

    if type == 'Windows':
        wipe_disk_windows(disk_info, pattern, passes)
    elif type == 'Linux':
        wipe_disk_linux(disk_info, pattern, passes)
    else:
        print(f"{red_color}[!] As the OS `{type}` was unsupported with this tool.{reset_color}")
        sys.exit(500)  # The unsupportive OS and 500 is while working with OS.

if __name__ == "__main__":
    WelcomeMessage()
    print(f"{green_color}[+] The operating system is {type} which is being used.\n{reset_color}")
    main()

# Developed by Rohan Thapa for wipping the disks.
