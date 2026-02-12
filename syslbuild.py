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

def loadTempPaths():
    global path_temp_architecture
    global path_build
    global path_build_checksums
    global path_temp_cache_pacman
    global path_temp_pacman_conf
    global path_temp_kernel_build
    global path_temp_temp
    global path_logs
    global path_mount
    global path_mount2
    global path_temp_kernel_sources
    
    path_temp_architecture = os.path.join(path_temp, architecture)
    os.makedirs(path_temp_architecture, exist_ok=True)
    
    path_build = os.path.join(path_temp_architecture, "build")
    path_build_checksums = os.path.join(path_temp_architecture, "build_checksums")
    path_temp_cache_pacman = os.path.join(path_temp_architecture, "pacman")
    path_temp_pacman_conf = os.path.join(path_temp_architecture, "pacman.conf")
    path_temp_kernel_build = os.path.join(path_temp_architecture, "last_kernel_build")

    path_temp_temp = os.path.join(path_temp, "temp")
    path_logs = os.path.join(path_temp, "logs")
    path_mount = os.path.join(path_temp, "mount")
    path_mount2 = os.path.join(path_temp, "mount2")
    path_temp_kernel_sources = os.path.join(path_temp, "downloaded_kernel_sources")

aeval = asteval.Interpreter()

DEFAULT_RIGHTS = [0, 0, "0000"]
DEFAULT_RIGHTS_0755 = [0, 0, "0755"]

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

VERSION = [1, 1, 0]

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
        buildLog(f"ERROR: building outside the sandbox: {path1} | {path2}")
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

    if log_file2:
        log_file2.write(logstr + "\n")
        log_file2.flush()

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

def calcSize(sizeLitteral, folderOrFilelist=None):
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
        buildLog(f"ERROR: unknown size unit: {unit}")
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

def getItemPath(item, nameName="name", exportName="export"):
    if readBool(item, exportName):
        path = pathConcat(path_output_target, item[nameName])
    else:
        os.makedirs(path_build, exist_ok=True)
        path = pathConcat(path_build, item[nameName])
    
    return path

def getCustomItemPath(nameValue, exportValue):
    if exportValue:
        path = pathConcat(path_output_target, nameValue)
    else:
        os.makedirs(path_build, exist_ok=True)
        path = pathConcat(path_build, nameValue)
    
    return path

def getItemFolder(item, nameName="name", exportName="export"):
    path = getItemPath(item, nameName, exportName)
    deleteDirectory(path)
    os.makedirs(path, exist_ok=True)
    return path

def getItemChecksumPathFromName(itemName):
    os.makedirs(path_build_checksums, exist_ok=True)
    return pathConcat(path_build_checksums, itemName)

def getItemChecksumPath(item):
    return getItemChecksumPathFromName(item["name"])

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

def findItem(itemName):
    path = pathConcat(path_build, itemName)
    if os.path.exists(path):
        return path
    else:
        path = pathConcat(path_output_target, itemName)
        if os.path.exists(path):
            return path
        else:
            path = pathConcat(".", itemName)
            if os.path.exists(path):
                return path

    buildLog(f"ERROR: failed to find item: {itemName}")
    sys.exit(1)

def isUserItem(itemName):
    path = pathConcat(path_build, itemName)
    if os.path.exists(path):
        return False
    else:
        path = pathConcat(path_output_target, itemName)
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
        buildLog("ERROR: failed to build")
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
        buildLog("ERROR: failed to build")
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
    
    if uid >= 0:
        chownString += str(uid)
    
    if gid >= 0:
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
        buildLog(f"ERROR: unknown kernel type: {kernelType}")
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
    itemFolder = getItemFolder(item)
    cmd += [
        "--aptopt=Acquire::Check-Valid-Until false",
        "--aptopt=Acquire::AllowInsecureRepositories true",
        "--aptopt=APT::Get::AllowUnauthenticated true",
        item["suite"],
        itemFolder,
        item["url"]
    ]
    cmd.append(f"--customize-hook=echo hostname > \"$1/etc/hostname\"")
    cmd.append(f"--customize-hook=rm \"$1\"/etc/resolv.conf")
    if "hook-directory" in item:
        makeAllFilesExecutable(item["hook-directory"])
        cmd.append(f"--hook-directory={item["hook-directory"]}")
    buildExecute(cmd)

    hostsFile = """127.0.0.1 localhost
    127.0.1.1 hostname"""

    path_etc = pathConcat(itemFolder, "etc")
    makedirsChangeRights(path_etc, [0, 0, "0755"])

    path_hosts = pathConcat(path_etc, "hosts")
    path_resolv_conf = pathConcat(path_etc, "resolv.conf")

    if not os.path.exists(path_hosts) and not os.path.lexists(path_hosts):
        with open(path_hosts, "w") as f:
            f.write("127.0.0.1 localhost\n")
            f.write("127.0.1.1 hostname\n")
            f.write("\n")
            f.write("# The following lines are desirable for IPv6 capable hosts\n")
            f.write("::1     ip6-localhost ip6-loopback\n")
            f.write("fe00::0 ip6-localnet\n")
            f.write("ff00::0 ip6-mcastprefix\n")
            f.write("ff02::1 ip6-allnodes\n")
            f.write("ff02::2 ip6-allrouters\n")

        changeAccessRights(path_hosts, [0, 0, "0644"])

    if not os.path.exists(path_resolv_conf) and not os.path.lexists(path_resolv_conf):
        with open(path_resolv_conf, "w") as f:
            f.write("nameserver 1.1.1.1\n")
            f.write("nameserver 1.0.0.1\n")
            f.write("nameserver 2606:4700:4700::1111\n")
            f.write("nameserver 2606:4700:4700::1001\n")
        
        changeAccessRights(path_resolv_conf, [0, 0, "0644"])

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

