#!/usr/bin/env python3
import sys
import json5
import argparse
import subprocess
import os
import stat
import shutil
import datetime
import asteval
import math
import re

path_output = "output"
path_temp = ".temp"
path_logs = os.path.join(path_temp, "logs")
path_build = os.path.join(path_temp, "build")
path_mount = os.path.join(path_temp, "mount")
path_mount2 = os.path.join(path_temp, "mount2")
path_temp_temp = os.path.join(path_temp, "temp")

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

VERSION = [0, 1, 0]

def formatVersion(version):
    return '.'.join(str(n) for n in version)

def checkVersion(project):
    if not "min-syslbuild-version" in project:
        return True
    
    minVersion = project["min-syslbuild-version"]

    for index, vernum in enumerate(VERSION):
        if vernum > minVersion[index]:
            return True
        elif vernum < minVersion[index]:
            return False
    
    return True

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

def getSize(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    
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

def calcSize(sizeLitteral, folderOrFilelist):
    if isinstance(sizeLitteral, (int, float)):
        return math.ceil(sizeLitteral)
    
    if "auto" in sizeLitteral:
        if folderOrFilelist:
            contentSize = 0
            if isinstance(folderOrFilelist, list):
                for path in folderOrFilelist:
                    contentSize += getSize(path)
            else:
                contentSize = getSize(folderOrFilelist)
            
            evalStr = sizeLitteral.replace("auto", str(contentSize))
            result = aeval(evalStr)
            return math.ceil(result)
        else:
            return 0
    
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

def needExport(item):
    return readBool(item, "export")

def getItemPath(item):
    if needExport(item):
        os.makedirs(path_output, exist_ok=True)
        path = pathConcat(path_output, item["name"])
    else:
        os.makedirs(path_build, exist_ok=True)
        path = pathConcat(path_build, item["name"])
    
    return path

def deleteDirectory(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)

def deleteAny(path):
    if os.path.isdir(path):
        deleteDirectory(path)
    else:
        os.remove(path)

def getTempFolder(subdirectory):
    path = pathConcat(path_temp_temp, subdirectory)
    deleteDirectory(path)
    os.makedirs(path, exist_ok=True)

    return path

def getItemFolder(item):
    path = getItemPath(item)
    deleteDirectory(path)
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

def buildExecute(cmd, checkValid=True, input_data=None):
    buildLog(f"Execute command: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    if process.stdin:
        if input_data:
            buildLog(f"With input: {input_data}")
            process.stdin.write(input_data)
        process.stdin.close()

    output_lines = []
    for line in process.stdout:
        buildLog(line.rstrip(), True)
        output_lines.append(line)

    process.stdout.close()
    returncode = process.wait()

    if returncode != 0 and checkValid:
        buildLog("failed to build")
        sys.exit(1)

    return "\n".join(output_lines)

def buildItemLog(item, comment="Building item ---------------- "):
    buildLog(f"{comment}{item["__item_index"]}/{item["__items_count"]} {item["type"]} ({item["name"]}){" (export)" if readBool(item, "export") else ""}")

def makeChmod(path, chmodList):
    for chmodAction in chmodList:
        cmd = ["chmod"]
        if chmodAction[2]:
            cmd.append("-R")
        cmd.append(chmodAction[1])
        cmd.append(pathConcat(path, chmodAction[0]))
        buildExecute(cmd)

def chownStr(uid, gid):
    chownString = ""
    
    if uid:
        chownString += str(uid)
    
    if gid:
        chownString += ":" + str(gid)
    
    return chownString

def makeChown(path, chownList):
    for chownAction in chownList:
        cmd = ["chown"]
        if chownAction[3]:
            cmd.append("-R")
        cmd.append(chownStr(chownAction[1], chownAction[2]))
        cmd.append(pathConcat(path, chownAction[0]))
        buildExecute(cmd)

debianKernelArchitectureAliases = {
    "i386": "686"
}

def getDebianKernelName(kernelType):
    kernelName = "linux-image-"
    if kernelType == "default":
        pass
    elif kernelType == "realtime":
        kernelName += "rt-"
    else:
        buildLog(f"Unknown kernel type: {kernelType}")
        sys.exit(1)

    kernelName += debianKernelArchitectureAliases.get(architecture, architecture)

    return kernelName

def makeAllFilesExecutable(path):
    for entry in os.scandir(path):
        if entry.is_file():
            st = os.stat(entry.path)
            os.chmod(entry.path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def buildDebian(item):
    buildItemLog(item)

    includeList = item.get("include", [])
    if "kernel" in item:
        includeList.append(getDebianKernelName(item["kernel"]))

    include_arg = "--include=" + ",".join(includeList) if includeList else None
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
    if "hook-directory" in item:
        makeAllFilesExecutable(item["hook-directory"])
        cmd.append(f"--hook-directory={item["hook-directory"]}")
    buildExecute(cmd)

def downloadFile(url, path):
    buildLog(f"Downloading file ({url}): {path}")
    buildExecute(["wget", "-O", path, url])

def buildDownload(item):
    downloadFile(item["url"], getItemPath(item))

def changeAccessRights(path, changeRights):
    buildExecute(["chmod", "-R", changeRights[2], path])
    buildExecute(["chown", "-R", chownStr(changeRights[0], changeRights[1]), path])

def copyItemFiles(fromPath, toPath, changeRights=None):
    if os.path.isdir(fromPath):
        os.makedirs(toPath, exist_ok=True)
        if changeRights:
            tempFolder = getTempFolder("changeRights")
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
    # buildExecute(["truncate", "-s", str(size), path])

def formatFilesystem(path, item):
    fs_type = item["fs_type"]
    cmd = [f"mkfs.{fs_type}"]

    if "fs_arg" in item:
        cmd.append(item["fs_arg"])
    
    if "label" in item:
        if "fat" in fs_type:
            cmd.append("-n")
        else:
            cmd.append("-L")
        cmd.append(item["label"])

    if "fsid" in item:
        if "fat" in fs_type:
            cmd.append("-i")
        else:
            cmd.append("-U")
        cmd.append(item["fsid"])
    
    cmd.append(path)
    buildExecute(cmd)

def recursionUmount(path):
    path = os.path.abspath(path)
    with open("/proc/self/mounts") as f:
        mounts = [line.split()[1] for line in f]
    mounts = [m.replace("\\040", " ") for m in mounts if m.startswith(path)]
    for m in sorted(mounts, key=len, reverse=True):
        subprocess.run(["umount", "-l", m], check=False)

mountLoops = {}

def mountFilesystem(img_path, mount_path, offset=None):
    mount_path = os.path.normpath(mount_path)
    os.makedirs(mount_path, exist_ok=True)

    result = subprocess.run(["losetup", "-f"], capture_output=True, text=True, check=True)
    loop_device = result.stdout.strip()

    losetup_cmd = ["losetup", loop_device, img_path]
    if offset:
        losetup_cmd.insert(2, f"-o {offset}")
    buildExecute(losetup_cmd)

    buildExecute(["mount", loop_device, mount_path])    
    mountLoops[mount_path] = loop_device

def umountFilesystem(mount_path):
    mount_path = os.path.normpath(mount_path)
    loop_device = mountLoops.get(mount_path)
    if loop_device:
        del mountLoops[mount_path]

    if os.path.exists(mount_path):
        buildExecute(["umount", mount_path], False)
        if loop_device:
            buildExecute(["losetup", "-d", loop_device])
        deleteDirectory(mount_path)

def buildDirectory(item):
    buildItemLog(item)
    buildDirectoryPath = getItemFolder(item)

    if "directories" in item:
        for directoryName in item["directories"]:
            directoryPath = pathConcat(buildDirectoryPath, directoryName)
            buildLog(f"Create empty directory: {directoryPath}")
            os.makedirs(directoryPath, exist_ok=True)

    if "items" in item:
        for itemObj in item["items"]:
            itemPath = findItem(itemObj[0])
            outputPath = pathConcat(buildDirectoryPath, itemObj[1])
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
        makeChmod(buildDirectoryPath, item["chmod"])

    if "chown" in item:
        makeChown(buildDirectoryPath, item["chown"])

    if "delete" in item:
        for deletePath in item["delete"]:
            deleteAny(pathConcat(buildDirectoryPath, deletePath))

def findDirectory(item):
    if not "source" in item:
        return None

    dirpath = findItem(item["source"])
    if not os.path.isdir(dirpath):
        buildLog(f"Item \"{dirpath}\" is not a directory")
        sys.exit(1)
    return dirpath

def buildTar(item):
    tar_files = findDirectory(item)
    tar_path = getItemPath(item)

    if readBool(item, "gz"):
        buildExecute(["tar", "-czf", tar_path, "-C", tar_files, "."])
    else:
        buildExecute(["tar", "-cf", tar_path, "-C", tar_files, "."])

def buildFilesystem(item):
    buildItemLog(item)
    fs_files = findDirectory(item)

    fs_path = getItemPath(item)
    allocateFile(fs_path, calcSize(item['size'], fs_files))

    if "fs_type" in item:
        formatFilesystem(fs_path, item)

    if fs_files:
        mountFilesystem(fs_path, path_mount)
        copyItemFiles(fs_files, path_mount)
        umountFilesystem(path_mount)

parititionTypesList_gpt = {
    "linux": "0FC63DAF-8483-4772-8E79-3D69D8477DE4",
    "swap": "0657FD6D-A4AB-43C4-84E5-0933C84B4F4F",
    "efi": "C12A7328-F81F-11D2-BA4B-00A0C93EC93B",
    "bios": "21686148-6449-6E6F-744E-656564454649"
}

parititionTypesList_dos = {
    "linux": "83",
    "swap": "82",
    "efi": "ef"
}

def getParititionType(item, partitionType):
    if item["partitionTable"] == "gpt":
        return parititionTypesList_gpt[partitionType]
    else:
        return parititionTypesList_dos[partitionType]

defaultGrubTargets_efi = {
    "amd64": "x86_64-efi",
    "i386": "i386-efi",
    "arm64": "arm64-efi",
    "armhf": "arm-efi",
    "armel": "arm-efi"
}

defaultGrubTargets_bios = {
    "amd64": "i386-pc",
    "i386": "i386-pc"
}

def getGrubTarget(item, efi):
    bootloaderInfo = item["bootloader"]
    if "target" in bootloaderInfo:
        return bootloaderInfo["target"]

    target = None
    if efi:
        target = defaultGrubTargets_efi.get(architecture)
    else:
        target = defaultGrubTargets_bios.get(architecture)

    if target == None:
        buildLog(f"Unknown grub target for {architecture} ({"efi" if efi else "bios"})")
        sys.exit(1)

    return target

def installBootloader(item, path, partitionsOffsets):
    bootloaderInfo = item["bootloader"]
    bootloaderType = bootloaderInfo["type"]

    if bootloaderType == "grub":
        efi = False

        mountFilesystem(path, path_mount, partitionsOffsets[bootloaderInfo["boot"]])
        if "esp" in bootloaderInfo:
            mountFilesystem(path, path_mount2, partitionsOffsets[bootloaderInfo["esp"]])
            efi = True

        bootDirectory = pathConcat(path_mount, "boot")
        os.makedirs(bootDirectory, exist_ok=True)

        modulesString = ""
        if "modules" in bootloaderInfo:
            modulesString = " ".join(bootloaderInfo["modules"])

        if efi:
            buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, True)}", f"--boot-directory={bootDirectory}", path, f"--efi-directory={path_mount2}", "--removable"])
        else:
            buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, False)}", f"--boot-directory={bootDirectory}", path])

        if "config" in bootloaderInfo:
            os.makedirs(pathConcat(bootDirectory, "grub"), exist_ok=True)
            copyItemFiles(findItem(bootloaderInfo["config"]), pathConcat(bootDirectory, "grub", "grub.cfg"), [0, 0, "0000"])

        umountFilesystem(path_mount)

        if efi:
            umountFilesystem(path_mount2)
    else:
        buildLog("Unknown bootloader type")
        sys.exit(1)

