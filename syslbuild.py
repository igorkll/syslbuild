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
import hashlib
import urllib.parse
import platform

path_output = "output"
path_temp = ".temp"
path_temp_temp = os.path.join(path_temp, "temp")
path_logs = os.path.join(path_temp, "logs")
path_mount = os.path.join(path_temp, "mount")
path_mount2 = os.path.join(path_temp, "mount2")
path_temp_kernel_sources = os.path.join(path_temp, "downloaded_kernel_sources")

def loadTempPaths():
    global path_temp_architecture
    global path_build
    global path_build_checksums
    global path_temp_cache_pacman
    global path_temp_pacman_conf
    global path_temp_kernel_build
    
    path_temp_architecture = os.path.join(path_temp, architecture)
    os.makedirs(path_temp_architecture, exist_ok=True)
    
    path_build = os.path.join(path_temp_architecture, "build")
    path_build_checksums = os.path.join(path_temp_architecture, "build_checksums")
    path_temp_cache_pacman = os.path.join(path_temp_architecture, "pacman")
    path_temp_pacman_conf = os.path.join(path_temp_architecture, "pacman.conf")
    path_temp_kernel_build = os.path.join(path_temp_architecture, "last_kernel_build")

aeval = asteval.Interpreter()

DEFAULT_RIGHTS = [0, 0, "0000"]

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

def makedirsChangeRights(path, changeRights=None):
    if not os.path.exists(path):
        os.makedirs(path)
        changeAccessRights(path, changeRights or DEFAULT_RIGHTS)

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
        path = pathConcat(path_output_target, item["name"])
    else:
        os.makedirs(path_build, exist_ok=True)
        path = pathConcat(path_build, item["name"])
    
    return path

def getCustomItemPath(item, nameName, exportName):
    if readBool(item, exportName):
        path = pathConcat(path_output_target, item[nameName])
    else:
        os.makedirs(path_build, exist_ok=True)
        path = pathConcat(path_build, item[nameName])
    
    return path

def getItemChecksumPath(item):
    os.makedirs(path_build_checksums, exist_ok=True)
    return pathConcat(path_build_checksums, item["name"])