def recursionDeleleSymlinks(directoryPath):
    buildRawExecute("find . -type l -exec rm -f {} +", True, directoryPath)

def copyItemFiles(fromPath, toPath, changeRights=None):
    if os.path.isdir(fromPath):
        makedirsChangeRights(toPath)
        if changeRights:
            tempFolder = getTempFolder("changeRights")
            buildExecute(["cp", "-a", fromPath + "/.", tempFolder])
            changeAccessRights(tempFolder, changeRights)
            buildExecute(["chmod", "--reference=" + toPath, tempFolder])
            buildExecute(["chown", "--reference=" + toPath, tempFolder])
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
    fs_subtype = None
    if fs_type == "fat12":
        fs_type = "vfat"
        fs_subtype = 12
    elif fs_type == "fat32":
        fs_type = "vfat"
        fs_subtype = 32
    elif fs_type == "fat64":
        fs_type = "vfat"
        fs_subtype = 64

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
        cmd.append(str(item["fsid"]))

    if fs_subtype is not None:
        cmd.append("-F")
        cmd.append(str(fs_subtype))
    
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

def rawItemsProcess(items, itemsDirectory):
    for itemObj in items:
        itemPath = findItem(itemObj[0])
        outputPath = pathConcat(itemsDirectory, itemObj[1])
        buildLog(f"Copy item: {itemPath} > {outputPath}")

        changeRights = None
        if len(itemObj) >= 3:
            changeRights = itemObj[2]
        
        if not changeRights and isUserItem(itemObj[0]):
            changeRights = DEFAULT_RIGHTS
        
        if changeRights:
            buildLog(f"With custom rights: {changeRights}")
        
        copyItemFiles(itemPath, outputPath, changeRights)

def buildDirectory(item):
    buildDirectoryPath = getItemFolder(item)

    if "deleteBeforeAdd" in item:
        for deletePath in item["deleteBeforeAdd"]:
            deleteAny(pathConcat(buildDirectoryPath, deletePath))

    if "directories" in item:
        for directoryData in item["directories"]:
            directoryPath = pathConcat(buildDirectoryPath, directoryData[0])
            changeRights = directoryData[1] or DEFAULT_RIGHTS

            buildLog(f"Create empty directory: {directoryPath} {changeRights}")
            makedirsChangeRights(directoryPath, changeRights)

    if "items" in item:
        rawItemsProcess(item["items"], buildDirectoryPath)

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
        buildLog(f"ERROR: item \"{dirpath}\" is not a directory")
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
    fs_size = calcSize(item["size"], fs_files)
    if "minsize" in item:
        minsize = calcSize(item["minsize"])
        if minsize > fs_size:
            fs_size = minsize
    allocateFile(fs_path, fs_size)

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
        buildLog(f"ERROR: unknown grub target for {architecture} ({"efi" if efi else "bios"})")
        sys.exit(1)

    return target

def installBootloader(item, path, partitionsOffsets, sectorsize):
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

            # in EFI mode, grub-install writes grub files to the /efi/boot directory, while grub itself searches for them simply by following the /boot/grub path
            # Thanks to the grub developers
            grubdir = os.path.join(path_mount2, "boot", "grub")
            makedirsChangeRights(grubdir)
            buildExecute(["cp", "-a", os.path.join(path_mount2, "efi", "boot") + "/.", grubdir])

            if readBool(bootloaderInfo, "efiAndBios"):
                buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, False)}", f"--boot-directory={bootDirectory}", path])
        else:
            buildExecute(["grub-install", f"--modules={modulesString}", f"--target={getGrubTarget(item, False)}", f"--boot-directory={bootDirectory}", path])

        if "config" in bootloaderInfo:
            makedirsChangeRights(pathConcat(bootDirectory, "grub"))
            copyItemFiles(findItem(bootloaderInfo["config"]), pathConcat(bootDirectory, "grub", "grub.cfg"), DEFAULT_RIGHTS)

        umountFilesystem(path_mount)

        if efi:
            umountFilesystem(path_mount2)
    elif bootloaderType == "binary":
        firstPartitionOffset = min(partitionsOffsets)

        for binary in bootloaderInfo["binaries"]:
            bootloaderSector = binary["sector"]
            bootloaderOffsetBytes = bootloaderSector * sectorsize
            if bootloaderOffsetBytes >= firstPartitionOffset:
                buildLog("Bootloader overlaps first partition")
                sys.exit(1)

            bootloaderPath = findItem(binary["file"])
            buildExecute([
                "dd",
                f"if={bootloaderPath}",
                f"of={path}",
                f"bs={sectorsize}",
                f"seek={bootloaderSector}",
                "conv=notrunc"
            ])
    else:
        buildLog("ERROR: unknown bootloader type")
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

    if "partitionsStartSector" in item:
        partitionTable += f"\nfirst-lba: {item["partitionsStartSector"]}"

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
        installBootloader(item, path, partitionsOffsets, resultSectorsize)

def buildUnknown(item):
    buildLog(f"ERROR: unknown build item type: {item["type"]}")
    sys.exit(1)

