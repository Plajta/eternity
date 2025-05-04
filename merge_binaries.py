import argparse
import os

def join_bin(bin1_path, bin2_path, bin2_offset, output_path, fill_byte=0xFF):
    with open(bin1_path, 'rb') as f:
        bin1_data = f.read()

    with open(bin2_path, 'rb') as f:
        bin2_data = f.read()

    # Calculate size needed
    end_of_bin1 = len(bin1_data)
    if end_of_bin1 > bin2_offset:
        raise ValueError("Offset is too small")
    end_of_bin2 = bin2_offset + len(bin2_data)

    # Start with a buffer filled with fill_byte
    output = bytearray([fill_byte] * end_of_bin2)

    # Copy binaries into correct positions
    output[0:end_of_bin1] = bin1_data
    output[bin2_offset:end_of_bin2] = bin2_data

    with open(output_path, 'wb') as f:
        f.write(output)

    print(f"Joined {os.path.basename(bin1_path)} and {os.path.basename(bin2_path)} into {os.path.basename(output_path)} (size: {end_of_bin2} bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Join eternity with a project at specific offset.")
    parser.add_argument("eternity_bin", help="Path to eternity's binary (starts at offset 0)")
    parser.add_argument("project_bin", help="Path to project binary")
    parser.add_argument("offset", type=lambda x: int(x, 0), help="Offset to place project binary (e.g., 0x100000)")
    parser.add_argument("output", help="Output file path")
    args = parser.parse_args()

    join_bin(args.eternity_bin, args.project_bin, args.offset, args.output)
