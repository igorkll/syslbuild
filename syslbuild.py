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
    if len(sys.argv) == 0:
        print("Usage: syslbuild build [-a ] <json file>")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Пример получения аргумента")
    parser.add_argument("--arch", type=str, default="amd64", help="Архитектура")
    args = parser.parse_args()

    require_root()

    