def buildFromDirectory(item):
    path = getItemPath(item)
    source = findDirectory(item)
    sourcePath = pathConcat(source, item["path"])
    if item.get("save_rights", False):
        copyItemFiles(sourcePath, path)
    else:
        copyItemFiles(sourcePath, path, DEFAULT_RIGHTS_0755)

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
    source = findDirectory(item)
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

    if args.d or not os.path.isdir(kernel_sources) or not os.path.isfile(kernel_sources_downloaded_flag):
        deleteAny(kernel_sources)
        os.makedirs(kernel_sources, exist_ok=True)
        downloadFile(url, kernel_sources_archive)
        buildRawExecute(unpacker % (kernel_sources_archive, kernel_sources))
        emptyFile(kernel_sources_downloaded_flag)
    
    return kernel_sources

def downloadKernelFromGit(item):
    url = item["kernel_source_git"]

    url_hash = hashlib.md5(url.encode('utf-8') + item.get("kernel_source_git_branch", "").encode('utf-8') + item.get("kernel_source_git_checkout", "").encode('utf-8')).hexdigest()
    kernel_sources = pathConcat(path_temp_kernel_sources, url_hash)
    kernel_sources_downloaded_flag = pathConcat(path_temp_kernel_sources, url_hash + ".downloaded")

    if args.d or not os.path.isdir(kernel_sources) or not os.path.isfile(kernel_sources_downloaded_flag):
        deleteAny(kernel_sources)
        os.makedirs(kernel_sources, exist_ok=True)
        
        cmd = ["git", "clone"]
        if "kernel_source_git_branch" in item:
            cmd.append("--single-branch")
            cmd.append("-b")
            cmd.append(item["kernel_source_git_branch"])
        cmd.append(url)
        cmd.append(".")
        buildExecute(cmd, True, None, kernel_sources)

        if "kernel_source_git_checkout" in item:
            buildExecute(["git", "checkout", item["kernel_source_git_checkout"]], True, None, kernel_sources)

        emptyFile(kernel_sources_downloaded_flag)
    
    return kernel_sources

def copyKernel(item, kernel_sources):
    current_kernel_sources_file = pathConcat(path_temp_kernel_build, ".current_kernel_sources")
    patches_checksum_file = pathConcat(path_temp_kernel_build, ".patches_checksum")
    patches_checksum = {"array": []}
    if "patches" in item:
        for file in item["patches"]:
            patches_checksum["array"].append(get_file_checksum(findItem(file)))
    patches_checksum = dictChecksum(patches_checksum)

    if os.path.isdir(path_temp_kernel_build) and os.path.isfile(current_kernel_sources_file) and os.path.isfile(patches_checksum_file):
        with open(current_kernel_sources_file, "r") as f:
            with open(patches_checksum_file, "r") as f2:
                if f.read().strip() == kernel_sources.strip() and f2.read().strip() == patches_checksum.strip():
                    return path_temp_kernel_build, False

    deleteDirectory(path_temp_kernel_build)
    os.makedirs(path_temp_kernel_build, exist_ok=True)
    copyItemFiles(kernel_sources, path_temp_kernel_build)

    with open(current_kernel_sources_file, "w") as f:
        f.write(kernel_sources.strip())

    with open(patches_checksum_file, "w") as f:
        f.write(patches_checksum.strip())

    return path_temp_kernel_build, True

def patchKernel(kernel_sources, patches, patches_ignore_errors=False):
    for patchPath in patches:
        buildRawExecute(f"patch -p1 < {os.path.abspath(findItem(patchPath))}", not patches_ignore_errors, kernel_sources)

kernelArchitectures = {
    "amd64": "x86_64",
    "i386": "x86",
    "arm64": "arm64",
    "armhf": "arm",
    "armel": "arm"
}

kernelArchitectureConfigs = {
    "amd64": "x86_64_defconfig",
    "i386": "i386_defconfig",
    "arm64": "defconfig",
    "armhf": "multi_v7_defconfig",
    "armel": "multi_v5_defconfig"
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

def update_kernel_config(kernel_sources, ARCH_STR, CROSS_COMPILE_STR):
    buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "olddefconfig"], True, None, kernel_sources)

def parse_kernel_config_changes(changes_file):
    with open(changes_file, "r") as f:
        changes = []
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line.startswith("#"):
                change = line.split("=", 1)
                if len(change) == 2:
                    change[0] = change[0].strip()
                    change[1] = change[1].strip()
                    changes.append(change)            
        return changes
    return []

def modifyKernelConfig(item, kernel_sources, ARCH_STR, CROSS_COMPILE_STR):
    kernel_config_path = pathConcat(kernel_sources, ".config")

    if "kernel_config_changes_files" in item:
        for changes_file in item["kernel_config_changes_files"]:
            for change in parse_kernel_config_changes(findItem(changes_file)):
                set_kernel_config_parameter(kernel_config_path, change[0], change[1])

    if "kernel_config_changes" in item:
        for change in item["kernel_config_changes"]:
            set_kernel_config_parameter(kernel_config_path, change[0], change[1])

    if not item.get("kernel_config_disable_default_changes", False):
        # I'm disabling this for some patches to work correctly
        set_kernel_config_parameter(kernel_config_path, "CONFIG_WERROR", "n")

        set_kernel_config_parameter(kernel_config_path, "CONFIG_RD_GZIP", "y")
    
    update_kernel_config(kernel_sources, ARCH_STR, CROSS_COMPILE_STR)

def additionalExportProcess(export_from, additional_export_list):
    for additional_export_item in additional_export_list:
        object_path = pathConcat(export_from, additional_export_item[0])
        copyItemFiles(object_path, getCustomItemPath(additional_export_item[1], additional_export_item[2]))

