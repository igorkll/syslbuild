#!/usr/bin/env python3
import sys
import json
import argparse
import os

def requireRoot():
    if os.geteuid() != 0:
        print("This program requires root permissions. Restarting with sudo...")
        sys.exit(os.system("sudo {} {}".format(sys.executable, " ".join(sys.argv))))

def buildItems(architecture, builditems):
    

def buildProject(architecture, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        projectData = json.load(f)
    
    buildItems(architecture, projectData["builditems"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="an assembly system for creating Linux distributions. it is focused on embedded distributions")
    parser.add_argument("--arch", choices=["amd64", "i386", "arm64", "armhf", "armel"], type=str, required=True, help="the processor architecture for which the build will be made")
    parser.add_argument("json_path", type=str, help="the path to the json file of the project")
    args = parser.parse_args()
    
    requireRoot()
    buildProject(args.arch, args.json_path)

    