def deleteDirectory(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def deleteFile(path):
    if os.path.exists(path):
        os.remove(path)

def deleteAny(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

def getTempPath(subpath):
    os.makedirs(path_temp_temp, exist_ok=True)
    return pathConcat(path_temp_temp, subpath)

def getTempFolder(subdirectory):
    path = getTempPath(subdirectory)
    deleteDirectory(path)
    os.makedirs(path, exist_ok=True)
    return path

def getItemFolder(item):
    path = getItemPath(item)
    deleteDirectory(path)
    os.makedirs(path, exist_ok=True)
    
    return path

def getCustomItemFolder(item, nameName, exportName):
    path = getCustomItemPath(item, nameName, exportName)
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

def buildExecute(cmd, checkValid=True, input_data=None, cwd=None):
    if cwd != None:
        buildLog(f"Execute command from directory ({cwd}): {cmd}")
    else:
        buildLog(f"Execute command: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=cwd
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

def buildRawExecute(cmd, checkValid=True, cwd=None):
    if cwd != None:
        buildLog(f"Execute raw command from directory ({cwd}): {cmd}")
    else:
        buildLog(f"Execute raw command: {cmd}")
    
    process = subprocess.Popen(
        cmd,
        shell=True,             
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=cwd
    )

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

def buildItemLog(item, comment=None, comment2=None, hideExport=False):
    if comment is None:
        comment = "Building item ---------------- "
    
    if comment2 is None:
        comment2 = ""
    
    buildLog(f"{comment}{item["__item_index"]}/{item["__items_count"]} {item["type"]} ({item["name"]}){" (export)" if (readBool(item, "export") and not hideExport) else ""}{comment2}")

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

def emptyFile(path):
    with open(path, "w") as f:
        pass

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

minDebianPackages = [
    "base-files",
    "libc6",
    "libc-bin",
    "libtinfo6",
    "dash",
    "diffutils",
    "coreutils",
    "dpkg"
]

def buildDebian(item):
    includeList = item.get("include", [])
    if "kernel" in item:
        includeList.append(getDebianKernelName(item["kernel"]))
    
    variant = item["variant"]
    if variant == "_min":
        variant = "custom"
        includeList += minDebianPackages

    include_arg = "--include=" + ",".join(includeList) if includeList else None
    # exclude_arg = "--exclude=" + ",".join(item["exclude"]) if item.get("exclude") else None

    cmd = ["mmdebstrap", "--arch", architecture, "--variant", variant]
    if include_arg: cmd.append(include_arg)
    # if exclude_arg: cmd.append(exclude_arg)
    cmd += [
        "--aptopt=Acquire::Check-Valid-Until false",
        "--aptopt=Acquire::AllowInsecureRepositories true",
        "--aptopt=APT::Get::AllowUnauthenticated true",
        item["suite"],
        getItemFolder(item),
        item["url"]
    ]
    cmd.append(f"--customize-hook=echo hostname > \"$1/etc/hostname\"")
    cmd.append(f"--customize-hook=rm \"$1\"/etc/resolv.conf")
    if "hook-directory" in item:
        makeAllFilesExecutable(item["hook-directory"])
        cmd.append(f"--hook-directory={item["hook-directory"]}")
    buildExecute(cmd)

def makePacmanConfig(pacman_conf):
    lines = []

    for section, values in pacman_conf.items():
        lines.append(f"[{section}]")
        for key, val in values.items():
            lines.append(f"{key} = {val}")
        lines.append("")

    with open(path_temp_pacman_conf, "w") as f:
        f.write("\n".join(lines))

pacman_architectures_names = {
    "amd64": "x86_64"
}

def prepairPacman(pacman_conf):
    os.makedirs(pacman_conf["options"]["CacheDir"], exist_ok=True)

def makeExtendedPacmanConfig(pacman_conf):
    if "options" not in pacman_conf:
        pacman_conf["options"] = {}
    
    if "_auto" in pacman_conf:
        pacman_conf["core"] = pacman_conf["_auto"]
        pacman_conf["extra"] = pacman_conf["_auto"]
        pacman_conf["community"] = pacman_conf["_auto"]
        del pacman_conf["_auto"]

    if "Architecture" not in pacman_conf["options"]:
        pacman_conf["options"]["Architecture"] = pacman_architectures_names[architecture]
    
    if "CacheDir" not in pacman_conf["options"]:
        pacman_conf["options"]["CacheDir"] = path_temp_cache_pacman
    
    makePacmanConfig(pacman_conf)
    prepairPacman(pacman_conf)

def archLinuxBuild(item):
    makeExtendedPacmanConfig(item["pacman_conf"])
    root_path = getItemFolder(item)

    cmd = ["pacstrap", "-M", "-C", path_temp_pacman_conf, root_path]
    if item.get("withoutDependencies", False):
        cmd.append("--nodeps")
    cmd += item.get("include", [])

    buildExecute(cmd)

def archLinuxPackage(item):
    makeExtendedPacmanConfig(item["pacman_conf"])
    root_path = getItemFolder(item)

    cmd = ["pacman", "-r", root_path, "-C", path_temp_pacman_conf, "-Sy", "--noconfirm"]
    if item.get("withoutDependencies", False):
        cmd.append("--nodeps")
    cmd.append(item["package"])

    buildExecute(cmd)

def grubIsoImage(item):
    tempPath = getTempFolder("isotemp")

    bootDirectory = pathConcat(tempPath, "boot")
    makedirsChangeRights(bootDirectory)

    grubDirectory = pathConcat(bootDirectory, "grub")
    makedirsChangeRights(grubDirectory)

    if "kernel" in item:
        copyItemFiles(findItem(item["kernel"]), pathConcat(bootDirectory, "vmlinuz"), DEFAULT_RIGHTS)

    if "initramfs" in item:
        copyItemFiles(findItem(item["initramfs"]), pathConcat(bootDirectory, "initrd.img"), DEFAULT_RIGHTS)

    grub_cfg_path = pathConcat(grubDirectory, "grub.cfg")
    if "config" in item:
        copyItemFiles(findItem(item["config"]), grub_cfg_path, DEFAULT_RIGHTS)
    else:
        with open(grub_cfg_path, "w") as f:
            if "kernel" in item:
                if item.get("show_boot_process", False):
                    f.write("echo \"Loading linux kernel...\"\n")
                f.write("linux /boot/vmlinuz " + item.get("kernel_args", "") + "\n")

            if "initramfs" in item:
                if item.get("show_boot_process", False):
                    f.write("echo \"Loading initramdisk...\"\n")
                f.write("initrd /boot/initrd.img\n")

            if item.get("show_boot_process", False):
                f.write("echo \"Booting...\"\n")
            f.write("boot\n")
        changeAccessRights(grub_cfg_path, DEFAULT_RIGHTS)

    cmd = ["grub-mkrescue", "-o", getItemPath(item), tempPath]
    if "modules" in item:
        cmd.append("--modules=\"" + " ".join(item["modules"]) + "\"")
    buildExecute(cmd)

def unpackInitramfs(item):
    initramfs = os.path.abspath(findItem(item["initramfs"]))
    folder = getItemFolder(item)

    buildRawExecute(f"{item.get("decompressor", "cat")} \"{initramfs}\" | cpio -idmv", True, folder)



def downloadFile(url, path):
    buildLog(f"Downloading file ({url}): {path}")
    buildExecute(["wget", "-O", path, url])

def buildDownload(item):
    downloadFile(item["url"], getItemPath(item))

def changeAccessRights(path, changeRights):
    if len(changeRights) >= 3 and changeRights[2]:
        buildExecute(["chmod", "-R", changeRights[2], path])
    
    chownString = chownStr(changeRights[0], changeRights[1])
    if chownString:
        buildExecute(["chown", "-R", chownString, path])

def copyItemFiles(fromPath, toPath, changeRights=None):
    if os.path.isdir(fromPath):
        makedirsChangeRights(toPath)
        if changeRights:
            tempFolder = getTempFolder("changeRights")
            buildExecute(["cp", "-a", fromPath + "/.", tempFolder])
            changeAccessRights(tempFolder, changeRights)
            buildExecute(["cp", "-a", tempFolder + "/.", toPath])
        else:
            buildExecute(["cp", "-a", fromPath + "/.", toPath])
    else:
        # this is necessary to correctly overwrite the symlink that links to a working file in the host system.
        deleteAny(toPath)

        file_dir = os.path.dirname(toPath)
        if not os.path.isdir(file_dir):
            makedirsChangeRights(file_dir)

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
    buildDirectoryPath = getItemFolder(item)

    if "directories" in item:
        for directoryData in item["directories"]:
            directoryPath = pathConcat(buildDirectoryPath, directoryData[0])
            changeRights = directoryData[1] or DEFAULT_RIGHTS

            buildLog(f"Create empty directory: {directoryPath} {changeRights}")
            makedirsChangeRights(directoryPath, changeRights)

    if "items" in item:
        for itemObj in item["items"]:
            itemPath = findItem(itemObj[0])
            outputPath = pathConcat(buildDirectoryPath, itemObj[1])
            buildLog(f"Copy item to filesystem: {itemPath} > {outputPath}")

            changeRights = None
            if len(itemObj) >= 3:
                changeRights = itemObj[2]
            
            if not changeRights and isUserItem(itemObj[0]):
                changeRights = DEFAULT_RIGHTS
            
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
        makedirsChangeRights(bootDirectory)

        modulesString = ""
        if "modules" in bootloaderInfo:
            modulesString = " ".join(bootloaderInfo["modules"])

        if efi:
            buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, True)}", f"--boot-directory={bootDirectory}", path, f"--efi-directory={path_mount2}", "--removable"])
            if readBool(bootloaderInfo, "efiAndBios"):
                buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, False)}", path])
        else:
            buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, False)}", f"--boot-directory={bootDirectory}", path])

        if "config" in bootloaderInfo:
            makedirsChangeRights(pathConcat(bootDirectory, "grub"))
            copyItemFiles(findItem(bootloaderInfo["config"]), pathConcat(bootDirectory, "grub", "grub.cfg"), DEFAULT_RIGHTS)

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