def buildFullDiskImage(item):
    # allocate file
    path = getItemPath(item)
    partitionsPaths = []
    partitionsSizes = []
    for partition in item["partitions"]:
        parititionPath = findItem(partition[0])
        partitionsPaths.append(parititionPath)
        partitionsSizes.append(getSize(parititionPath))
    allocateFile(path, calcSize(item['size'], partitionsPaths))

    # make paritition table
    partitionTable = f"label: {item["partitionTable"]}"
    for i, partition in enumerate(item["partitions"]):
        partitionTable += f"\nsize={math.ceil(partitionsSizes[i] / 1024 / 1024)}MiB, type={getParititionType(item, partition[1])}"

    buildExecute(["sfdisk", path], False, partitionTable)

    # apply partitions
    resultPartitionTable = json5.loads(buildExecute(["sfdisk", "-J", path]))
    resultPartitions = resultPartitionTable["partitiontable"]["partitions"]
    resultSectorsize = resultPartitionTable["partitiontable"]["sectorsize"]

    partitionsOffsets = []
    for i, paritition in enumerate(resultPartitions):
        start_sector = paritition["start"]
        partitionsOffsets.append(start_sector * resultSectorsize)
        buildExecute([
            "dd",
            f"if={partitionsPaths[i]}",
            f"of={path}",
            f"bs={resultSectorsize}",
            "seek=" + str(start_sector),
            "conv=notrunc"
        ])

    # install bootloader
    if "bootloader" in item:
        installBootloader(item, path, partitionsOffsets)

