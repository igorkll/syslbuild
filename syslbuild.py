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
    parser = argparse.ArgumentParser(description="Пример получения аргумента")
    parser.add_argument("--arch", type=str, required=True, help="the processor architecture for which the build will be made")
    args = parser.parse_args()
    
    require_root()

    