#!/usr/bin/env python3
import sys
import json5
import argparse
import subprocess
import os
import shutil
import datetime
import asteval
import math
import re

path_output = "output"
path_temp = ".temp"
path_logs = os.path.join(path_temp, "logs")
path_build = os.path.join(path_temp, "build")
path_build_process = os.path.join(path_temp, "build_process")
path_build_temp = os.path.join(path_temp, "build_temp")

aeval = asteval.Interpreter()

SIZE_UNITS = {
    "":   1,
    "B":  1,
    "K":  1024,
    "KB": 1024,
    "M":  1024**2,
    "MB": 1024**2,
    "G":  1024**3,
    "GB": 1024**3,
    "T":  1024**4,
    "TB": 1024**4,
}

def _pathConcat(path1, path2):
    path2_rel = os.path.relpath(path2, "/") if os.path.isabs(path2) else path2
    full_path = os.path.normpath(os.path.join(path1, path2_rel))
    abs_path1 = os.path.abspath(path1)
    abs_full = os.path.abspath(full_path)
    if not abs_full.startswith(abs_path1):
        buildLog(f"Building outside the sandbox: {path1} | {path2}")
        sys.exit(1)

    return full_path

def pathConcat(*paths):
    if not paths:
        return ""
    
    full_path = paths[0]
    for p in paths[1:]:
        full_path = _pathConcat(full_path, p)
    
    return full_path

def buildLog(logstr, quiet=False):
    if not quiet:
        logstr = f"-------- SYSLBUILD: {logstr}"
    
    print(logstr)
    log_file.write(logstr + "\n")
    log_file.flush()

