import xml.etree.ElementTree as ET
import sys

NETWORK_FILE = "input/regional-network-cleaned.xml"

print(f"Attempting to parse {NETWORK_FILE}...")

try:
    tree = ET.parse(NETWORK_FILE)
    root = tree.getroot()
    print("Successfully parsed XML.")
    print(f"Root tag: {root.tag}")
except ET.ParseError as e:
    print(f"XML Parse Error: {e}")
    with open(NETWORK_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        line_num, col = e.position
        print(f"Error at line {line_num}, column {col}")
        if 0 <= line_num - 1 < len(lines):
            print(f"Content: {lines[line_num-1].strip()}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
