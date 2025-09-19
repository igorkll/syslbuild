#!/usr/bin/env python3
import sys
import json5
import argparse
import subprocess
import os
import shutil

path_output = "output"
path_temp = ".temp"
path_build = os.path.join(path_temp, "build")

def getLogFile(architecture):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"build_{architecture}_{timestamp}.log"
    return open(os.path.join(path_temp, "logs", log_filename), "w")

def readBool(tbl, name):
    if name in tbl:
        return bool(tbl[name])
    
    return False

def getItemPath(item):
    if readBool(item, "export"):
        path = os.path.join(path_output, item["name"])
    else:
        path = os.path.join(path_build, item["name"])
    
    return path

def getFolder(item):
    path = getItemPath(item)
    os.makedirs(path, exist_ok=True)
    
    return path

def deleteDirectory(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)

def buildLog(logstr):
    print(f"-------- SYSLBUILD: {logstr}")

def executeProcess(item, cmd):
    buildLog(f"building item 1/1 {item["type"]} ({item["name"]})")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        buildLog("failed to build")
        os.exit(1)

def buildDebian(architecture, item):
    include_arg = "--include=" + ",".join(item["include"]) if item.get("include") else None
    exclude_arg = "--exclude=" + ",".join(item["exclude"]) if item.get("exclude") else None

    cmd = ["mmdebstrap", "--arch", architecture, "--variant", item["variant"]]
    if include_arg: cmd.append(include_arg)
    if exclude_arg: cmd.append(exclude_arg)
    cmd += [
        "--aptopt=Acquire::Check-Valid-Until false",
        "--aptopt=Acquire::AllowInsecureRepositories true",
        "--aptopt=APT::Get::AllowUnauthenticated true",
        item["suite"],
        getFolder(item),
        item["url"]
    ]
    executeProcess(item, cmd)

def buildUnknown(architecture, item):
    buildLog(f"unknown build item type: {item["type"]}")
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

    deleteDirectory(path_output)
    deleteDirectory(path_build)
    
    buildItems(architecture, projectData["builditems"])

def requireRoot():
    if os.geteuid() != 0:
        buildLog("This program requires root permissions. Restarting with sudo...")
        sys.exit(os.system("sudo {} {}".format(sys.executable, " ".join(sys.argv))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="an assembly system for creating Linux distributions. it is focused on embedded distributions")
    parser.add_argument("--arch", choices=["amd64", "i386", "arm64", "armhf", "armel"], type=str, required=True, help="the processor architecture for which the build will be made")
    parser.add_argument("json_path", type=str, help="the path to the json file of the project")
    args = parser.parse_args()
    
    requireRoot()
    buildProject(args.arch, args.json_path)

    