def buildKernel(item):
    if "kernel_source_url" in item:
        downloaded_kernel_sources = downloadKernel(
            item["kernel_source_url"],
            item.get("kernel_source_unpacker", "tar -xJf %s -C %s --strip-components=1")
        )
    elif "kernel_source_git" in item:
        downloaded_kernel_sources = downloadKernelFromGit(item)
    else:
        buildLog("ERROR: it is impossible to build a kernel without specifying the source code download source")
        sys.exit(1)

    kernel_sources, realCopied = copyKernel(item, downloaded_kernel_sources)

    if "items" in item:
        rawItemsProcess(item["items"], kernel_sources)

    if realCopied and "patches" in item:
        patchKernel(kernel_sources, item["patches"], item.get("patches_ignore_errors", False))

    ARCH = kernelArchitectures[architecture]
    CROSS_COMPILE = gccNames[architecture]
    ARCH_STR = f"ARCH={ARCH}"
    CROSS_COMPILE_STR = f"CROSS_COMPILE={CROSS_COMPILE}-"
    DEFCONFIG_NAME = item.get("defconfig", kernelArchitectureConfigs.get(architecture, "defconfig"))
    buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, DEFCONFIG_NAME], True, None, kernel_sources)

    kernel_config_path = pathConcat(kernel_sources, ".config")

    if "kernel_config" in item:
        copyItemFiles(findItem(item["kernel_config"]), kernel_config_path)

    modifyKernelConfig(item, kernel_sources, ARCH_STR, CROSS_COMPILE_STR)
    buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "modules_prepare"], True, None, kernel_sources)

    if "result_config_name" in item:
        buildLog(f"exporting result kernel config...")
        export_path = getItemPath(item, "result_config_name", "result_config_export")
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
            buildLog(f"ERROR: failed to find \"{kernel_output_filename}\" kernel output file")
            sys.exit(1)

    if "modules_name" in item:
        buildLog(f"exporting modules...")
        export_path = getItemFolder(item, "modules_name", "modules_export")
        buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "modules_install", f"INSTALL_MOD_PATH={os.path.abspath(export_path)}"], True, None, kernel_sources)
        recursionDeleleSymlinks(export_path)

    if "headers_name" in item:
        buildLog(f"exporting headers...")
        export_path = getItemFolder(item, "headers_name", "headers_export")
        buildExecute(["make", ARCH_STR, CROSS_COMPILE_STR, "headers_install", f"INSTALL_HDR_PATH={os.path.abspath(export_path)}"], True, None, kernel_sources)
        recursionDeleleSymlinks(export_path)

    if "additional_export" in item:
        additionalExportProcess(kernel_sources, item["additional_export"])

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

def rawCrossChroot(chrootDirectory, chrootCommand, useSystemd=False, manualValidation=False):
    if useSystemd:
        bindList = []
    else:
        bindList = [
            "dev",
            "proc",
            "sys"
        ]

    makedDirectories = []
    
    for bindPath in bindList:
        chrootSubdirPath = pathConcat(chrootDirectory, bindPath)
        if not os.path.isdir(chrootSubdirPath):
            buildExecute(["mkdir", "-p", chrootSubdirPath])
            buildExecute(["chmod", "1755", chrootSubdirPath])
            buildExecute(["chown", "0:0", chrootSubdirPath])
            makedDirectories.append(chrootSubdirPath)
        buildRawExecute(f"mount --bind /{bindPath} \"{chrootSubdirPath}\"")

    boolCopyQemuStatic = checkQemuStaticNeed()
    qemuStaticName = qemuStaticNames[architecture]
    qemuStaticHostPath = f"/usr/bin/{qemuStaticName}"
    qemuStaticPath = pathConcat(chrootDirectory, "usr/bin", qemuStaticName)

    if boolCopyQemuStatic and not os.path.isfile(qemuStaticHostPath):
        buildLog(f"WARNING: there is no suitable version of qemu-static ({qemuStaticName}) in the host system. we are trying without it")
        boolCopyQemuStatic = False

    if boolCopyQemuStatic:
        if os.path.isfile(qemuStaticPath):
            buildLog(f"copying qemu-static ({qemuStaticName})")
            os.makedirs(os.path.dirname(qemuStaticPath), exist_ok=True)
            buildExecute(["cp", "-a", qemuStaticHostPath, qemuStaticPath])
            buildExecute(["chmod", "0755", qemuStaticPath])
            buildExecute(["chown", "0:0", qemuStaticPath])
        else:
            buildLog(f"qemu-static should have been copied, but the file with that name is already in the chroot directory. i'm skipping it ({qemuStaticName})")

    if useSystemd:
        machineName = "smartchroot"
        buildRawExecute(f"""systemd-nspawn --boot --machine={machineName} --directory="{chrootDirectory}" &
CONTAINER_PID=$!
sleep 10
machinectl shell root@{machineName} {chrootCommand[0]}
machinectl terminate {machineName}
wait $CONTAINER_PID""")
    else:
        buildExecute(["chroot", chrootDirectory] + chrootCommand)

    if boolCopyQemuStatic:
        deleteAny(qemuStaticPath)

    for bindPath in bindList:
        buildRawExecute(f"umount \"{pathConcat(chrootDirectory, bindPath)}\"")

    for makedDirectoryBindPath in makedDirectories:
        buildRawExecute(f"rm -rf \"{makedDirectoryBindPath}\"")


    if manualValidation:
        checkObjPath = pathConcat(chrootDirectory, ".chrootend")
        if os.path.exists(checkObjPath):
            deleteAny(checkObjPath)
        else:
            return False

    return True