def getSourceDirectory(item):
    source = findItem(item["source"])
    if not os.path.isdir(source):
        buildLog("Source item is not a directory")
        sys.exit(1)
    return source

def buildFromDirectory(item):
    path = getItemPath(item)
    source = getSourceDirectory(item)
    sourcePath = pathConcat(source, item["path"])
    copyItemFiles(sourcePath, path, [0, 0, "0755"])

gccNames = {
    "amd64": "x86_64-linux-gnu",
    "i386": "i686-linux-gnu",
    "arm64": "aarch64-linux-gnu",
    "armhf": "arm-linux-gnueabihf",
    "armel": "arm-linux-gnueabi"
}

def collect_sources(item):
    sources = []
    dirs = item.get("sources-dirs", [])
    recursive = item.get("sources-dirs-recursive", False)
    exts = item.get("sources-dirs-extensions", None)  # optional. if this is not specified, syslbuild will take all files.

    for d in dirs:
        if recursive:
            for root, _, files in os.walk(d):
                for f in files:
                    if exts is None or any(f.endswith(ext) for ext in exts):
                        sources.append(os.path.join(root, f))
        else:
            for f in os.listdir(d):
                full = os.path.join(d, f)
                if os.path.isfile(full) and (exts is None or any(f.endswith(ext) for ext in exts)):
                    sources.append(full)

    return sources

