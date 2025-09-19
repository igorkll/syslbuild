#!/usr/bin/env python3
import sys
import json5
import argparse
import subprocess
import os

def readBool(tbl, name):
    if name in tbl:
        return bool(tbl[name])
    
    return False

def getFolder(architecture, item):
    if readBool(item, "export"):
        path = os.path.join("output", item["name"])
    else:
        path = os.path.join(".temp", "build", item["name"])
    
    return path

def buildDebian(architecture, item):
    subprocess.run(["mmdebstrap",
        "--arch", architecture,
        "--variant", item["variant"],
        "--include=" + ",".join(item["include"]),
        "--exclude=" + ",".join(item["exclude"]),
        "--aptopt=Acquire::Check-Valid-Until \"false\"",
        "--aptopt=Acquire::AllowInsecureRepositories \"true\"",
        "--aptopt=APT::Get::AllowUnauthenticated \"true\"",
        item["suite"],
        ".local/rootfs",
        item["url"]
    ])

def buildUnknown(architecture, item):
    print(f"unknown build item type: {item["type"]}")
    sys.exit(1)

buildActions = {
    "debian": buildDebian
}

def buildItems(architecture, builditems):
    for item in builditems:
        buildActions.get(item["type"], buildUnknown)(architecture, item)

def buildProject(architecture, json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)
    
    buildItems(architecture, projectData["builditems"])

def requireRoot():
    if os.geteuid() != 0:
        print("This program requires root permissions. Restarting with sudo...")
        sys.exit(os.system("sudo {} {}".format(sys.executable, " ".join(sys.argv))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="an assembly system for creating Linux distributions. it is focused on embedded distributions")
    parser.add_argument("--arch", choices=["amd64", "i386", "arm64", "armhf", "armel"], type=str, required=True, help="the processor architecture for which the build will be made")
    parser.add_argument("json_path", type=str, help="the path to the json file of the project")
    args = parser.parse_args()
    
    requireRoot()
    buildProject(args.arch, args.json_path)

    