#!/usr/bin/env python3
import sys
import json
import argparse
import os

def require_root():
    if os.geteuid() != 0:
        print("This program requires root permissions. Restarting with sudo...")
        sys.exit(os.system("sudo {} {}".format(sys.executable, " ".join(sys.argv))))

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: syslbuild build [-arch amd64/i386/arm64/armhf/armel] <json file>")
        sys.exit(1)

    require_root()

    parser = argparse.ArgumentParser(description="Пример получения аргумента")
    parser.add_argument("--arch", type=str, default="amd64", help="Архитектура")
    args = parser.parse_args()
    
    

    