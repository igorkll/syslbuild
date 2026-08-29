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
import time
from pathlib import Path
import uuid

# ---------------------------------------

syslbuild_install_path = "/opt/syslbuild"
if os.path.isdir(syslbuild_install_path):
    syslbuild_path = syslbuild_install_path
else:
    syslbuild_path = "."

sys.path.insert(0, os.path.join(syslbuild_path, "syslbuild", "pyimport"))
sys.path.insert(0, os.path.join(syslbuild_path))

print("syslbuild path: ", syslbuild_path)

import version

# ---------------------------------------

path_output = "output"
path_temp = ".temp"

def loadTempPaths():
    global path_temp_architecture
    global path_build
    global path_build_independent
    global path_build_checksums
    global path_build_checksums_independent
    global path_temp_cache_pacman
    global path_temp_pacman_conf
    global path_temp_kernel_build
    global path_temp_temp
    global path_logs
    global path_mount
    global path_mount2
    global path_temp_kernel_sources
    
    path_temp_architecture = os.path.join(path_temp, architecture)
    if architecture != "ALL":
        os.makedirs(path_temp_architecture, exist_ok=True)
        if args.g:
            deleteAny(path_temp_architecture)

    path_build_independent = os.path.join(path_temp, "independent", "build")
    path_build_checksums_independent = os.path.join(path_temp, "independent", "build_checksums")

    path_build = os.path.join(path_temp_architecture, "build")
    path_build_checksums = os.path.join(path_temp_architecture, "build_checksums")
    path_temp_cache_pacman = os.path.join(path_temp_architecture, "pacman")
    path_temp_pacman_conf = os.path.join(path_temp_architecture, "pacman.conf")
    path_temp_kernel_build = os.path.join(path_temp_architecture, "kernel_build")

    if architecture != "ALL" and args.g:
        deleteAny(path_temp_architecture)

    path_temp_temp = os.path.join(path_temp, "temp")
    path_logs = os.path.join(path_temp, "logs")
    path_mount = os.path.join(path_temp, "mount")
    path_mount2 = os.path.join(path_temp, "mount2")
    path_temp_kernel_sources = os.path.join(path_temp, "downloaded_kernel_sources")

aeval = asteval.Interpreter()

DEFAULT_RIGHTS_0700 = [0, 0, "0700"]
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

DD_BS = "4M"

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

    if log_file3:
        log_file3.write(logstr + "\n")
        log_file3.flush()

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