def rawUpdateInitramfs(path, kernel_version):
    rawCrossChroot(path, ["update-initramfs", "-c", "-k", kernel_version])

def getKernelVersion(item, rootfsPath):
    if "kernel_version" in item:
        return item["kernel_version"]
    else:
        modulesDirectory = pathConcat(rootfsPath, "lib/modules")
        if os.path.isdir(modulesDirectory):
            for directory in os.listdir(modulesDirectory):
                if os.path.isdir(pathConcat(modulesDirectory, directory)):
                    return directory
        buildLog("the directory of kernel modules was not found in the system (/lib/modules)")
        sys.exit(1)

def debianUpdateInitramfs(item):
    itemPath = getItemFolder(item)
    copyItemFiles(findItem(item["source"]), itemPath)
    rawUpdateInitramfs(itemPath, getKernelVersion(item, itemPath))

def debianExportInitramfs(item):
    tempRootfs = getTempFolder("export_initramfs_rootfs")
    copyItemFiles(findItem(item["source"]), tempRootfs)

    kernel_version = getKernelVersion(item, tempRootfs)

    if "kernel_config" in item:
        newKernelConfigPath = pathConcat(tempRootfs, f"boot/config-{kernel_version}")
        
        bootDirectoryPath = pathConcat(tempRootfs, "boot")
        if not os.path.isdir(bootDirectoryPath):
            os.makedirs(bootDirectoryPath)

        copyItemFiles(findItem(item["kernel_config"]), newKernelConfigPath, DEFAULT_RIGHTS_0755)

    rawUpdateInitramfs(tempRootfs, kernel_version)

    initramfsPaths = [
        pathConcat(tempRootfs, f"boot/initrd.img-{kernel_version}"),
        pathConcat(tempRootfs, f"boot/initramfs.img-{kernel_version}"),
        pathConcat(tempRootfs, f"initrd.img-{kernel_version}"),
        pathConcat(tempRootfs, f"initramfs.img-{kernel_version}"),
        pathConcat(tempRootfs, f"boot/initrd.img"),
        pathConcat(tempRootfs, f"boot/initramfs.img"),
        pathConcat(tempRootfs, f"initrd.img"),
        pathConcat(tempRootfs, f"initramfs.img")
    ]
    exportInitramfsPath = getItemPath(item)
    for initramfsPath in initramfsPaths:
        if os.path.isfile(initramfsPath):
            copyItemFiles(initramfsPath, exportInitramfsPath, DEFAULT_RIGHTS_0755)
            break

def smartChroot(item):
    itemPath = getItemFolder(item)
    copyItemFiles(findItem(item["source"]), itemPath)
    for scriptPath in item["scripts"]:
        chroot_script_path = pathConcat(itemPath, ".syslbuild-smart-chroot.sh")
        copyItemFiles(scriptPath, chroot_script_path, DEFAULT_RIGHTS_0755)
        if rawCrossChroot(itemPath, ["/.syslbuild-smart-chroot.sh"], item.get("use_systemd_container", False), item.get("manual_validation", False)):
            buildExecute("reset")
        else:
            buildLog(f"ERROR: with \"manual_validation\" enabled, the chroot script \"{os.path.basename(scriptPath)}\" did not create a file or directory on the path \"/.chrootend\"")
            sys.exit(1)

        os.remove(chroot_script_path)

def singleboardBuild(item):
    singleboardType = item["singleboardType"]
    builditemName = item["name"]

    if singleboardType == "uboot-16":
        bootdirName = builditemName + "_bootdir"
        bootfsName = builditemName + "_bootfs"

        bootloaderFileName = os.path.basename(item["bootloader"])
        kernelFileName = item.get("kernel_filename_override", os.path.basename(item["kernel"]))
        if "initramfs" in item:
            initramfsFileName = item.get("initramfs_filename_override", os.path.basename(item["initramfs"]))

        # boot directory
        buildDirectoryBuilditem = {
            "name": bootdirName,
            "export": False,

            "directories": [
                ["/dtbs/overlay", [0, 0, "0755"]],
                ["/extlinux", [0, 0, "0755"]]
            ],

            "items": [
                [item["bootloader"], bootloaderFileName, [0, 0, "0644"]],
                [item["kernel"], kernelFileName, [0, 0, "0644"]]
            ]
        }
        
        if initramfsFileName is not None:
            buildDirectoryBuilditem["items"].append([item["initramfs"], initramfsFileName, [0, 0, "0644"]])
        
        if "dtbList" in item:
            for dtb in item["dtbList"]:
                buildDirectoryBuilditem["items"].append([dtb, pathConcat("/dtbs", os.path.basename(dtb)), [0, 0, "0644"]])

        if "dtboList" in item:
            for dtb in item["dtboList"]:
                buildDirectoryBuilditem["items"].append([dtb, pathConcat("/dtbs/overlay", os.path.basename(dtb)), [0, 0, "0644"]])

        buildDirectory(buildDirectoryBuilditem)

        # boot config
        bootDirectory = findItem(bootdirName)
        extlinuxPath = pathConcat(bootDirectory, "extlinux/extlinux.conf")
        
        with open(extlinuxPath, "w") as f:
            f.write("LABEL linux\n")
            f.write(f"KERNEL /{kernelFileName}\n")
            if "bootloaderDtb" in item:
                f.write(f"FDT /dtbs/{item["bootloaderDtb"]}\n")
            
            kernel_args = item.get("kernel_args", "")
            
            if item.get("kernel_rootfs_auto", False):
                if "rootfs" in item:
                    kernel_args = f"root=/dev/mmcblk0p2 {item.get("kernel_rootfs_auto")} " + kernel_args
            
            if item.get("kernel_args_auto", False):
                if "initramfs" in item:
                    kernel_args = f"initrd=/{initramfsFileName} " + kernel_args
            
            f.write(f"APPEND {kernel_args}")

        # boot partition
        buildFilesystem({
            "name": bootfsName,
            "export": False,

            "source": bootdirName,

            "fs_type": "fat32",
            "size": "(auto * 1.2) + (100 * 1024 * 1024)",
            "minsize": "64MB",
            "label": "BOOT"
        })

        # bootable image
        buildFullDiskImageBuilditem = {
            "name": builditemName,
            "export": readBool(item, "export"),

            "size": "auto + (16 * 1024 * 1024)",

            "partitionsStartSector": 8192,
            "partitionTable": "dos",
            "partitions": [
                [bootfsName, "linux"]
            ],

            "bootloader": {
                "type": "binary",
                "binaries": [
                    {
                        "file": item["bootloader"],
                        "sector": 16
                    }
                ]
            }
        }
        if "rootfs" in item:
            buildFullDiskImageBuilditem["partitions"].append([item["rootfs"], "linux"])
        buildFullDiskImage(buildFullDiskImageBuilditem)