def buildUnknown(item):
    buildLog(f"unknown build item type: {item["type"]}")
    sys.exit(1)

buildActions = {
    "debian": buildDebian,
    "download": buildDownload,
    "directory": buildDirectory,
    "tar": buildTar,
    "filesystem": buildFilesystem,
    "full-disk-image": buildFullDiskImage
}

def buildItems(builditems):
    exported = []
    for item in builditems:
        buildActions.get(item["type"], buildUnknown)(item)
        if needExport(item):
            exported.append(item)
    return exported

def showProjectInfo(projectData):
    buildLog(f"Project info:")

    if "min-syslbuild-version" in projectData:
        buildLog(f"Minimal syslbuild: {formatVersion(projectData["min-syslbuild-version"])}")
    
    buildLog(";")

def buildProject(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)

    showProjectInfo(projectData)

    if not checkVersion(projectData):
        buildLog(f"the project requires at least the syslbuild {formatVersion(projectData["min-syslbuild-version"])} version. you have {formatVersion(VERSION)} installed")
        sys.exit(1)

    recursionUmount(path_temp)

    umountFilesystem(path_mount)
    umountFilesystem(path_mount2)
    deleteDirectory(path_output)
    deleteDirectory(path_build)
    deleteDirectory(path_temp_temp)

    builditems = projectData["builditems"]
    i = 0
    while i < len(builditems):
        builditem = builditems[i]
        if "architectures" in builditem and not architecture in builditem["architectures"]:
            del builditems[i]
        else:
            i += 1

    for index, item in enumerate(builditems):
        item["__item_index"] = index + 1
        item["__items_count"] = len(builditems)

    buildLog("Item list:")
    for item in builditems:
        buildItemLog(item, "")
    buildLog(";")
    
    exported = buildItems(builditems)
    buildLog("The build was successful. export list:")
    for exportedItem in exported:
        buildItemLog(exportedItem, "Exported: ")
    buildLog(";")

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

    buildLog("Syslbuild info:")
    buildLog(f"Syslbuild version: {formatVersion(VERSION)}")
    buildLog(";")
    buildProject(args.json_path)

    