def getLogFile():
    os.makedirs(path_logs, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"build_{architecture}_{timestamp}.log"
    filepath = pathConcat(path_logs, filename)

    print(f"Log path: {filepath}")
    return open(filepath, "w")

def getLastLogFile():
    os.makedirs(path_temp, exist_ok=True)
    filepath = pathConcat(path_temp, "last.log")

    print(f"Log path: {filepath}")
    return open(filepath, "w")

def readBool(tbl, name):
    if name in tbl:
        return bool(tbl[name])
    
    return False

def getItemPath(item, nameName="name", exportName="export", copyInput=True):
    if readBool(item, exportName):
        path = pathConcat(path_output_target, item[nameName])
    else:
        os.makedirs(path_build, exist_ok=True)
        path = pathConcat(path_build, item[nameName])

    if item.get("input", False) and copyInput:
        parent_item = findItem(item["input"])
        os.makedirs(path, exist_ok=True)
        copyItemFiles(parent_item, path)

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
    if not item.get("input", False):
        deleteDirectory(path)
        os.makedirs(path, exist_ok=True)
    return path

def getItemChecksumPathFromName(itemName):
    os.makedirs(path_build_checksums, exist_ok=True)
    return pathConcat(path_build_checksums, itemName)

def getItemChecksumPathFromName_independent(itemName):
    os.makedirs(path_build_checksums_independent, exist_ok=True)
    return pathConcat(path_build_checksums_independent, itemName)

def getItemChecksumPath(item):
    return getItemChecksumPathFromName(item["name"])

def getItemChecksumPath_independent(item):
    return getItemChecksumPathFromName_independent(item["name"])

def deleteDirectory(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def deleteFile(path):
    if os.path.exists(path):
        os.remove(path)

def deleteAny(path):
    if os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
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

def resolveItemName(itemName):
    if itemName == "@previous":
        if previous_builditem:
            return previous_builditem["name"]
        else:
            buildLog(f"ERROR: you can't use @previous in the first builditem.")
            sys.exit(1)
    elif itemName == "@marker":
        if marker_builditem:
            return marker_builditem["name"]
        else:
            buildLog(f"ERROR: you can't use @marker before \"marker: true\" element")
            sys.exit(1)

    return itemName

def findItem(itemName):
    if itemName.startswith("&"):
        return itemName[1:]
    
    itemName = resolveItemName(itemName)

    path = pathConcat(path_build, itemName)
    if os.path.exists(path):
        return path
    
    path = pathConcat(path_output_target, itemName)
    if os.path.exists(path):
        return path

    path = pathConcat(path_build_independent, itemName)
    if os.path.exists(path):
        return path

    path = pathConcat(path_output_target_independent, itemName)
    if os.path.exists(path):
        return path
    
    path = pathConcat(".", itemName)
    if os.path.exists(path):
        return path

    buildLog(f"ERROR: failed to find item: {itemName}")
    sys.exit(1)

def buildExecute(cmd, checkValid=True, input_data=None, cwd=None, envmod=None):
    if cwd is not None:
        buildLog(f"Execute command from directory ({cwd}): {cmd}")
    else:
        buildLog(f"Execute command: {cmd}")

    env=None
    if envmod:
        env = os.environ.copy()
        env.update(envmod)
    
    process = subprocess.Popen(
        cmd,
        shell=False,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=cwd,
        env=env
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

def buildRawExecute(cmd, checkValid=True, cwd=None, envmod=None):
    if cwd is not None:
        buildLog(f"Execute raw command from directory ({cwd}): {cmd}")
    else:
        buildLog(f"Execute raw command: {cmd}")

    env=None
    if envmod:
        env = os.environ.copy()
        env.update(envmod)
    
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        cwd=cwd,
        env=env
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

def buildRawExecuteLiveOutput(cmd, checkValid=True, cwd=None, envmod=None):
    if cwd is not None:
        buildLog(f"Execute raw command from directory ({cwd}): {cmd}")
    else:
        buildLog(f"Execute raw command: {cmd}")

    env = None
    if envmod:
        env = os.environ.copy()
        env.update(envmod)

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=None,
        stderr=None,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        env=env
    )

    returncode = process.wait()

    if returncode != 0 and checkValid:
        buildLog("ERROR: failed to build")
        sys.exit(1)

def doCommands(cwd, commands=None):
    if commands:
        for command in commands:
            buildRawExecuteLiveOutput(command, True, cwd)

def buildItemLog(item, comment=None, comment2=None, hideExport=False):
    if comment is None:
        comment = "Building item ---------------- "
    
    if comment2 is None:
        comment2 = ""
    
    buildLog(f"{comment}{item['__item_index']}/{item['__items_count']} {item['type']} ({item['name']}){' (export)' if (readBool(item, 'export') and not hideExport) else ''}{comment2}")

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

def filter_underscored(d):
    if not isinstance(d, dict):
        return d
    return {k: filter_underscored(v) for k, v in d.items() if not k.startswith("_")}

def dictChecksum(tbl):
    filtered = filter_underscored(tbl)
    return hashlib.md5(json5.dumps(filtered).encode('utf-8')).hexdigest()

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

# -------------------------------------------------- builditems

def buildUnknown(item):
    buildLog(f"ERROR: unknown build item type: {item['type']}")
    sys.exit(1)

buildActions = {}

def syslbuild_push_buildItems(buildActionsDict):
    buildActions.update(buildActionsDict)

# -------------------------------------------------- dependencies

getDependencies = {}

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
# возможно стоит пересмотреть это архитектурное решение чтобы потом не запутатся при добавлении новых элементов сборки
def getDependenciesFieldChecksum(fieldValue, filesOnly=False, target=None, fieldName=None):
    def inlineFindItem(inputPath):
        if not filesOnly:
            if os.path.exists(pathConcat(path_build_independent, inputPath)) or os.path.exists(pathConcat(path_output_target_independent, inputPath)):
                checksumPath = getItemChecksumPathFromName_independent(inputPath.split("/", 1)[0])
                if os.path.exists(checksumPath):
                    with open(checksumPath, "r") as f:
                        return "@" + f.read()

            if os.path.exists(pathConcat(path_build, inputPath)) or os.path.exists(pathConcat(path_output_target, inputPath)):
                # так как начиная с версии syslbuild 1.5.5 добавилась поддержка указания путей добавляемого обьекта прямо внутри имени builditem через /
                # что уменьшает количество использований from-directory и сокрашает размер файлов конфигурации
                # сдесь нужно сделать split, чтобы получить реальное имя builditem
                checksumPath = getItemChecksumPathFromName(inputPath.split("/", 1)[0])
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
                # не учитываем прямую запись строчки в file через builditem "directory"
                if target != "directory" or fieldName != "items" or len(inlineFieldValue) <= 3 or not inlineFieldValue[3]:
                    checkDict["array"].append(getDependenciesFileOrDirectoryChecksum(inlineFindItem(inlineFieldValue[0])))

        return dictChecksum(checkDict)
    else:
        buildLog("ERROR: failed to get dependencies checksum")
        sys.exit(1)

def rawGetDependencies(item, items_and_files_fields=None, files_only_fields=None, target=None):
    dependencies = []

    if items_and_files_fields:
        for fieldName in items_and_files_fields:
            if fieldName in item:
                dependencies.append(getDependenciesFieldChecksum(item[fieldName], False, target, fieldName))

    if files_only_fields:
        for fieldName in files_only_fields:
            if fieldName in item:
                dependencies.append(getDependenciesFieldChecksum(item[fieldName], True, target, fieldName))

    return dependencies

def syslbuild_push_getDependencies(getDependenciesDict):
    getDependencies.update(getDependenciesDict)

# -------------------------------------------------- build project

def getItemChecksum(item):
    if not item.get("disable_cache", False) and item["type"] in getDependencies:
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
    if item.get("disable_cache", False):
        return False

    def check(f):
        readed = f.read()
        return readed == checksum or readed.strip() == "TEST"

    checksum_path_independent = getItemChecksumPath_independent(item)
    if os.path.exists(checksum_path_independent):
        with open(checksum_path_independent, "r") as f:
            if check(f):
                return True

    checksum_path = getItemChecksumPath(item)
    if os.path.exists(checksum_path):
        with open(checksum_path, "r") as f:
            if check(f):
                return True
    
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
    global previous_builditem
    global marker_builditem
    global current_builditem

    previous_builditem = None
    marker_builditem = None
    current_builditem = None

    exported = []
        
    for item in builditems:
        checksum = getItemChecksum(item)
        current_builditem = item

        if isCacheValid(item, checksum) and not args.n:
            buildItemLog(item, None, " (cache)")
        else:
            buildItemLog(item)
            itemPath = getItemPath(item, "name", "export", False)
            deleteAny(itemPath)
            buildActions.get(item["type"], buildUnknown)(item)

            if item.get("disable_cache", False):
                if item.get("disable_cache_always_changed", False):
                    checksum_random = "RANDOM_" + uuid.uuid4()
                    writeCacheChecksum(item, checksum_random)
                    writeOtherChecksums(item, checksum_random)
            else:
                writeCacheChecksum(item, checksum)
                writeOtherChecksums(item, checksum)

        previous_builditem = item

        if item.get("marker", False):
            marker_builditem = item
        
        if readBool(item, "export"):
            exported.append(item)
    
    return exported

def showProjectInfo(projectData):
    buildLog(f"Project info:")

    if "min-syslbuild-version" in projectData:
        buildLog(f"Minimal syslbuild: {version.formatVersion(projectData['min-syslbuild-version'])}")
    
    buildLog(";")

def cleanup():
    recursionUmount(path_temp)
    umountFilesystem(path_mount)
    umountFilesystem(path_mount2)
    deleteDirectory(path_temp_temp)

def prepairBuild():
    global path_output_target
    global path_output_target_independent
    path_output_target = pathConcat(path_output, architecture)
    path_output_target_independent = pathConcat(path_output, "independent")

    os.makedirs(path_output_target, exist_ok=True)
    os.makedirs(path_output_target_independent, exist_ok=True)

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

def buildItemArchitectureDeleteCheck(builditem):
    independent_architecture = builditem.get("independent_architecture", False)

    if architecture == "independent" and independent_architecture and "architectures" in builditem and not (set(global_architectures) & set(builditem["architectures"])):
        return True

    if (architecture == "independent") != (not not independent_architecture):
        return True
    
    return "architectures" in builditem and not architecture in builditem["architectures"]

def buildItemFilterDeleteCheck(builditem):
    filtered_delete = False

    if builditem.get("build-if-filter-exists", False) and len(filters) == 0:
        filtered_delete = True
    elif builditem.get("build-if-filter-not-exists", False) and len(filters) > 0:
        filtered_delete = True
    elif "build-if-all-filters-exists" in builditem and not all(x in filters for x in builditem["build-if-all-filters-exists"]):
        filtered_delete = True
    elif "build-if-one-filter-exists" in builditem and not any(x in filters for x in builditem["build-if-one-filter-exists"]):
        filtered_delete = True
    elif "build-if-not-all-filters-exists" in builditem and all(x in filters for x in builditem["build-if-not-all-filters-exists"]):
        filtered_delete = True
    elif "build-if-not-one-filter-exists" in builditem and any(x in filters for x in builditem["build-if-not-one-filter-exists"]):
        filtered_delete = True
    elif "build-if-no-filters-or-one-filter-exists" in builditem and len(filters) > 0 and not any(x in filters for x in builditem["build-if-no-filters-or-one-filter-exists"]):
        filtered_delete = True

    return filtered_delete

def buildItemDeleteCheck(builditem):
    return buildItemArchitectureDeleteCheck(builditem) or buildItemFilterDeleteCheck(builditem)

def includeProcess(builditems, included=None):
    includeDetected=False
    for builditem in builditems:
        if "type" in builditem and builditem["type"] == "include" and not buildItemDeleteCheck(builditem):
            includeDetected=True

    if includeDetected:
        if included is None:
            included = []

        newBuilditems = []
        for builditem in builditems:
            if "type" in builditem and builditem["type"] == "include":
                if not buildItemDeleteCheck(builditem):
                    includeFilePath = builditem["file"]
                    if includeFilePath in included:
                        buildLog(f"double include the \"{includeFilePath}\" file")
                        sys.exit(1)
                    included.append(includeFilePath)

                    buildLog(f"reading include: {includeFilePath}")
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

forkKeysBlacklist = [
    "forkbase",
    "fork",
    "forkArraysCombine",
    "template"
]

def prepairBuildItems(builditems):
    builditems = includeProcess(builditems)

    forkbase=None
    for builditem in builditems:
        if builditem.get("fork", False):
            if forkbase is None:
                buildLog(f"ERROR: an attempt to fork without a single forkbase before that")
                sys.exit(1)
            
            forkCombine(builditem, forkbase, builditem.get("forkArraysCombine", False), forkKeysBlacklist, ["deleteBuildItemKeys"])
        
        if builditem.get("forkbase", False):
            forkbase = builditem

    i = len(builditems) - 1
    while i >= 0:
        builditem = builditems[i]

        if builditem.get("template", False) or buildItemDeleteCheck(builditem):
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
        elif item["name"].startswith("@"):
            buildLog(f"ERROR: the builditem name cannot start with the @ character, as this is reserved for virtual builditems")
            sys.exit(1)
        elif item["name"] not in namesExists:
            buildItemLog(item)
            namesExists.append(item["name"])
        else:
            buildLog(f"ERROR: more than one builditem named {item['name']}")
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

def has_cwd_non_ascii_or_spaces():
    cwd = os.getcwd()
    return any(ord(ch) > 127 or ch == ' ' for ch in cwd)

def start_build_in_chroot(json_path, all_args, nspawn_mode=False):
    if nspawn_mode:
        build_in_chroot_script_path = "/opt/syslbuild/build_in_chroot_nspawn.sh"
    else:
        build_in_chroot_script_path = "/opt/syslbuild/build_in_chroot.sh"

    chroot_directory = "/opt/syslbuild_chroot"
    if os.path.isfile(build_in_chroot_script_path) and os.path.isdir(chroot_directory):
        print(f"RUN BUILD IN CHROOT: {chroot_directory}")
        print(f"ARGS: {all_args}")

        cmdstr = f"{build_in_chroot_script_path} \"{os.path.abspath(json_path)}\""

        for arg in all_args:
            cmdstr += f" {arg}"

        print(f"CMD: {cmdstr}")

        subprocess.run(cmdstr, shell=True)
        exit(0)

import builditem_base

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="an assembly system for creating Linux distributions. it is focused on embedded distributions")
    parser.add_argument("--arch", choices=["ALL", "amd64", "i386", "arm64", "armhf", "armel"], type=str, required=True, help="the processor architecture for which the build will be made")
    parser.add_argument("--filters", type=str, help="specify build filters to assemble specific project elements. multiple filters can be specified via \",\"")
    parser.add_argument("--output", type=str, help="path to output directory")
    parser.add_argument("--temp", type=str, help="path to .temp directory")
    parser.add_argument("--lastlog", type=str, help="additional log file")
    parser.add_argument("json_path", type=str, help="the path to the json file of the project")
    parser.add_argument("-n", action="store_true", help="does the build anew, does not use the cache")
    parser.add_argument("-d", action="store_true", help="do not use the download cache of the kernel sources")
    parser.add_argument("-e", action="store_true", help="completely clears the entire cache before building")
    parser.add_argument("-g", action="store_true", help="deletes the files of the architecture being builded before building. saves downloaded kernel sources")
    parser.add_argument("--enable-chroot", action="store_true", help="enable the build inside the chroot container")
    args = parser.parse_args()
    
    requireRoot()
    if args.enable_chroot:
        all_args = sys.argv[1:]
        json_path = args.json_path
        all_args.pop(all_args.index(json_path))
        start_build_in_chroot(json_path, all_args, True)

    if args.temp:
        path_temp = args.temp
    
    if args.output:
        path_output = args.output

    if args.filters:
        filters = args.filters.split(",")
    else:
        filters = []
    
    architecture = args.arch
    saved_architecture = args.arch
    loadTempPaths()
    if args.e:
        deleteAny(path_temp)
        deleteAny(path_output)
    
    log_file = getLogFile()
    log_file2 = getLastLogFile()
    if args.lastlog:
        log_file3 = open(args.lastlog, "w")
        print(f"Log path: {log_file3}")
    else:
        log_file3 = None

    buildLog("Syslbuild info:")
    buildLog(f"Syslbuild version: {version.formatVersion(version.VERSION)}")
    buildLog(f"Syslbuild working directory: {os.getcwd()}")
    buildLog(";")

    if has_cwd_non_ascii_or_spaces():
        buildLog(f"WARNING: there are non-ascii or spaces characters in the path to the working directory. THIS MAY CAUSE BUILD PROBLEMS!")

    with open(args.json_path, "r", encoding="utf-8") as f:
        projectData = json5.load(f)
        showProjectInfo(projectData)
        if not version.checkVersion(projectData):
            buildLog(f"ERROR: the project requires at least the syslbuild {version.formatVersion(projectData['min-syslbuild-version'])} version. you have {version.formatVersion(version.VERSION)} installed")
            sys.exit(1)

        if architecture == "ALL":
            if "architectures" in projectData:
                global_architectures = projectData["architectures"]

                buildLog("build for the following list of architectures:")
                for arch in projectData["architectures"]:
                    buildLog(arch)
                buildLog(";")

                architecture = "independent"
                loadTempPaths()
                buildProject(args.json_path)
                
                for arch in projectData["architectures"]:
                    architecture = arch
                    loadTempPaths()
                    buildProject(args.json_path)
            else:
                buildLog("Architectures list is not defined in project json")
        else:
            global_architectures = [saved_architecture]

            architecture = "independent"
            loadTempPaths()
            buildProject(args.json_path)
            
            architecture = saved_architecture
            loadTempPaths()
            buildProject(args.json_path)

    changeOutputRights(path_output)
    