def gitcloneBuild(item):
    url = item["git_url"]
    output_folder = getItemFolder(item)
    
    cmd = ["git", "clone"]
    if "git_branch" in item:
        cmd.append("--single-branch")
        cmd.append("-b")
        cmd.append(item["git_branch"])
    cmd.append(url)
    cmd.append(".")
    buildExecute(cmd, True, None, output_folder)

    if "git_checkout" in item:
        buildExecute(["git", "checkout", item["git_checkout"]], True, None, output_folder)

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
    "debian-update-initramfs": debianUpdateInitramfs,
    "debian-export-initramfs": debianExportInitramfs,
    "smart-chroot": smartChroot,
    "singleboard": singleboardBuild,
    "gitclone": gitcloneBuild
}

def get_file_checksum(file_path, hash_algo="sha256"):
    h = hashlib.new(hash_algo)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError:
        return "failed_checksum"

    return h.hexdigest()


def get_dir_checksum(dir_path, hash_algo="sha256"):
    # создаём хэш от всех файлов в директории
    h = hashlib.new(hash_algo)
    for root, dirs, files in os.walk(dir_path):
        for name in sorted(files):  # сортировка для стабильности
            file_path = os.path.join(root, name)
            h.update(file_path.encode())  # путь влияет на хэш
            h.update(get_file_checksum(file_path, hash_algo).encode())
    return h.hexdigest()

def getDependenciesFileOrDirectoryChecksum(pathOrChecksum, hash_algo="sha256"):
    if pathOrChecksum.startswith("@") or pathOrChecksum == "NOT CALCULATED":
        return pathOrChecksum
    
    if os.path.isfile(pathOrChecksum):
        return get_file_checksum(pathOrChecksum, hash_algo)
    elif os.path.isdir(pathOrChecksum):
        return get_dir_checksum(pathOrChecksum, hash_algo)
    
    return "NOT EXISTS"
    
# если какое то поле зависимостей ссылается на массив массивов то в втором массиве учитываются только элементы с индексом 0
# ТАК И ЗАДУМАНО!
def getDependenciesFieldChecksum(fieldValue, filesOnly=False):
    def inlineFindItem(inputPath):
        if not filesOnly:
            if os.path.exists(pathConcat(path_build, inputPath)) or os.path.exists(pathConcat(path_output_target, inputPath)):
                checksumPath = getItemChecksumPathFromName(inputPath)
                if os.path.exists(checksumPath):
                    with open(checksumPath, "r") as f:
                        return "@" + f.read()
                else:
                    return "NOT CALCULATED"
        return inputPath

    if isinstance(fieldValue, str):
        return getDependenciesFileOrDirectoryChecksum(inlineFindItem(fieldValue))
    elif isinstance(fieldValue, list):
        checkDict = {
            "array": []
        }

        for inlineFieldValue in fieldValue:
            if isinstance(inlineFieldValue, str):
                checkDict["array"].append(getDependenciesFileOrDirectoryChecksum(inlineFindItem(inlineFieldValue)))
            elif isinstance(inlineFieldValue, list):
                checkDict["array"].append(getDependenciesFileOrDirectoryChecksum(inlineFindItem(inlineFieldValue[0])))

        return dictChecksum(checkDict)
    else:
        buildLog("ERROR: failed to get dependencies checksum")
        sys.exit(1)

def rawGetDependencies(item, items_and_files_fields=None, files_only_fields=None):
    dependencies = []

    if items_and_files_fields:
        for fieldName in items_and_files_fields:
            if fieldName in item:
                dependencies.append(getDependenciesFieldChecksum(item[fieldName], False))

    if files_only_fields:
        for fieldName in files_only_fields:
            if fieldName in item:
                dependencies.append(getDependenciesFieldChecksum(item[fieldName], True))

    return dependencies

def getDependenciesDebian(item):
    return rawGetDependencies(item, [], ["hook-directory"])

def getDependenciesDirectory(item):
    return rawGetDependencies(item, ["items"], [])

def getDependenciesTar(item):
    return rawGetDependencies(item, ["source"], [])

def getDependenciesFilesystem(item):
    return rawGetDependencies(item, ["source"], [])