def gccBuild(item):
    buildExecute(
        [gccNames[architecture] + "-gcc"] +
        item.get("CFLAGS", []) +
        item.get("sources", collect_sources(item)) +
        item.get("LDFLAGS", []) +
        ["-o", getItemPath(item)]
    )

def buildInitramfs(item):
    source = getSourceDirectory(item)
    realOutputPath = os.path.abspath(getItemPath(item))
    
    if "compressor" in item:
        outputPath = os.path.abspath(getTempPath("temp.cpio"))
    else:
        outputPath = realOutputPath

    buildRawExecute(f"find . -print0 | cpio --null -ov --format=newc > \"{outputPath}\"", True, source)

    if "compressor" in item:
        buildRawExecute(f"{item["compressor"]} < \"{outputPath}\" > \"{realOutputPath}\"", True)

def get_file_extension(url):
    path = urllib.parse.urlparse(url).path
    filename = os.path.basename(path)

    double_exts = ['.tar.gz', '.tar.xz', '.tar.bz2', '.tar.Z', '.tar.lz']

    for ext in double_exts:
        if filename.endswith(ext):
            return ext

    _, ext = os.path.splitext(filename)
    return ext

def downloadKernel(url, unpacker):
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    kernel_sources = pathConcat(path_temp_kernel_sources, url_hash)
    kernel_sources_downloaded_flag = pathConcat(path_temp_kernel_sources, url_hash + ".downloaded")
    kernel_sources_archive = pathConcat(path_temp_kernel_sources, url_hash + get_file_extension(url))

    if not os.path.isdir(kernel_sources) or not os.path.isfile(kernel_sources_downloaded_flag):
        os.makedirs(kernel_sources, exist_ok=True)
        downloadFile(url, kernel_sources_archive)
        buildRawExecute(unpacker % (kernel_sources_archive, kernel_sources))
        emptyFile(kernel_sources_downloaded_flag)
    
    return kernel_sources

def copyKernel(kernel_sources):
    deleteDirectory(path_temp_kernel_build)
    os.makedirs(path_temp_kernel_build, exist_ok=True)
    copyItemFiles(kernel_sources, path_temp_kernel_build)
    return path_temp_kernel_build

def patchKernel(kernel_sources, patches):
    for patchPath in patches:
        buildRawExecute(f"patch -p1 < {os.path.abspath(findItem(patchPath))}", True, kernel_sources)

kernelArchitectures = {
    "amd64": "x86_64",
    "i386": "x86",
    "arm64": "arm64",
    "armhf": "arm",
    "armel": "arm"
}

import os
import subprocess