def getFolderSize(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except FileNotFoundError:
                pass
    return total

def splitNumberUnit(s):
    match = re.match(r"([\d\.]+)([a-zA-Z]*)", s)
    if match:
        number, unit = match.groups()
        return float(number), unit.upper()
    return 0, ""

def calcSize(sizeLitteral, folder):
    if isinstance(sizeLitteral, (int, float)):
        return math.ceil(sizeLitteral)
    
    if "auto" in sizeLitteral:
        folderSize = getFolderSize(folder)
        evalStr = sizeLitteral.replace("auto", str(folderSize))
        result = aeval(evalStr)
        return math.ceil(result)
    
    number, unit = splitNumberUnit(sizeLitteral)

    if not unit in SIZE_UNITS:
        buildLog(f"Unknown size unit: {unit}")
        sys.exit(1)

    return math.ceil(number * SIZE_UNITS[unit])

def getLogFile():
    os.makedirs(path_logs, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"build_{architecture}_{timestamp}.log"
    filepath = pathConcat(path_logs, filename)

    print(f"Log path: {filepath}")
    return open(filepath, "w")

def readBool(tbl, name):
    if name in tbl:
        return bool(tbl[name])
    
    return False

def getItemPath(item):
    if readBool(item, "export"):
        path = pathConcat(path_output, item["name"])
    else:
        path = pathConcat(path_build, item["name"])
    
    return path

def getTempPath(item, subdirectory):
    path = pathConcat(path_build_process, subdirectory, item["name"])
    deleteDirectory(path)
    os.makedirs(path, exist_ok=True)

    return path

def deleteDirectory(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)

def deleteAny(path):
    if os.path.isdir(path):
        deleteDirectory(path)
    else:
        os.remove(path)

def getAnyTempPath(subdirectory):
    path = pathConcat(path_build_temp, subdirectory)
    deleteDirectory(path)
    os.makedirs(path, exist_ok=True)

    return path

def getItemFolder(item):
    path = getItemPath(item)
    os.makedirs(path, exist_ok=True)
    
    return path

def findItem(itemName):
    path = pathConcat(path_build, itemName)
    if os.path.exists(path):
        return path
    else:
        path = pathConcat(path_output, itemName)
        if os.path.exists(path):
            return path
        else:
            path = pathConcat(".", itemName)
            if os.path.exists(path):
                return path

    buildLog(f"Failed to find item: {itemName}")
    sys.exit(1)

def isUserItem(itemName):
    path = pathConcat(path_build, itemName)
    if os.path.exists(path):
        return False
    else:
        path = pathConcat(path_output, itemName)
        if os.path.exists(path):
            return False
        else:
            path = pathConcat(".", itemName)
            if os.path.exists(path):
                return True

    return False

def buildExecute(cmd):
    buildLog(f"execute command: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        buildLog(line.rstrip(), True)

    process.stdout.close()
    returncode = process.wait()

    if returncode != 0:
        buildLog("failed to build")
        sys.exit(1)

def buildItemLog(item):
    buildLog(f"building item {item["__item_index"]}/{item["__items_count"]} {item["type"]} ({item["name"]})")

def makeChmod(path, chmodList):
    for chmodAction in chmodList:
        cmd = ["chmod"]
        if chmodAction[2]:
            cmd.append("-R")
        cmd.append(chmodAction[1])
        cmd.append(pathConcat(path, chmodAction[0]))
        buildExecute(cmd)

def buildDebian(item):
    buildItemLog(item)

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
        getItemFolder(item),
        item["url"]
    ]
    buildExecute(cmd)

def changeAccessRights(path, changeRights):
    buildExecute(["chmod", "-R", changeRights[2], path])
    buildExecute(["chown", "-R", str(changeRights[0]) + ":" + str(changeRights[1]), path])

def copyItemFiles(fromPath, toPath, changeRights=None):
    if os.path.isdir(fromPath):
        os.makedirs(toPath, exist_ok=True)
        if changeRights:
            tempFolder = getAnyTempPath("changeRights")
            buildExecute(["cp", "-a", fromPath + "/.", tempFolder])
            changeAccessRights(tempFolder, changeRights)
            buildExecute(["cp", "-a", tempFolder + "/.", toPath])
        else:
            buildExecute(["cp", "-a", fromPath + "/.", toPath])
    else:
        shutil.copy2(fromPath, toPath)
        if changeRights:
            changeAccessRights(toPath, changeRights)

def allocateFile(path, size):
    buildLog(f"Allocation file with size {size}: {path}")

    bs = 1024 * 1024
    count = math.ceil(size / bs)

    buildExecute([
        "dd",
        "if=/dev/zero",
        f"of={path}",
        "bs=" + str(bs),
        "count=" + str(count)
    ])
    buildExecute(["truncate", "-s", str(size), path])

def buildFilesystem(item):
    buildItemLog(item)

    fs_files = getTempPath(item, "fs_files")
    fs_path = getItemPath(item)

    if "directories" in item:
        for folderName in item["directories"]:
            folderPath = pathConcat(fs_files, folderName)
            buildLog(f"Create empty folder: {folderPath}")
            os.makedirs(folderPath, exist_ok=True)

    if "items" in item:
        for itemObj in item["items"]:
            itemPath = findItem(itemObj[0])
            outputPath = pathConcat(fs_files, itemObj[1])
            buildLog(f"Copy item to filesystem: {itemPath} > {outputPath}")

            changeRights = None
            if len(itemObj) >= 3:
                changeRights = itemObj[2]
            
            if not changeRights and isUserItem(itemObj[0]):
                changeRights = [0, 0, "0000"]
            
            if changeRights:
                buildLog(f"With custom rights: {changeRights}")
            
            copyItemFiles(itemPath, outputPath, changeRights)

    if "chmod" in item:
        makeChmod(fs_files, item["chmod"])

    allocateFile(fs_path, calcSize(item['size'], fs_files))     

def buildUnknown(item):
    buildLog(f"unknown build item type: {item["type"]}")
    sys.exit(1)

buildActions = {
    "debian": buildDebian,
    "filesystem": buildFilesystem
}

def buildItems(builditems):
    for item in builditems:
        buildActions.get(item["type"], buildUnknown)(item)

def buildProject(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)

    deleteDirectory(path_output)
    deleteDirectory(path_build)
    deleteDirectory(path_build_process)
    deleteDirectory(path_build_temp)

    builditems = projectData["builditems"]

    for index, item in enumerate(builditems):
        item["__item_index"] = index + 1
        item["__items_count"] = len(builditems)
    
    buildItems(builditems)

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
    
    architecture = args.arch
    log_file = getLogFile()
    buildProject(args.json_path)

    