def getDependenciesFullDiskImage(item):
    dependencies = rawGetDependencies(item, ["partitions"], [])
    if item.get("bootloader", {}).get("config", None):
        dependencies.append(getDependenciesFieldChecksum(item["bootloader"]["config"], False))
    return dependencies

def getDependenciesFromDirectory(item):
    return rawGetDependencies(item, ["source"], [])

def getDependenciesGccBuild(item):
    return rawGetDependencies(item, [], ["sources-dirs"])

def getDependenciesInitramfs(item):
    return rawGetDependencies(item, ["source"], [])

def getDependenciesGrubIsoImage(item):
    return rawGetDependencies(item, ["kernel", "initramfs", "config"], [])

def getDependenciesUnpackInitramfs(item):
    return rawGetDependencies(item, ["initramfs"], [])

def getDependenciesKernel(item):
    return rawGetDependencies(item, ["patches", "kernel_config", "kernel_config_changes_files", "items"], [])

def getDependenciesDebianUpdateInitramfs(item):
    return rawGetDependencies(item, ["source"], [])

def getDependenciesDebianExportInitramfs(item):
    return rawGetDependencies(item, ["kernel_config", "source"], [])

def getDependenciesSmartChroot(item):
    return rawGetDependencies(item, ["scripts", "source"], [])

def getDependenciesSingleboard(item):
    return rawGetDependencies(item, ["bootloader", "initramfs", "kernel", "rootfs", "dtbList", "dtboList", "bootloaderDtb"], [])

getDependencies = {
    "debian": getDependenciesDebian,
    "directory": getDependenciesDirectory,
    "tar": getDependenciesTar,
    "filesystem": getDependenciesFilesystem,
    "full-disk-image": getDependenciesFullDiskImage,
    "from-directory": getDependenciesFromDirectory,
    "gcc-build": getDependenciesGccBuild,
    "initramfs": getDependenciesInitramfs,
    "grub-iso-image": getDependenciesGrubIsoImage,
    "unpack-initramfs": getDependenciesUnpackInitramfs,
    "kernel": getDependenciesKernel,
    "debian-update-initramfs": getDependenciesDebianUpdateInitramfs,
    "debian-export-initramfs": getDependenciesDebianExportInitramfs,
    "smart-chroot": getDependenciesSmartChroot,
    "singleboard": getDependenciesSingleboard
}

def filter_underscored(d):
    if not isinstance(d, dict):
        return d
    return {k: filter_underscored(v) for k, v in d.items() if not k.startswith("_")}

def dictChecksum(tbl):
    filtered = filter_underscored(tbl)
    return hashlib.md5(json5.dumps(filtered).encode('utf-8')).hexdigest()

def getItemChecksum(item):
    if item["type"] in getDependencies:
        dependencies = getDependencies[item["type"]](item)
    else:
        dependencies = []

    checksumDict = {
        "item": item,
        "dependencies": dependencies
    }

    return dictChecksum(checksumDict)

def writeCacheChecksum(item, checksum):
    checksum_path = getItemChecksumPath(item)
    with open(checksum_path, "w") as f:
        f.write(checksum)

def writeCacheChecksumForName(itemName, checksum):
    checksum_path = getItemChecksumPathFromName(itemName)
    with open(checksum_path, "w") as f:
        f.write(checksum)

def isCacheValid(item, checksum):
    checksum_path = getItemChecksumPath(item)
    if os.path.exists(checksum_path):
        with open(checksum_path, "r") as f:
            return f.read() == checksum
    return False

def writeOtherChecksums(item, checksum):
    if "headers_name" in item:
        writeCacheChecksumForName(item["headers_name"], checksum)
    
    if "modules_name" in item:
        writeCacheChecksumForName(item["modules_name"], checksum)
    
    if "result_config_name" in item:
        writeCacheChecksumForName(item["result_config_name"], checksum)

    if "additional_export" in item:
        for additional_export_item in item["additional_export"]:
            writeCacheChecksumForName(additional_export_item[1], checksum)

def buildItems(builditems):
    exported = []
        
    for item in builditems:
        itemPath = getItemPath(item)
        checksum = getItemChecksum(item)
        if isCacheValid(item, checksum) and not args.n:
            buildItemLog(item, None, " (cache)")
        else:
            deleteAny(itemPath)
            buildItemLog(item)
            buildActions.get(item["type"], buildUnknown)(item)
            writeCacheChecksum(item, checksum)
            writeOtherChecksums(item, checksum)
        
        if readBool(item, "export"):
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
    # recursionUmount(path_output_target)
    # deleteDirectory(path_output_target)
    os.makedirs(path_output_target, exist_ok=True)

def forkCombine(builditem, forkbase, forkArraysCombine=False, keysBlackList=None, recursionKeyBlackList=None):
    for k, v in forkbase.items():
        if (not keysBlackList or k not in keysBlackList) and (not recursionKeyBlackList or k not in recursionKeyBlackList):
            if k not in builditem:
                builditem[k] = v
            elif isinstance(v, list):
                if forkArraysCombine and isinstance(builditem[k], list):
                    builditem[k] = v + builditem[k]
            elif isinstance(v, dict):
                if isinstance(builditem[k], dict):
                    forkCombine(builditem[k], v, forkArraysCombine, None, recursionKeyBlackList)

def deleteBuildItemKeysProcess(builditemDict):
    if "deleteBuildItemKeys" in builditemDict:
        for deleteBuildItemKey in builditemDict["deleteBuildItemKeys"]:
            builditemDict.pop(deleteBuildItemKey, None)

    for k, v in builditemDict.items():
        if isinstance(v, dict):
            deleteBuildItemKeysProcess(v)