def set_kernel_config_parameter(config_path, param, value):
    with open(config_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    param_found = False
    for line in lines:
        if line.startswith(f"{param}=") or line.startswith(f"# {param} is not set"):
            param_found = True
            if value is None:
                new_lines.append(f"# {param} is not set\n")
            else:
                new_lines.append(f"{param}={value}\n")
        else:
            new_lines.append(line)

    if not param_found:
        if value is not None:
            new_lines.append(f"{param}={value}\n")

    with open(config_path, "w") as f:
        f.writelines(new_lines)

def update_kernel_config(kernel_sources):
    buildExecute(["make", "olddefconfig"], True, None, kernel_sources)

def modifyKernelConfig(item, kernel_sources):
    kernel_config_path = pathConcat(kernel_sources, ".config")

    if "kernel_config_changes" in item:
        for change in item["kernel_config_changes"]:
            set_kernel_config_parameter(kernel_config_path, change[0], change[1])

    if not item.get("kernel_config_disable_default_changes", False):
        # I'm disabling this for some patches to work correctly
        set_kernel_config_parameter(kernel_config_path, "CONFIG_WERROR", "n")

        set_kernel_config_parameter(kernel_config_path, "CONFIG_RD_GZIP", "y")
    
    update_kernel_config(kernel_sources)

def buildKernel(item):
    kernel_sources = copyKernel(
        downloadKernel(
            item["kernel_source_url"],
            item.get("kernel_source_unpacker", "tar -xJf %s -C %s --strip-components=1")
        )
    )

    if "patches" in item:
        patchKernel(kernel_sources, item["patches"])

    ARCH = kernelArchitectures[architecture]
    CROSS_COMPILE = gccNames[architecture]
    ARCH_STR = f"ARCH={ARCH}"
    CROSS_COMPILE_STR = f"CROSS_COMPILE={CROSS_COMPILE}-"
    buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "defconfig"], True, None, kernel_sources)

    kernel_config_path = pathConcat(kernel_sources, ".config")

    if "kernel_config" in item:
        copyItemFiles(findItem(item["kernel_config"]), kernel_config_path)

    modifyKernelConfig(item, kernel_sources)

    if "result_config_name" in item:
        buildLog(f"exporting result kernel config...")
        export_path = getCustomItemPath(item, "result_config_name", "result_config_export")
        copyItemFiles(kernel_config_path, export_path)

    buildRawExecute(f"make {ARCH_STR} {CROSS_COMPILE_STR} -j$(nproc)", True, kernel_sources)

    kernel_output_filename = item.get("kernel_output_file", "bzImage")
    kernel_output_file = pathConcat(kernel_sources, "arch", kernelArchitectures[architecture], "boot", kernel_output_filename)
    if os.path.isfile(kernel_output_file):
        copyItemFiles(kernel_output_file, getItemPath(item))
    else:
        kernel_output_file = pathConcat(kernel_sources, kernel_output_filename)
        if os.path.isfile(kernel_output_file):
            copyItemFiles(kernel_output_file, getItemPath(item))
        else:
            buildLog(f"failed to find \"{kernel_output_filename}\" kernel output file")
            sys.exit(1)

    if "modules_name" in item:
        buildLog(f"exporting modules...")
        export_path = getCustomItemFolder(item, "modules_name", "modules_export")
        buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "modules_install", f"INSTALL_MOD_PATH={os.path.abspath(export_path)}"], True, None, kernel_sources)

    if "headers_name" in item:
        buildLog(f"exporting headers...")
        export_path = getCustomItemFolder(item, "headers_name", "headers_export")
        buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "headers_install", f"INSTALL_HDR_PATH={os.path.abspath(export_path)}"], True, None, kernel_sources)

def get_host_arch():
    m = platform.machine().lower()

    if m in ("x86_64", "amd64"):
        return "amd64"
    if m in ("i386", "i686"):
        return "i386"
    if m in ("aarch64", "arm64"):
        return "arm64"
    if m.startswith("arm"):
        return "armhf"

    raise RuntimeError(f"unknown host architecture: {m}")

qemuStaticNames = {
    "amd64": "qemu-x86_64-static",
    "i386": "qemu-i386-static",
    "arm64": "qemu-aarch64-static",
    "armhf": "qemu-arm-static",
    "armel": "qemu-arm-static"
}

notNeedQemuStatic = {
    "amd64": ("i386")
}

def checkQemuStaticNeed():
    hostArchitecture = get_host_arch()
    if hostArchitecture == architecture:
        buildLog(f"the architectures of the host and the target system are the same ({architecture}) we do not use qemu-static")
        return False
    
    if hostArchitecture == "amd64" and architecture == "i386":
        buildLog(f"the host architecture ({hostArchitecture}) is compatible with the target architecture ({architecture}) we do not use qemu-static")
        return False

    buildLog(f"the host architecture ({hostArchitecture}) is NOT compatible with the target architecture ({architecture}), we use qemu-static")
    return True

def rawCrossChroot(chrootDirectory, chrootCommand):
    bindList = [
        "dev",
        "proc",
        "sys"
    ]
    
    for bindPath in bindList:
        buildRawExecute(f"mount --bind /{bindPath} \"{pathConcat(chrootDirectory, bindPath)}\"")

    boolCopyQemuStatic = checkQemuStaticNeed()
    qemuStaticName = qemuStaticNames[architecture]
    qemuStaticHostPath = f"/usr/bin/{qemuStaticName}"
    qemuStaticPath = pathConcat(chrootDirectory, "usr/bin", qemuStaticName)

    if boolCopyQemuStatic and not os.path.isfile(qemuStaticHostPath):
        buildLog(f"WARNINGL: there is no suitable version of qemu-static ({qemuStaticName}) in the host system. we are trying without it")
        boolCopyQemuStatic = False

    if boolCopyQemuStatic:
        buildLog(f"copying qemu-static ({qemuStaticName})")
        os.makedirs(os.path.dirname(qemuStaticPath), exist_ok=True)
        buildExecute(["cp", "-a", qemuStaticHostPath, qemuStaticPath])
        buildExecute(["chmod", "0755", qemuStaticPath])
        buildExecute(["chown", "0:0", qemuStaticPath])

    buildExecute(["chroot", chrootDirectory] + chrootCommand)

    if boolCopyQemuStatic:
        os.remove(qemuStaticPath)

    for bindPath in bindList:
        buildRawExecute(f"umount \"{pathConcat(chrootDirectory, bindPath)}\"")

def debianUpdateInitramfs(item):
    rawCrossChroot(findItem(item["rootfs"]), ["update-initramfs", "-c", "-k", item["kernel_version"]])

buildActions = {
    "debian": buildDebian,
    "download": buildDownload,
    "directory": buildDirectory,
    "tar": buildTar,
    "filesystem": buildFilesystem,
    "full-disk-image": buildFullDiskImage,
    "from-directory": buildFromDirectory,
    "gcc-build": gccBuild,
    "initramfs": buildInitramfs,
    "arch-linux": archLinuxBuild,
    "arch-package": archLinuxPackage,
    "grub-iso-image": grubIsoImage,
    "unpack-initramfs": unpackInitramfs,
    "kernel": buildKernel,
    "debian-update-initramfs": debianUpdateInitramfs
}

cachedBuildActions = [
    "debian"
]

def dictChecksum(tbl):
    filtered = {k: v for k, v in tbl.items() if not k.startswith("_")}
    return hashlib.md5(json5.dumps(filtered).encode('utf-8')).hexdigest()

def writeCacheChecksum(item, checksum):
    checksum_path = getItemChecksumPath(item)
    with open(checksum_path, "w") as f:
        f.write(checksum)

def isCacheValid(item, checksum):
    checksum_path = getItemChecksumPath(item)
    if os.path.exists(checksum_path):
        with open(checksum_path, "r") as f:
            return f.read() == checksum
    return False

def buildItems(builditems):
    exported = []
    for item in builditems:
        itemPath = getItemPath(item)
        checksum = dictChecksum(item)
        if item["type"] in cachedBuildActions and os.path.exists(itemPath) and (isCacheValid(item, checksum) and not args.n):
            buildItemLog(item, None, " (cache)")
        else:
            writeCacheChecksum(item, checksum)
            deleteAny(itemPath)
            buildItemLog(item)
            buildActions.get(item["type"], buildUnknown)(item)
            

        if needExport(item):
            exported.append(item)
    return exported