def includeArchitectureCheck(builditem):
    return ("architectures" not in builditem) or (architecture in builditem["architectures"])

def includeProcess(builditems, included=None):
    includeDetected=False
    for builditem in builditems:
        if "type" in builditem and builditem["type"] == "include" and includeArchitectureCheck(builditem):
            includeDetected=True

    if includeDetected:
        if included is None:
            included = []

        newBuilditems = []
        for builditem in builditems:
            if "type" in builditem and builditem["type"] == "include":
                if includeArchitectureCheck(builditem):
                    includeFilePath = builditem["file"]
                    if includeFilePath in included:
                        buildLog(f"double include the \"{includeFilePath}\" file")
                        sys.exit(1)
                    included.append(includeFilePath)

                    with open(includeFilePath, "r", encoding="utf-8") as f:
                        newLocalBuilditems = json5.load(f)
                        if not isinstance(newLocalBuilditems, list):
                            buildLog(f"there is no \"{includeFilePath}\" array in the root of the attached file")
                            sys.exit(1)
                        newBuilditems.extend(newLocalBuilditems)
            else:
                newBuilditems.append(builditem)

        return includeProcess(newBuilditems, included)
    
    return builditems

def prepairBuildItems(builditems):
    builditems = includeProcess(builditems)

    forkbase=None
    for builditem in builditems:
        if builditem.get("fork", False):
            if forkbase == None:
                buildLog(f"ERROR: an attempt to fork without a single forkbase before that")
                sys.exit(1)
            
            forkCombine(builditem, forkbase, builditem.get("forkArraysCombine", False), ["forkbase", "fork", "forkArraysCombine", "template"], ["deleteBuildItemKeys"])
        
        if builditem.get("forkbase", False):
            forkbase = builditem

    i = len(builditems) - 1
    while i >= 0:
        builditem = builditems[i]
        if builditem.get("template", False) or ("architectures" in builditem and not architecture in builditem["architectures"]):
            del builditems[i]
        i -= 1

    for builditem in builditems:
        deleteBuildItemKeysProcess(builditem)

    for index, item in enumerate(builditems):
        item["__item_index"] = index + 1
        item["__items_count"] = len(builditems)

    return builditems

def buildProject(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)

    buildLog(f"Build for architecture: {architecture}")
    builditems = projectData["builditems"]
    cleanup()
    prepairBuild()
    builditems = prepairBuildItems(builditems)

    namesExists = []
    buildLog("Item list:")
    for item in builditems:
        if "name" not in item:
            buildLog(f"ERROR: builditem without a name")
            sys.exit(1)
        elif "type" not in item:
            buildLog(f"ERROR: builditem without a type")
            sys.exit(1)
        elif item["name"] not in namesExists:
            buildItemLog(item)
            namesExists.append(item["name"])
        else:
            buildLog(f"ERROR: more than one builditem named {item["name"]}")
            sys.exit(1)
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

def changeOutputRights(path):
    """
    Для указанной папки:
    - Ставит 777 на саму папку.
    - Рекурсивно ставит 777 на все подпапки.
    - Для файлов внутри этих подпапок (но не дальше) ставит 777.
    """
    path = os.path.abspath(path)

    # Ставим 777 на саму папку
    os.chmod(path, 0o777)

    # Проходим по подпапкам
    for entry in os.listdir(path):
        sub_path = os.path.join(path, entry)
        if os.path.isdir(sub_path):
            os.chmod(sub_path, 0o777)  # права на подпапку
            # файлы внутри этой подпапки (не рекурсивно)
            for f in os.listdir(sub_path):
                file_path = os.path.join(sub_path, f)
                if os.path.isfile(file_path):
                    os.chmod(file_path, 0o777)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="an assembly system for creating Linux distributions. it is focused on embedded distributions")
    parser.add_argument("--arch", choices=["ALL", "amd64", "i386", "arm64", "armhf", "armel"], type=str, required=True, help="the processor architecture for which the build will be made")
    parser.add_argument("--output", type=str, help="path to output directory")
    parser.add_argument("--temp", type=str, help="path to .temp directory")
    parser.add_argument("--lastlog", type=str, help="additional log file")
    parser.add_argument("json_path", type=str, help="the path to the json file of the project")
    parser.add_argument("-n", action="store_true", help="does the build anew, does not use the cache")
    parser.add_argument("-d", action="store_true", help="do not use the download cache of the kernel sources")
    parser.add_argument("-e", action="store_true", help="completely clears the entire cache before building")
    args = parser.parse_args()
    
    requireRoot()

    if "temp" in args and args.temp:
        path_temp = args.temp
    
    if "output" in args and args.output:
        path_output = args.output
    
    architecture = args.arch
    loadTempPaths()
    if args.e:
        deleteAny(path_temp)
        deleteAny(path_output)
    log_file = getLogFile()
    
    if "lastlog" in args and args.lastlog:
        log_file2 = open(args.lastlog, "w")
    else:
        log_file2 = None

    buildLog("Syslbuild info:")
    buildLog(f"Syslbuild version: {formatVersion(VERSION)}")
    buildLog(";")

    with open(args.json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)
        showProjectInfo(projectData)
        if not checkVersion(projectData):
            buildLog(f"ERROR: the project requires at least the syslbuild {formatVersion(projectData["min-syslbuild-version"])} version. you have {formatVersion(VERSION)} installed")
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

    changeOutputRights(path_output)
    