def showProjectInfo(projectData):
    buildLog(f"Project info:")

    if "min-syslbuild-version" in projectData:
        buildLog(f"Minimal syslbuild: {formatVersion(projectData["min-syslbuild-version"])}")
    
    buildLog(";")

def cleanup():
    recursionUmount(path_temp)
    umountFilesystem(path_mount)
    umountFilesystem(path_mount2)
    deleteDirectory(path_temp_temp)

def prepairBuild():
    global path_output_target
    path_output_target = pathConcat(path_output, architecture)
    recursionUmount(path_output_target)
    deleteDirectory(path_output_target)
    os.makedirs(path_output_target, exist_ok=True)

def forkCombine(builditem, forkbase, forkArraysCombine=False, keysBlackList=None):
    for k, v in forkbase.items():
        if not keysBlackList or k not in keysBlackList:
            if k not in builditem:
                builditem[k] = v
            elif isinstance(v, list):
                if forkArraysCombine and isinstance(builditem[k], list):
                    builditem[k] = v + builditem[k]
            elif isinstance(v, dict):
                if isinstance(builditem[k], dict):
                    forkCombine(builditem[k], v, forkArraysCombine)

def prepairBuildItems(builditems):
    forkbase=None
    for builditem in builditems:
        if builditem.get("fork", False):
            if forkbase == None:
                buildLog(f"an attempt to fork without a single forkbase before that")
                sys.exit(1)
            
            forkCombine(builditem, forkbase, builditem.get("forkArraysCombine", False), ["forkbase", "fork", "forkArraysCombine", "template"])
        
        if builditem.get("forkbase", False):
            forkbase = builditem

    i = len(builditems) - 1
    while i >= 0:
        builditem = builditems[i]
        if builditem.get("template", False) or ("architectures" in builditem and not architecture in builditem["architectures"]):
            del builditems[i]
        i -= 1

    for index, item in enumerate(builditems):
        item["__item_index"] = index + 1
        item["__items_count"] = len(builditems)

def buildProject(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)

    buildLog(f"Build for architecture: {architecture}")
    builditems = projectData["builditems"]
    cleanup()
    prepairBuild()
    prepairBuildItems(builditems)

    buildLog("Item list:")
    for item in builditems:
        buildItemLog(item, "")
    buildLog(";")
    
    exported = buildItems(builditems)
    buildLog("The build was successful. export list:")
    for exportedItem in exported:
        buildItemLog(exportedItem, "Exported: ", None, True)
    buildLog(";")

def requireRoot():
    if os.geteuid() != 0:
        print("This program requires root permissions. Restarting with sudo...")
        sys.exit(os.system("sudo {} {}".format(sys.executable, " ".join(sys.argv))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="an assembly system for creating Linux distributions. it is focused on embedded distributions")
    parser.add_argument("--arch", choices=["ALL", "amd64", "i386", "arm64", "armhf", "armel"], type=str, required=True, help="the processor architecture for which the build will be made")
    parser.add_argument("json_path", type=str, help="the path to the json file of the project")
    parser.add_argument("-n", action="store_true", help="does the build anew, does not use the cache")
    args = parser.parse_args()
    
    requireRoot()
    
    architecture = args.arch
    log_file = getLogFile()

    buildLog("Syslbuild info:")
    buildLog(f"Syslbuild version: {formatVersion(VERSION)}")
    buildLog(";")

    with open(args.json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)
        showProjectInfo(projectData)
        if not checkVersion(projectData):
            buildLog(f"the project requires at least the syslbuild {formatVersion(projectData["min-syslbuild-version"])} version. you have {formatVersion(VERSION)} installed")
            sys.exit(1)

        if architecture == "ALL":
            if "architectures" in projectData:
                buildLog("build for the following list of architectures:")
                for arch in projectData["architectures"]:
                    buildLog(arch)
                buildLog(";")
                
                for arch in projectData["architectures"]:
                    architecture = arch
                    loadTempPaths()
                    buildProject(args.json_path)
            else:
                buildLog("Architectures list is not defined in project json")
        else:
            loadTempPaths()
            buildProject(args.json_path)
        