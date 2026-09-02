from __main__ import *
import __main__
import funcs

# --------------------------------------------------------------------- builditems

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

    kernelName += debianKernelArchitectureAliases.get(__main__.architecture, __main__.architecture)

    return kernelName

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

    cmd = ["mmdebstrap", "--arch", __main__.architecture, "--variant", variant]
    if "components" in item:
        components_line = " ".join(item["components"])
        cmd.append(f"--components={components_line}")
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
        funcs.makeAllFilesExecutable(item["hook-directory"])
        cmd.append(f"--hook-directory={item['hook-directory']}")
    buildExecute(cmd)

    hostsFile = """127.0.0.1 localhost
127.0.1.1 hostname"""

    path_etc = pathConcat(itemFolder, "etc")
    funcs.makedirsChangeRights(path_etc, [0, 0, "0755"])

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

        funcs.changeAccessRights(path_hosts, [0, 0, "0644"])

    if not os.path.exists(path_resolv_conf) and not os.path.lexists(path_resolv_conf):
        with open(path_resolv_conf, "w") as f:
            f.write("nameserver 1.1.1.1\n")
            f.write("nameserver 1.0.0.1\n")
            f.write("nameserver 2606:4700:4700::1111\n")
            f.write("nameserver 2606:4700:4700::1001\n")
        
        funcs.changeAccessRights(path_resolv_conf, [0, 0, "0644"])

def makePacmanConfig(pacman_conf):
    lines = []

    for section, values in pacman_conf.items():
        lines.append(f"[{section}]")
        for key, val in values.items():
            lines.append(f"{key} = {val}")
        lines.append("")

    with open(__main__.path_temp_pacman_conf, "w") as f:
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
        pacman_conf["options"]["Architecture"] = pacman_architectures_names[__main__.architecture]
    
    if "CacheDir" not in pacman_conf["options"]:
        pacman_conf["options"]["CacheDir"] = __main__.path_temp_cache_pacman
    
    makePacmanConfig(pacman_conf)
    prepairPacman(pacman_conf)

def archLinuxBuild(item):
    makeExtendedPacmanConfig(item["pacman_conf"])
    root_path = getItemFolder(item)

    cmd = ["pacstrap", "-M", "-C", __main__.path_temp_pacman_conf, root_path]
    if item.get("withoutDependencies", False):
        cmd.append("--nodeps")
    cmd += item.get("include", [])

    buildExecute(cmd)

def archLinuxPackage(item):
    makeExtendedPacmanConfig(item["pacman_conf"])
    root_path = getItemFolder(item)

    cmd = ["pacman", "-r", root_path, "-C", __main__.path_temp_pacman_conf, "-Sy", "--noconfirm"]
    if item.get("withoutDependencies", False):
        cmd.append("--nodeps")
    cmd.append(item["package"])

    buildExecute(cmd)

def grubIsoImage(item):
    tempPath = getTempFolder("isotemp")

    bootDirectory = pathConcat(tempPath, "boot")
    funcs.makedirsChangeRights(bootDirectory)

    grubDirectory = pathConcat(bootDirectory, "grub")
    funcs.makedirsChangeRights(grubDirectory)

    if "kernel" in item:
        copyItemFiles(findItem(item["kernel"]), pathConcat(bootDirectory, "vmlinuz"), DEFAULT_RIGHTS_0700)

    if "initramfs" in item:
        copyItemFiles(findItem(item["initramfs"]), pathConcat(bootDirectory, "initrd.img"), DEFAULT_RIGHTS_0700)

    grub_cfg_path = pathConcat(grubDirectory, "grub.cfg")
    if "config" in item:
        copyItemFiles(findItem(item["config"]), grub_cfg_path, DEFAULT_RIGHTS_0700)
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
        funcs.changeAccessRights(grub_cfg_path, DEFAULT_RIGHTS_0700)

    cmd = ["grub-mkrescue", "-o", getItemPath(item), tempPath]
    if "modules" in item:
        cmd.append("--modules=\"" + " ".join(item["modules"]) + "\"")
    buildExecute(cmd)

def unpackInitramfs(item):
    initramfs = os.path.abspath(findItem(item["initramfs"]))
    folder = getItemFolder(item)

    buildRawExecute(f"{item.get('decompressor', 'cat')} \"{initramfs}\" | cpio -idmv", True, folder)

def downloadFile(url, path):
    buildLog(f"Downloading file ({url}): {path}")
    buildExecute(["wget", "-O", path, url])

def buildDownload(item):
    downloadFile(item["url"], getItemPath(item))

"""
def funcs.changeAccessRights(path, changeRights):
    if len(changeRights) >= 3 and changeRights[2]:
        buildExecute(["chmod", "-R", changeRights[2], path])
    
    chownString = chownStr(changeRights[0], changeRights[1])
    if chownString:
        buildExecute(["chown", "-R", chownString, path])
"""

def copyItemFiles(fromPath, toPath, changeRights=None, allowSymlinks=True, copySymlinksAsFiles=False):
    rsync_arg = "-a"
    if copySymlinksAsFiles:
        rsync_arg += "L"

    if os.path.isdir(fromPath):
        funcs.makedirsChangeRights(toPath)
        if allowSymlinks:
            if changeRights:
                tempFolder = getTempFolder("changeRights")
                buildExecute(["cp", "-a", fromPath + "/.", tempFolder])
                funcs.changeAccessRights(tempFolder, changeRights) # рекурсивно устанавливаем права доступа для всего внутри каталога
                buildExecute(["chmod", "--reference=" + toPath, tempFolder]) # не меняем права доступа на сам каталог, для этого переносим оригинальные на него
                buildExecute(["chown", "--reference=" + toPath, tempFolder])
                buildExecute(["rsync", rsync_arg, "--keep-dirlinks", tempFolder + "/.", toPath])
            else:
                buildExecute(["rsync", rsync_arg, "--keep-dirlinks", fromPath + "/.", toPath])
        else:
            if changeRights:
                tempFolder = getTempFolder("changeRights")
                buildExecute(["cp", "-a", fromPath + "/.", tempFolder])
                funcs.changeAccessRights(tempFolder, changeRights)
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
            funcs.makedirsChangeRights(file_dir)

        if allowSymlinks:
            buildExecute(["rsync", rsync_arg, "--keep-dirlinks", fromPath, toPath])
        else:
            shutil.copy2(fromPath, toPath)

        if changeRights:
            funcs.changeAccessRights(toPath, changeRights)

def writeRawItem(raw, toPath, changeRights=None):
    deleteAny(toPath)

    file_dir = os.path.dirname(toPath)
    if not os.path.isdir(file_dir):
        funcs.makedirsChangeRights(file_dir)

    with open(toPath, "w") as f:
        f.write(raw)

    if changeRights:
        funcs.changeAccessRights(toPath, changeRights)

def allocateFile(path, size):
    buildLog(f"Allocation file with size {size}: {path}")

    buildExecute([
        "dd",
        "if=/dev/zero",
        f"of={path}",
        f"bs={DD_BS}",
        f"count={size}",
        "iflag=count_bytes"
    ])

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

    if "revision" in item:
        if "fat" not in fs_type:
            cmd.append("-r")
            cmd.append(str(item["revision"]))

    if fs_subtype is not None:
        cmd.append("-F")
        cmd.append(str(fs_subtype))
    
    cmd.append(path)
    buildExecute(cmd)

def rawItemsProcess(items, itemsDirectory):
    for itemObj in items:
        outputPath = pathConcat(itemsDirectory, itemObj[1])

        changeRights = None
        if len(itemObj) >= 3:
            changeRights = itemObj[2]

        writeRaw = False
        if len(itemObj) >= 4:
            writeRaw = itemObj[3]
        
        if writeRaw:
            rawItem = itemObj[0]
            buildLog(f"Write item: {rawItem} > {outputPath}")
        elif itemObj[0].startswith("&"):
            itemObj[0] = itemObj[0][1:]
            itemPath = itemObj[0]
            buildLog(f"Copy global path item: {itemPath} > {outputPath}")
        else:
            parts = itemObj[0].split('/', 1)
            if len(parts) == 2:
                itemObj[0], inItemPath = parts
            else:
                inItemPath = None

            itemPath = findItem(itemObj[0])
            if inItemPath:
                buildLog(f"Copy item with path: {{{itemPath}}}/{{{inItemPath}}} > {outputPath}")
                itemPath += "/" + inItemPath
            else:
                buildLog(f"Copy item: {itemPath} > {outputPath}")
            
        # так как папка с проектом может переносится через разные файловые системы
        # и системы контроля версий
        # права доступа на файлы из проекта должны быть указаны в конфиге проекта
        # а не в самих файлов проекта
        if not changeRights and (writeRaw or funcs.isUserItem(itemObj[0])):
            changeRights = DEFAULT_RIGHTS_0700
        
        if changeRights:
            buildLog(f"With custom rights: {changeRights}")
        
        if writeRaw:
            writeRawItem(rawItem, outputPath, changeRights)
        else:
            copyItemFiles(itemPath, outputPath, changeRights)

def handlelink(topdir, filep, subdir):
    link = os.readlink(filep)
    if link[0] != "/":
        return
    if link.startswith(topdir):
        return

    relative_path = os.path.relpath(topdir+link, subdir)
    
    buildLog("Replacing %s with %s for %s" % (link, relative_path, filep))
    
    os.unlink(filep)
    os.symlink(relative_path, filep)

    new_link = os.readlink(filep)
    buildLog("NEW LINK: %s" % new_link)

def make_relative_symlinks(topdir):
    topdir = os.path.abspath(topdir)
    buildLog(f"make_relative_symlinks: {topdir}")
    for subdir, dirs, files in os.walk(topdir):
        for f in dirs:
            filep = os.path.join(subdir, f)
            if os.path.islink(filep):
                handlelink(topdir, filep, subdir)

        for f in files:
            filep = os.path.join(subdir, f)
            if os.path.islink(filep):
                handlelink(topdir, filep, subdir)

def buildMove(buildDirectoryPath, fromPath, toPath):
    fromPath = pathConcat(buildDirectoryPath, fromPath)
    toPath = pathConcat(buildDirectoryPath, toPath)

    buildExecute(["rsync", "-aK", "--remove-source-files", fromPath + "/", toPath + "/"])
    buildExecute(["rm", "-rf", fromPath])

def buildDirectory(item):
    buildDirectoryPath = getItemFolder(item)

    if "move" in item:
        for move in item["move"]:
            buildMove(buildDirectoryPath, move[0], move[1])

    if "symlinks" in item:
        for symlink in item["symlinks"]:
            buildExecute(["ln", "-sfn", symlink[0], pathConcat(buildDirectoryPath, symlink[1])])

    make_relative_symlinks(buildDirectoryPath)

    if "deleteBeforeAdd" in item:
        for deletePath in item["deleteBeforeAdd"]:
            deleteAny(pathConcat(buildDirectoryPath, deletePath))

    if "directories" in item:
        for directoryData in item["directories"]:
            directoryPath = pathConcat(buildDirectoryPath, directoryData[0])

            changeRights = DEFAULT_RIGHTS_0700
            if len(directoryData) >= 2:
                changeRights = directoryData[1]

            chainRights = None
            if len(directoryData) >= 3:
                chainRights = directoryData[2]

            buildLog(f"Create empty directory: {directoryPath} {changeRights} {chainRights}")
            funcs.makedirsChangeRights(directoryPath, changeRights, chainRights)

    if "items" in item:
        rawItemsProcess(item["items"], buildDirectoryPath)
        make_relative_symlinks(buildDirectoryPath)

    if "move_after_items" in item:
        for move in item["move_after_items"]:
            buildMove(buildDirectoryPath, move[0], move[1])

    if "symlinks_after_items" in item:
        for symlink in item["symlinks_after_items"]:
            buildExecute(["ln", "-sfn", symlink[0], pathConcat(buildDirectoryPath, symlink[1])])

        make_relative_symlinks(buildDirectoryPath)

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
        compress = "z"
    elif readBool(item, "xz"):
        compress = "J"
    else:
        compress = ""

    buildExecute(["tar", "-c" + compress + "f", tar_path, "-C", tar_files, "."])

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

    if fs_files or "chmod" in item or "chown" in item:
        mountFilesystem(fs_path, __main__.path_mount)

        if fs_files:
            copyItemFiles(fs_files, __main__.path_mount)

        if "chmod" in item:
            makeChmod(__main__.path_mount, item["chmod"])

        if "chown" in item:
            makeChown(__main__.path_mount, item["chown"])

        umountFilesystem(__main__.path_mount)


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
        return parititionTypesList_gpt.get(partitionType, partitionType)
    else:
        return parititionTypesList_dos.get(partitionType, partitionType)

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
        target = defaultGrubTargets_efi.get(__main__.architecture)
    else:
        target = defaultGrubTargets_bios.get(__main__.architecture)

    if target is None:
        buildLog(f"ERROR: unknown grub target for {__main__.architecture} ({'efi' if efi else 'bios'})")
        sys.exit(1)

    return target

def getGrubInstallCmd(bootloaderInfo, grub_target, arr):
    arr.insert(0, f"--target={grub_target}")

    if bootloaderInfo.get("build") is not None:
        arr.insert(0, f"--directory={findItem(bootloaderInfo.get("build"))}/{grub_target}")
    elif bootloaderInfo.get("builddir") is not None:
        arr.insert(0, f"--directory={findItem(bootloaderInfo.get("builddir"))}")
    
    arr.insert(0, "grub-install")
    return arr

def installBootloader(item, path, partitionsOffsets, sectorsize):
    bootloaderInfo = item["bootloader"]
    bootloaderType = bootloaderInfo["type"]

    if bootloaderType == "grub":
        efi = False

        mountFilesystem(path, __main__.path_mount, partitionsOffsets[bootloaderInfo["boot"]])
        if "esp" in bootloaderInfo:
            mountFilesystem(path, __main__.path_mount2, partitionsOffsets[bootloaderInfo["esp"]])
            efi = True

        bootDirectory = pathConcat(__main__.path_mount, "boot")
        funcs.makedirsChangeRights(bootDirectory)

        modulesString = ""
        if "modules" in bootloaderInfo:
            modulesString = " ".join(bootloaderInfo["modules"])

        install_extra_args = []
        if "install_extra_args" in bootloaderInfo:
            install_extra_args = bootloaderInfo["install_extra_args"]

        if efi:
            buildExecute(getGrubInstallCmd(bootloaderInfo, getGrubTarget(item, True), install_extra_args + [f"--modules={modulesString}", f"--boot-directory={bootDirectory}", f"--efi-directory={__main__.path_mount2}", "--removable", path]))

            # in EFI mode, grub-install writes grub files to the /efi/boot directory, while grub itself searches for them simply by following the /boot/grub path
            # Thanks to the grub developers
            grubdir = os.path.join(__main__.path_mount2, "boot", "grub")
            funcs.makedirsChangeRights(grubdir)
            buildExecute(["cp", "-a", os.path.join(__main__.path_mount2, "efi", "boot") + "/.", grubdir])

            if readBool(bootloaderInfo, "efiAndBios"):
                buildExecute(getGrubInstallCmd(bootloaderInfo, getGrubTarget(item, False), install_extra_args + [f"--modules={modulesString}", f"--boot-directory={bootDirectory}", path]))
        else:
            buildExecute(getGrubInstallCmd(bootloaderInfo, getGrubTarget(item, False), install_extra_args + [f"--modules={modulesString}", f"--boot-directory={bootDirectory}", path]))

        if "config" in bootloaderInfo:
            funcs.makedirsChangeRights(pathConcat(bootDirectory, "grub"))
            copyItemFiles(findItem(bootloaderInfo["config"]), pathConcat(bootDirectory, "grub", "grub.cfg"), DEFAULT_RIGHTS_0700)

        umountFilesystem(__main__.path_mount)

        if efi:
            umountFilesystem(__main__.path_mount2)
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
                f"bs={DD_BS}",
                f"seek={bootloaderOffsetBytes}",
                "conv=notrunc",
                "status=progress",
                "oflag=seek_bytes"
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
    partitionTable = f"label: {item['partitionTable']}"

    if "partitionsStartSector" in item:
        partitionTable += f"\nfirst-lba: {item['partitionsStartSector']}"

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
        start_bytes = start_sector * resultSectorsize
        partitionsOffsets.append(start_bytes)
        buildExecute([
            "dd",
            f"if={partitionsPaths[i]}",
            f"of={path}",
            f"bs={DD_BS}",
            f"seek={start_bytes}",
            "conv=notrunc",
            "status=progress",
            "oflag=seek_bytes"
        ])

    # install bootloader
    if "bootloader" in item:
        installBootloader(item, path, partitionsOffsets, resultSectorsize)

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
    exts = item.get("sources-dirs-extensions", None) # optional. if this is not specified, syslbuild will take all files.
    exclude = item.get("sources-dirs-exclude", [])

    def is_excluded(path):
        name = os.path.basename(path)
        return any(name == ex or path.endswith(ex) for ex in exclude)

    for d in dirs:
        d = findItem(d)

        if recursive:
            for root, _, files in os.walk(d):
                for f in files:
                    full = os.path.join(root, f)

                    if is_excluded(full):
                        continue

                    if exts is None or any(f.endswith(ext) for ext in exts):
                        sources.append(full)

        else:
            for f in os.listdir(d):
                full = os.path.join(d, f)

                if not os.path.isfile(full):
                    continue

                if is_excluded(full):
                    continue

                if exts is None or any(f.endswith(ext) for ext in exts):
                    sources.append(full)

    return sources

def gccBuild(item):
    gccargs = [gccNames[__main__.architecture] + "-gcc"]

    if "sysroot" in item:
        gccargs += ["--sysroot=" + findItem(item["sysroot"])]

    gccargs += item.get("CFLAGS", [])
    gccargs += item.get("sources", collect_sources(item))
    gccargs += item.get("LDFLAGS", [])
    gccargs += ["-o", getItemPath(item)]

    buildExecute(gccargs)

def buildInitramfs(item):
    source = findDirectory(item)
    realOutputPath = os.path.abspath(getItemPath(item))
    
    if "compressor" in item:
        outputPath = os.path.abspath(getTempPath("temp.cpio"))
    else:
        outputPath = realOutputPath

    buildRawExecute(f"find . -print0 | cpio --null -ov --format=newc > \"{outputPath}\"", True, source)

    if "compressor" in item:
        buildRawExecute(f"{item['compressor']} < \"{outputPath}\" > \"{realOutputPath}\"", True)

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
    kernel_sources = pathConcat(__main__.path_temp_kernel_sources, url_hash)
    kernel_sources_downloaded_flag = pathConcat(__main__.path_temp_kernel_sources, url_hash + ".downloaded")
    kernel_sources_archive = pathConcat(__main__.path_temp_kernel_sources, url_hash + get_file_extension(url))

    if __main__.args.d or not os.path.isdir(kernel_sources) or not os.path.isfile(kernel_sources_downloaded_flag):
        deleteAny(kernel_sources)
        os.makedirs(kernel_sources, exist_ok=True)
        downloadFile(url, kernel_sources_archive)
        buildRawExecute(unpacker % (kernel_sources_archive, kernel_sources))
        emptyFile(kernel_sources_downloaded_flag)
    
    return kernel_sources

def downloadKernelFromGit(item):
    url = item["kernel_source_git"]

    url_hash = hashlib.md5(url.encode('utf-8') + item.get("kernel_source_git_branch", "").encode('utf-8') + item.get("kernel_source_git_checkout", "").encode('utf-8')).hexdigest()
    kernel_sources = pathConcat(__main__.path_temp_kernel_sources, url_hash)
    kernel_sources_downloaded_flag = pathConcat(__main__.path_temp_kernel_sources, url_hash + ".downloaded")

    if __main__.args.d or not os.path.isdir(kernel_sources) or not os.path.isfile(kernel_sources_downloaded_flag):
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
    patches_checksum = {"array": []}

    for command in item.get("pre_patches_commands", []):
        patches_checksum["array"].append(get_file_checksum(command))

    for file in item.get("patches", []):
        patches_checksum["array"].append(get_file_checksum(findItem(file)))

    for command in item.get("post_patches_commands", []):
        patches_checksum["array"].append(get_file_checksum(command))
        
    patches_checksum = dictChecksum(patches_checksum)

    copied_kernel_files = pathConcat(__main__.path_temp_kernel_build, hashlib.md5((kernel_sources + ":" + patches_checksum).encode("utf-8")).hexdigest())
    out_of_tree_dir = copied_kernel_files + "_build"
    copied_kernel_files_flag = pathConcat(copied_kernel_files, ".copied")
    patched_kernel_files_flag = pathConcat(copied_kernel_files, ".patched")

    if not os.path.isdir(copied_kernel_files) or not os.path.isfile(copied_kernel_files_flag) or not os.path.isfile(patched_kernel_files_flag):
        deleteDirectory(copied_kernel_files)
        os.makedirs(copied_kernel_files, exist_ok=True)

        deleteDirectory(out_of_tree_dir)
        os.makedirs(out_of_tree_dir, exist_ok=True)

        copyItemFiles(kernel_sources, copied_kernel_files)
        with open(copied_kernel_files_flag, "w") as f:
            pass
        return copied_kernel_files, out_of_tree_dir, True

    return copied_kernel_files, out_of_tree_dir, False

def auto_patch_dt_makefile(git_work_dir: str, dt_rel_dir: str, config_var: str, add_only: bool = True) -> bool:
    """
    Автоматически патчит Makefile в указанной директории с Device Tree.
    Находит все .dts файлы и добавляет их в Makefile, если они ещё не добавлены.

    Аргументы:
        git_work_dir (str): Абсолютный путь к корню исходников ядра.
        dt_rel_dir (str): Относительный путь к целевой директории (например, "arch/arm/boot/dts/allwinner").
        config_var (str): Переменная конфигурации ядра (например, "CONFIG_ARCH_SUNXI").
        add_only (bool): Если True, только добавляет недостающие записи (безопасный режим).
                         Если False, полностью перезаписывает секцию dtb-... всеми найденными .dts.

    Возвращает:
        bool: True в случае успеха, иначе завершает работу через sys.exit(1).
    """
    # 1. Формируем полные пути
    dts_dir = Path(git_work_dir) / dt_rel_dir
    makefile_path = dts_dir / "Makefile"

    if not dts_dir.is_dir():
        buildLog(f"ERROR: Directory not found: {dts_dir}")
        sys.exit(1)

    # 2. Находим все .dts файлы (только в самой директории, не рекурсивно)
    dts_files = sorted([f.name for f in dts_dir.glob("*.dts") if f.is_file()])
    if not dts_files:
        buildLog(f"WARNING: No .dts files found in {dts_dir}")
        return True  # Не ошибка, просто нет файлов

    # 3. Читаем текущий Makefile, если он существует
    if not makefile_path.exists():
        buildLog(f"ERROR: Makefile not found: {makefile_path}")
        sys.exit(1)

    with open(makefile_path, 'r') as f:
        lines = f.readlines()

    # 4. Извлекаем все существующие имена .dtb (без расширения) из строк вида:
    #    dtb-$(CONFIG_XXX) += имя.dtb
    #    или многострочных: dtb-$(CONFIG_XXX) += \ ... \t имя.dtb
    existing_dtbs = set()
    dtb_regex = re.compile(r'^dtb-\$\([^)]+\)\s*\+=\s*(.*)$')
    multi_dtb_regex = re.compile(r'^\s*([\w\-]+)\.dtb\s*(\\?)$')

    for line in lines:
        line = line.rstrip()
        m = dtb_regex.match(line)
        if m:
            # Одиночная или начальная строка с обратным слешом
            rest = m.group(1).strip()
            if rest.endswith('\\'):
                rest = rest[:-1].strip()
                # Это начало многострочного блока — нужно собрать все имена
                # Мы просто извлечём все .dtb из этой и последующих строк
                # (упрощённо: будем искать все упоминания .dtb в строке)
                for token in re.findall(r'([\w\-]+)\.dtb', rest):
                    existing_dtbs.add(token)
                # Также нужно пройти по следующим строкам, пока не встретим строку без \ в конце
                # но для простоты мы можем просто собрать все .dtb из всего файла, это надежнее.
                # Но мы уже сделаем отдельный поиск по всему файлу чуть ниже.
            else:
                # Одиночная запись
                for token in re.findall(r'([\w\-]+)\.dtb', rest):
                    existing_dtbs.add(token)

    # Дополнительно пройдёмся по всему файлу, чтобы собрать все .dtb упоминания
    # (это покроет многострочные блоки)
    all_dtb_matches = re.findall(r'([\w\-]+)\.dtb', ''.join(lines))
    existing_dtbs.update(all_dtb_matches)

    # 5. Определяем, какие .dts нужно добавить
    new_dtbs = []
    for dts in dts_files:
        dtb_name = dts.replace('.dts', '')
        if dtb_name not in existing_dtbs:
            new_dtbs.append(dtb_name)

    if not new_dtbs:
        buildLog(f"No new DTB files to add in {dt_rel_dir}")
        return True

    # 6. Патчим Makefile
    if add_only:
        # Режим "только добавление": дописываем новые записи в конец файла
        buildLog(f"Adding {len(new_dtbs)} new DTB entries to {makefile_path}")
        with open(makefile_path, 'a') as f:
            f.write(f"\n# Auto-added by Armbian patch (add-only)\n")
            for dtb in new_dtbs:
                f.write(f"dtb-$({config_var}) += {dtb}.dtb\n")
            f.write("# End of auto-added entries\n")
    else:
        # Режим "полной замены": пересоздаём секцию dtb-... со всеми найденными .dts
        buildLog(f"REPLACING DTB section in {makefile_path} with all {len(dts_files)} entries")
        # Находим диапазон строк, содержащих dtb-$(...), и заменяем их
        # Для простоты мы удалим все строки между первой и последней строкой с dtb-...,
        # и вставим новые строки на их место.
        first_idx = None
        last_idx = None
        for i, line in enumerate(lines):
            if re.search(r'^dtb-\$\([^)]+\)\s*\+=', line):
                if first_idx is None:
                    first_idx = i
                last_idx = i

        if first_idx is None:
            # Если нет ни одной строки с dtb-..., то добавляем в конец файла
            buildLog("No existing dtb-... section found, appending to end")
            with open(makefile_path, 'a') as f:
                f.write(f"\n# Auto-added by Armbian patch (full replace)\n")
                # Определяем стиль: если больше 5 файлов, используем многострочный формат
                if len(dts_files) > 5:
                    f.write(f"dtb-$({config_var}) += \\\n")
                    for dts in dts_files:
                        dtb = dts.replace('.dts', '')
                        f.write(f"\t{dtb}.dtb \\\n")
                    f.write("\n")
                else:
                    for dts in dts_files:
                        dtb = dts.replace('.dts', '')
                        f.write(f"dtb-$({config_var}) += {dtb}.dtb\n")
                f.write("# End of auto-added entries\n")
        else:
            # Заменяем строки с first_idx по last_idx включительно
            new_lines = lines[:first_idx]
            # Добавляем комментарий
            new_lines.append("# Auto-generated DTB entries\n")
            if len(dts_files) > 5:
                new_lines.append(f"dtb-$({config_var}) += \\\n")
                for dts in dts_files:
                    dtb = dts.replace('.dts', '')
                    new_lines.append(f"\t{dtb}.dtb \\\n")
                new_lines.append("\n")
            else:
                for dts in dts_files:
                    dtb = dts.replace('.dts', '')
                    new_lines.append(f"dtb-$({config_var}) += {dtb}.dtb\n")
            new_lines.extend(lines[last_idx+1:])
            with open(makefile_path, 'w') as f:
                f.writelines(new_lines)

    # 7. Проверяем наличие поддиректории overlay и добавляем её, если нужно
    overlay_dir = dts_dir / "overlay"
    if overlay_dir.is_dir() and (overlay_dir / "Makefile").exists():
        # Проверяем, есть ли уже строка subdir-y += overlay
        with open(makefile_path, 'r') as f:
            content = f.read()
        if "subdir-y += overlay" not in content:
            buildLog(f"Adding overlay subdir to {makefile_path}")
            with open(makefile_path, 'a') as f:
                f.write(f"\n# Support for overlays\n")
                f.write(f"subdir-y += overlay\n")

    buildLog(f"Successfully patched {makefile_path}")
    return True

def read_series_conf(series_path: str, prefix: str) -> list:
    buildLog(f"read_series_conf: {series_path}, {prefix}")

    patches = []
    try:
        with open(series_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Пропускаем комментарии
                if line.startswith('#') or line.startswith('-'):
                    continue

                # Отбрасываем комментарий внутри строки (если есть)
                if '#' in line:
                    line = line.split('#', 1)[0].strip()
                    if not line:
                        continue

                # Берём первый токен (имя файла), остальное игнорируем
                tokens = line.split()
                if tokens:
                    patch_name = tokens[0]
                    patches.append(prefix + patch_name)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {series_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading {series_path}: {e}")

    buildLog(f"read_series_conf count: {len(patches)}")

    return patches

def applyPatches(sources, item):
    if "items_before_patches" in item:
        rawItemsProcess(item["items_before_patches"], sources)

    doCommands(sources, item.get("pre_patches_commands", None))

    patches = item.get("patches", [])
    if "read_series_conf" in item:
        additional_patches = []

        for read_series_conf_part in item["read_series_conf"]:
            additional_patches += read_series_conf(findItem(read_series_conf_part[0]), read_series_conf_part[1])
        
        patches += additional_patches

    if patches:
        patches_ignore_errors = item.get("patches_ignore_errors", False)
        patches_additional_args = item.get("patches_additional_args", "")

        for patchPath in patches:
            buildRawExecute(f"patch -p1 {patches_additional_args} < {os.path.abspath(findItem(patchPath))}", not patches_ignore_errors, sources)

    doCommands(sources, item.get("post_patches_commands", None))

    if "items_after_patches" in item:
        rawItemsProcess(item["items_after_patches"], sources)

    if "auto_patch_dt_makefile" in item:
        for auto_patch in item["auto_patch_dt_makefile"]:
            auto_patch_dt_makefile(sources, auto_patch[0], auto_patch[1], auto_patch[2])

    doCommands(sources, item.get("patches_complete_commands", None))

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

def update_kernel_config(kernel_sources, ARCH_STR, CROSS_COMPILE_STR, build_output_dir):
    arr = ["make", ARCH_STR, CROSS_COMPILE_STR, "olddefconfig"]
    if build_output_dir is not None:
        arr.insert(1, f"O={build_output_dir}")
    buildExecute(arr, True, None, kernel_sources)

def parse_kernel_config(config_file):
    with open(config_file, "r") as f:
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

def kernel_config_embed_all_modules(kernel_config_path):
    buildLog(f"kernel_config_embed_all_modules: {kernel_config_path}")

    with open(kernel_config_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        line = line.strip()
        if not line.startswith(f"#") and line.endswith(f"=m"):
            new_lines.append(line.split("=", 1)[0] + "=y" + "\n")
            print("change", line.split("=", 1)[0] + "=y")
        else:
            new_lines.append(line + "\n")

    with open(kernel_config_path, "w") as f:
        f.writelines(new_lines)

def modifyKernelConfig(item, kernel_sources, ARCH_STR, CROSS_COMPILE_STR, build_output_dir):
    kernel_config_path = pathConcat(build_output_dir if build_output_dir else kernel_sources, ".config")
    buildLog(f"modifyKernelConfig: {kernel_sources} {build_output_dir}")

    if "kernel_config_changes_files" in item:
        for changes_file in item["kernel_config_changes_files"]:
            for change in parse_kernel_config(findItem(changes_file)):
                set_kernel_config_parameter(kernel_config_path, change[0], change[1])

    if "kernel_config_changes" in item:
        for change in item["kernel_config_changes"]:
            set_kernel_config_parameter(kernel_config_path, change[0], change[1])

    if not item.get("kernel_config_disable_default_changes", False):
        # I'm disabling this for some patches to work correctly
        set_kernel_config_parameter(kernel_config_path, "CONFIG_WERROR", "n")

        set_kernel_config_parameter(kernel_config_path, "CONFIG_RD_GZIP", "y")

    update_kernel_config(kernel_sources, ARCH_STR, CROSS_COMPILE_STR, build_output_dir)

    if item.get("kernel_config_embed_all_modules", False):
        kernel_config_embed_all_modules(kernel_config_path)

def additionalExportProcess(export_from, additional_export_list):
    for additional_export_item in additional_export_list:
        object_path = pathConcat(export_from, additional_export_item[0])
        copyItemFiles(object_path, getCustomItemPath(additional_export_item[1], additional_export_item[2]), None, True, True)

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

    kernel_sources, out_of_tree_dir, realCopied = copyKernel(item, downloaded_kernel_sources)

    build_output_dir = None
    if item.get("out_of_tree", False):
        build_output_dir = out_of_tree_dir

    if build_output_dir:
        build_output_dir = os.path.abspath(build_output_dir)
        os.makedirs(build_output_dir, exist_ok=True)
        buildLog(f"Out‑of‑tree build enabled, output directory: {build_output_dir}")

    build_output_dir_or_sources = build_output_dir if build_output_dir else kernel_sources
    
    # ------------------------------------------------

    if "items" in item:
        rawItemsProcess(item["items"], kernel_sources)

    if realCopied:
        applyPatches(kernel_sources, item)
        
        # записываю .patched флаг даже если реальных патчей ядра не указано
        # это нужно чтобы при следующей сборки не копировать файлы ядра заного
        patched_kernel_files_flag = pathConcat(kernel_sources, ".patched")
        with open(patched_kernel_files_flag, "w") as f:
            pass

    if item.get("only_test_patches", False):
        return

    ARCH = kernelArchitectures[__main__.architecture]
    CROSS_COMPILE = gccNames[__main__.architecture]
    ARCH_STR = f"ARCH={ARCH}"
    CROSS_COMPILE_STR = f"CROSS_COMPILE={CROSS_COMPILE}-"
    DEFCONFIG_NAME = item.get("defconfig", kernelArchitectureConfigs.get(__main__.architecture, "defconfig"))

    def make_cmd(base_cmd):
        cmd = ["make"]
        if build_output_dir:
            cmd.append(f"O={build_output_dir}")
        cmd.extend(base_cmd)
        return cmd

    def make_raw_cmd(cmd_str):
        if build_output_dir:
            return f"make O={build_output_dir} {cmd_str}"
        return f"make {cmd_str}"
    
    # --------------------------------------------------------------

    buildExecute(make_cmd([ARCH_STR, CROSS_COMPILE_STR, DEFCONFIG_NAME]), True, None, kernel_sources)

    kernel_config_path = pathConcat(build_output_dir_or_sources, ".config")

    if "kernel_config" in item:
        buildLog(f"Copy kernel config to: {kernel_config_path}")
        copyItemFiles(findItem(item["kernel_config"]), kernel_config_path)

    modifyKernelConfig(item, kernel_sources, ARCH_STR, CROSS_COMPILE_STR, build_output_dir)
    buildExecute(make_cmd([ARCH_STR, CROSS_COMPILE_STR, "modules_prepare"]), True, None, kernel_sources)

    if "result_config_name" in item:
        buildLog(f"exporting result kernel config...")
        export_path = getItemPath(item, "result_config_name", "result_config_export")
        copyItemFiles(kernel_config_path, export_path, None, True, True)

    additional_make_str = ""
    if "additional_make_str" in item:
        additional_make_str = item["additional_make_str"] + " "

    buildRawExecute(make_raw_cmd(f"{additional_make_str}{ARCH_STR} {CROSS_COMPILE_STR} -j$(nproc)"), True, kernel_sources)

    kernel_output_filename = item.get("kernel_output_file", "bzImage")
    kernel_output_file = pathConcat(build_output_dir_or_sources, "arch", kernelArchitectures[__main__.architecture], "boot", kernel_output_filename)

    if not os.path.isfile(kernel_output_file):
        # запасной вариант: корень сборки / исходников
        fallback = pathConcat(build_output_dir_or_sources, kernel_output_filename)
        if os.path.isfile(fallback):
            kernel_output_file = fallback
        else:
            buildLog(f"ERROR: failed to find \"{kernel_output_filename}\" kernel output file")
            sys.exit(1)
    
    # -------------------------------------------------------------

    if os.path.isfile(kernel_output_file):
        copyItemFiles(kernel_output_file, getItemPath(item), None, True, True)
    else:
        buildLog(f"ERROR: failed to find \"{kernel_output_filename}\" kernel output file")
        sys.exit(1)

    if "modules_name" in item:
        buildLog(f"exporting modules...")
        export_path = getItemFolder(item, "modules_name", "modules_export")
        buildExecute(make_cmd([ARCH_STR, CROSS_COMPILE_STR, "modules_install", f"INSTALL_MOD_PATH={os.path.abspath(export_path)}"]), True, None, kernel_sources)
        funcs.recursionDeleleSymlinks(export_path)

    if "headers_name" in item:
        buildLog(f"exporting headers...")
        export_path = getItemFolder(item, "headers_name", "headers_export")
        buildExecute(make_cmd([ARCH_STR, CROSS_COMPILE_STR, "headers_install", f"INSTALL_HDR_PATH={os.path.abspath(export_path)}"]), True, None, kernel_sources)
        funcs.recursionDeleleSymlinks(export_path)

    if "symvers_name" in item:
        buildLog(f"exporting symvers...")
        additionalExportProcess(build_output_dir_or_sources, [
            ["Module.symvers", item["symvers_name"], item.get("symvers_export", False)],
        ])

    if "additional_export" in item:
        additionalExportProcess(build_output_dir_or_sources, item["additional_export"])

def buildPatches(item):
    itemPath = cloneBuildItem(item["source"], item)
    applyPatches(itemPath, item)

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
    if hostArchitecture == __main__.architecture:
        buildLog(f"the architectures of the host and the target system are the same ({__main__.architecture}) we do not use qemu-static")
        return False
    
    if hostArchitecture == "amd64" and __main__.architecture == "i386":
        buildLog(f"the host architecture ({hostArchitecture}) is compatible with the target architecture ({__main__.architecture}) we do not use qemu-static")
        return False

    buildLog(f"the host architecture ({hostArchitecture}) is NOT compatible with the target architecture ({__main__.architecture}), we use qemu-static")
    return True

def set_rules_755(path):
    buildExecute(["chmod", "0755", path])
    buildExecute(["chown", "0:0", path])

def rawCrossChroot(chrootDirectory, chrootCommand, useSystemd=False, manualValidation=False, item=None):
    if item is None:
        item = {}
    
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
    qemuStaticName = qemuStaticNames[__main__.architecture]
    qemuStaticHostPath = f"/usr/bin/{qemuStaticName}"
    qemuStaticPath = pathConcat(chrootDirectory, "usr/bin", qemuStaticName)
    qemuCopied = False

    dirCreatedForQemu_usr = False
    dirCreatedForQemu_usr_bin = False
    usr_dir = pathConcat(chrootDirectory, "usr")
    usr_bin_dir = pathConcat(chrootDirectory, "usr/bin")

    if boolCopyQemuStatic and not os.path.isfile(qemuStaticHostPath):
        buildLog(f"WARNING: there is no suitable version of qemu-static ({qemuStaticName}) in the host system. we are trying without it")
        boolCopyQemuStatic = False

    if boolCopyQemuStatic:
        if os.path.exists(qemuStaticPath):
            # надо добавить флаг чтобы можно было принудительно копировать qemu переименовывая старый а потом возврашая как было
            buildLog(f"qemu-static should have been copied, but the file with that name is already in the chroot directory. i'm skipping it ({qemuStaticName})")
        else:
            buildLog(f"copying qemu-static ({qemuStaticName})")
            qemuCopied = True

            if not os.path.exists(usr_dir):
                dirCreatedForQemu_usr = True
                os.makedirs(usr_dir)
                set_rules_755(usr_dir)

            if not os.path.exists(usr_bin_dir):
                dirCreatedForQemu_usr_bin = True
                os.makedirs(usr_bin_dir)
                set_rules_755(usr_bin_dir)

            buildExecute(["cp", "-a", qemuStaticHostPath, qemuStaticPath])
            set_rules_755(qemuStaticPath)

    fix_systemd_container_host_files_copy_list = [
        "/etc/localtime",
        "/etc/resolv.conf"
    ]

    checkValid = not manualValidation
    if useSystemd:
        fix_systemd_container_host_files_copy = item.get("fix_systemd_container_host_files_copy", False)
        if fix_systemd_container_host_files_copy:
            for localpath in fix_systemd_container_host_files_copy_list:
                old_path = pathConcat(chrootDirectory, localpath)
                new_path = pathConcat(chrootDirectory, localpath + "_")
                buildLog(f"fix_systemd_container_host_files_copy (start): {old_path} > {new_path}")
                copyItemFiles(old_path, new_path)

        machineName = "smartchroot"
        buildRawExecute(f"""machinectl terminate {machineName}
systemd-machine-id-setup --root="{chrootDirectory}"

systemd-nspawn --boot --capability=all --machine={machineName} --directory="{chrootDirectory}" &
CONTAINER_PID=$!

sleep 20

until machinectl list | grep -q {machineName}; do
    sleep 1
done

machinectl shell root@{machineName} {chrootCommand[0]}
sleep 2
machinectl terminate {machineName}
sleep 2
wait $CONTAINER_PID""", checkValid)

        if fix_systemd_container_host_files_copy:
            for localpath in fix_systemd_container_host_files_copy_list:
                old_path = pathConcat(chrootDirectory, localpath + "_")
                new_path = pathConcat(chrootDirectory, localpath)
                buildLog(f"fix_systemd_container_host_files_copy (end): {old_path} > {new_path}")
                deleteAny(new_path)
                copyItemFiles(old_path, new_path)
                deleteAny(old_path)

        time.sleep(60)
    else:
        if not item.get("disable_shitfix_armel_armhf_build", False):
            # кастыль для сборки на armel и armhf
            # когда пофиксят баг с qemu-arm-static (32 бита) СУКАААААА
            # обьяснения от deepseek, не ручаюсь за правильность. решается кастылями
            # без этой фигни не собирается initramfs для armhf и armel
            """
            Upstream-баг в glibc: #23960 в баг-трекере Sourceware. Опубликован в 2018 году и до сих пор не исправлен
            Баг в Debian для dracut-install: #1079443
            . Опубликован в августе 2024 года. Именно в нем подробно описывается проблема для armhf/armel.
            """
            symlink_creation_path = "/usr/lib/arm-linux-gnu"
            symlink_abs_path = pathConcat(chrootDirectory, symlink_creation_path)
            if not os.path.lexists(symlink_abs_path) and (__main__.architecture == "armhf" or __main__.architecture == "armel"):
                buildExecute(["chroot", chrootDirectory, "ln", "-s", "/usr/lib/arm-linux-gnueabi" + ("hf" if __main__.architecture == "armhf" else ""), symlink_creation_path], checkValid)

        buildExecute(["chroot", chrootDirectory] + chrootCommand, checkValid)

    if qemuCopied:
        deleteAny(qemuStaticPath)

        if dirCreatedForQemu_usr:
            deleteAny(usr_dir)

        if dirCreatedForQemu_usr_bin:
            deleteAny(usr_bin_dir)

    for bindPath in bindList:
        buildRawExecute(f"umount -R \"{pathConcat(chrootDirectory, bindPath)}\"", False)

    buildRawExecute(f"umount -R {chrootDirectory}", False)

    for makedDirectoryBindPath in makedDirectories:
        buildRawExecute(f"rm -rf \"{makedDirectoryBindPath}\"")

    if manualValidation:
        checkObjPath = pathConcat(chrootDirectory, ".chrootend")
        if os.path.exists(checkObjPath):
            deleteAny(checkObjPath)
        else:
            return False

    return True

def rawUpdateInitramfs(path, kernel_version, item=None):
    kernel_version_path = os.path.join(path, ".kernel_version")
    with open(kernel_version_path, "w") as f:
        f.write(kernel_version)
    
    rawCrossChroot(path, ["update-initramfs", "-c", "-k", kernel_version], False, False, item)

    os.remove(kernel_version_path)

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
    rawUpdateInitramfs(itemPath, getKernelVersion(item, itemPath), item)

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

    rawUpdateInitramfs(tempRootfs, kernel_version, item)

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
            copyItemFiles(initramfsPath, exportInitramfsPath, DEFAULT_RIGHTS_0755, True, True)
            break

def cloneBuildItem(fromItem, newItem):
    newItemPath = getItemFolder(newItem)
    oldItemPath = findItem(fromItem)
    copyItemFiles(oldItemPath, newItemPath)
    return newItemPath

def smartChroot(item):
    itemPath = cloneBuildItem(item["source"], item)
    
    for scriptItem in item["scripts"]:
        if isinstance(scriptItem, str):
            scriptPath = scriptItem
            use_systemd_container = item.get("use_systemd_container", False)
            manual_validation = item.get("manual_validation", False)
        else:
            scriptPath = scriptItem[0]
            use_systemd_container = scriptItem[1]
            manual_validation = scriptItem[2]

        chroot_script_path = pathConcat(itemPath, ".syslbuild-smart-chroot.sh")
        copyItemFiles(findItem(scriptPath), chroot_script_path, DEFAULT_RIGHTS_0755)
        if rawCrossChroot(itemPath, ["/.syslbuild-smart-chroot.sh"], use_systemd_container, manual_validation, item):
            buildExecute("reset")
        else:
            buildLog(f"ERROR: with \"manual_validation\" enabled, the chroot script \"{scriptPath}\" did not create a file or directory on the path \"/.chrootend\"")
            sys.exit(1)

        os.remove(chroot_script_path)

def singleboardBuild(item):
    singleboardType = item["singleboardType"]
    builditemName = item["name"]

    # "uboot-16" is legacy
    if singleboardType == "uboot-offset" or singleboardType == "uboot-16":
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
                ["/dtbs/overlay"]
            ],

            "items": [
                [item["bootloader"], bootloaderFileName, [0, 0, "0644"]],
                [item["kernel"], kernelFileName, [0, 0, "0644"]]
            ]
        }
        
        if initramfsFileName is not None:
            buildDirectoryBuilditem["items"].append([item["initramfs"], initramfsFileName, [0, 0, "0644"]])

        if "uboot_script" in item:
            uboot_script = findItem(item["uboot_script"])
            if Path(uboot_script).suffix.lower() == ".scr":
                buildDirectoryBuilditem["items"].append(["&" + uboot_script, "/boot.scr"])
            else:
                boot_script_compilled = getTempPath("boot.scr")
                buildExecute(["mkimage", "-C", "none", "-A", "arm", "-T", "script", "-d", uboot_script, boot_script_compilled])
                buildDirectoryBuilditem["items"].append(["&" + boot_script_compilled, "/boot.scr"])
        
        if "boot_part_items" in item:
            for addItem in item["boot_part_items"]:
                buildDirectoryBuilditem["items"].append(addItem)

        if "dtbList" in item:
            for dtb in item["dtbList"]:
                buildDirectoryBuilditem["items"].append([dtb, pathConcat("/dtbs", os.path.basename(dtb)), [0, 0, "0644"]])

        if "dtboList" in item:
            for dtb in item["dtboList"]:
                buildDirectoryBuilditem["items"].append([dtb, pathConcat("/dtbs/overlay", os.path.basename(dtb)), [0, 0, "0644"]])

        if "trigger_boot_flag" in item:
            buildDirectoryBuilditem["directories"].append([item["trigger_boot_flag"], [0, 0, "0000"]])

        buildDirectory(buildDirectoryBuilditem)

        # boot config
        bootDirectory = findItem(bootdirName)
        extlinuxPath = pathConcat(bootDirectory, item.get("extlinux_path", "extlinux/extlinux.conf"))
        
        with open(extlinuxPath, "w") as f:
            f.write("LABEL linux\n")
            f.write(f"KERNEL /{kernelFileName}\n")
            if "bootloaderDtb" in item:
                f.write(f"FDT /dtbs/{item['bootloaderDtb']}\n")
            
            kernel_args = item.get("kernel_args", "")
            
            if item.get("kernel_rootfs_auto", False):
                if "rootfs" in item:
                    kernel_rootfs_auto = item["kernel_rootfs_auto"]
                    if kernel_rootfs_auto == "manual":
                        kernel_args = f"root=/dev/mmcblk0p2 " + kernel_args
                    else:
                        kernel_args = f"root=/dev/mmcblk0p2 {kernel_rootfs_auto} " + kernel_args
            
            if item.get("kernel_args_auto", False):
                if "initramfs" in item:
                    kernel_args = f"initrd=/{initramfsFileName} " + kernel_args
            
            f.write(f"APPEND {kernel_args}\n")

            if "dtboList_active" in item:
                active_overlays = []
                for active_overlay in item["dtboList_active"]:
                    active_overlays.append(f"/dtbs/overlay/{active_overlay}")

                if len(active_overlays) > 0:
                    f.write(f"FDTOVERLAYS {' '.join(active_overlays)}\n")

        # boot partition
        buildFilesystem({
            "name": bootfsName,
            "export": False,

            "source": bootdirName,

            "fs_type": "fat32",
            "size": item.get("boot_partition_size", "(auto * 1.2) + (100 * 1024 * 1024)"),
            "minsize": item.get("boot_partition_minsize", "64MB"),
            "label": item.get("boot_partition_name", "BOOT")
        })

        # bootable image
        bootloader_offset = item.get("bootloader_offset", 16)
        buildFullDiskImageBuilditem = {
            "name": builditemName,
            "export": readBool(item, "export"),

            "size": "auto + (16 * 1024 * 1024)",

            "partitionsStartSector": bootloader_offset * 512,
            "partitionTable": "dos",
            "partitions": [
                [bootfsName, "linux"]
            ],

            "bootloader": {
                "type": "binary",
                "binaries": [
                    {
                        "file": item["bootloader"],
                        "sector": bootloader_offset
                    }
                ]
            }
        }
        
        if "prepandPartitions" in item:
            buildFullDiskImageBuilditem["partitions"] += item["prepandPartitions"]
        
        if "rootfs" in item:
            buildFullDiskImageBuilditem["partitions"].append([item["rootfs"], "linux"])

        if "appendPartitions" in item:
            buildFullDiskImageBuilditem["partitions"] += item["appendPartitions"]
        
        buildFullDiskImage(buildFullDiskImageBuilditem)

"""
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
"""

def gitcloneBuild(item):
    url = item["git_url"]
    output_folder = getItemFolder(item)
    
    # Инициализируем пустой репозиторий
    buildExecute(["git", "init"], True, None, output_folder)
    buildExecute(["git", "remote", "add", "origin", url], True, None, output_folder)
    
    # Определяем что фетчить
    if "git_checkout" in item:
        commit_or_branch = item["git_checkout"]
        # Получаем только один коммит с родителем
        buildExecute(["git", "fetch", "--depth=1", "origin", commit_or_branch], True, None, output_folder)
        buildExecute(["git", "checkout", "FETCH_HEAD"], True, None, output_folder)
    elif "git_branch" in item:
        branch = item["git_branch"]
        # shallow fetch ветки
        buildExecute(["git", "fetch", "--depth=1", "origin", branch], True, None, output_folder)
        buildExecute(["git", "checkout", branch], True, None, output_folder)
    else:
        # Если не указано ни commit, ни branch, просто fetch master/main
        buildExecute(["git", "fetch", "--depth=1", "origin", "HEAD"], True, None, output_folder)
        buildExecute(["git", "checkout", "FETCH_HEAD"], True, None, output_folder)

def executeCommands(item):
    commands = item.get("commands", [])
    if "working_dir" in item:
        doCommands(item["working_dir"], commands)
    elif "source" in item:
        doCommands(cloneBuildItem(item["source"], item), commands)
    else:
        doCommands(".", commands)

def unpackArchive(item):
    buildExecute(["7z", "x", findItem(item["archive"]), f"-o{getItemFolder(item)}"])

def unpackTarGz(item):
    cmd = ["tar", "-xzf", findItem(item["archive"]), "-C", getItemFolder(item)]
    strip_components = item.get("strip_components", 0)
    if strip_components > 0:
        cmd.append(f"--strip-components={strip_components}")
    buildExecute(cmd)

def unpackTarAuto(item):
    cmd = ["tar", "-xaf", findItem(item["archive"]), "-C", getItemFolder(item)]
    strip_components = item.get("strip_components", 0)
    if strip_components > 0:
        cmd.append(f"--strip-components={strip_components}")
    buildExecute(cmd)

def deleteAllNones(tbl):
    for key, value in list(tbl.items()):
        if value is None:
            del tbl[key]

def buildConfigureMake(item):
    path = findItem(item["source"])
    output = getItemFolder(item)
    build_temp = getTempFolder("build-configure-make")

    host_architecture = get_host_arch()

    gcc_native = gccNames[host_architecture]
    gcc_cross = gccNames[__main__.architecture]

    if item.get("disable_cross_compile", False):
        gcc_cross = gcc_native
    
    sysroot_gcc_direct = item.get("sysroot_gcc_direct", False)
    sysroot_gcc_direct_cmd = item.get("sysroot_gcc_direct_cmd", False)
    sysroot_gcc_disable_default = item.get("sysroot_gcc_disable_default", False)
    sysroot_gcc_env = item.get("sysroot_gcc_env", False)

    env = {}
    env["CROSS_COMPILE"] = gcc_cross + "-"
    env["CC"] = gcc_cross + "-gcc"
    env["CXX"] = gcc_cross + "-g++"
    env["LD"] = gcc_cross + "-ld"
    env["AR"] = gcc_cross + "-ar"
    env["RANLIB"] = gcc_cross + "-ranlib"
    env["STRIP"] = gcc_cross + "-strip"

    env["CFLAGS"] = " ".join(item.get("CFLAGS", []))
    env["LDFLAGS"] = " ".join(item.get("LDFLAGS", []))
    env["CXXFLAGS"] = " ".join(item.get("CXXFLAGS", []))
    env["CPPFLAGS"] = " ".join(item.get("CPPFLAGS", []))
    env["LIBS"] = " ".join(item.get("LIBS", []))

    default_flags = ""

    if not item.get("disable_cross_compile", False):
        default_flags += f"--build={gcc_native} --host={gcc_cross}"

    if "sysroot" in item:
        sysroot_path = os.path.abspath(findItem(item["sysroot"]))
        buildLog(f"sysroot_path: {sysroot_path}")

        if item.get("sysroot_set_env_PKG_CONFIG_SYSROOT_DIR", False):
            env["PKG_CONFIG_SYSROOT_DIR"] = sysroot_path

        if item.get("sysroot_set_env_PKG_CONFIG_LIBDIR", False):
            env["PKG_CONFIG_LIBDIR"] = f"{sysroot_path}/usr/lib/pkgconfig:{sysroot_path}/usr/share/pkgconfig:{sysroot_path}/lib/pkgconfig"

        if sysroot_gcc_direct:
            sysroot = f" --sysroot=\"{sysroot_path}\""
            env["CFLAGS"] += sysroot
            env["LDFLAGS"] += sysroot
            env["CXXFLAGS"] += sysroot
            env["CPPFLAGS"] += sysroot

        if sysroot_gcc_direct_cmd:
            additional_args = f" --sysroot=\"{sysroot_path}\""
            env["CC"] += additional_args
            env["CXX"] += additional_args
            env["LD"] += additional_args
        
        if not sysroot_gcc_disable_default:
            default_flags += f" --{item.get('sysroot_field_name', 'sysroot')}=\"{sysroot_path}\""

        if sysroot_gcc_env:
            env["SYSROOT"] = sysroot_path

        if item.get("sysroot_auto_libs", False):
            include_arg = f" -I{sysroot_path}/usr/include -I{sysroot_path}/include"

            env["CFLAGS"] += include_arg
            env["CPPFLAGS"] += include_arg
            env["LDFLAGS"] += f" -L{sysroot_path}/usr/lib -L{sysroot_path}/lib"

    env.update(item.get("env_change", []))
    deleteAllNones(env)

    if "prefix" in item:
        default_flags += " --prefix=\"" + item["prefix"] + "\""

    cmd = f"{os.path.abspath(os.path.join(path, 'configure'))} {default_flags} {' '.join(item.get('FLAGS', []))}"
    buildRawExecute(cmd, True, build_temp, env)

    cmd = f"make -j$(nproc)"
    buildRawExecute(cmd, True, build_temp, env)

    cmd = f"make install DESTDIR=\"{os.path.abspath(output)}\""
    buildRawExecute(cmd, True, build_temp, env)

def buildMake(item):
    path = findItem(item["source"])
    output = getItemFolder(item)
    build_temp = getTempFolder("build-make")
    copyItemFiles(path, build_temp)

    host_architecture = get_host_arch()
    gcc_native = gccNames[host_architecture]
    gcc_cross = gccNames[__main__.architecture]
    if item.get("disable_cross_compile", False):
        gcc_cross = gcc_native

    args = []
    args.append("CC=\"" + gcc_cross + "-gcc\"")
    args.append("CXX=\"" + gcc_cross + "-g++\"")
    args.append("LD\"=" + gcc_cross + "-ld\"")
    args.append("AR=\"" + gcc_cross + "-ar\"")
    args.append("RANLIB=\"" + gcc_cross + "-ranlib\"")
    args.append("STRIP=\"" + gcc_cross + "-strip\"")

    install_args = []

    if "prefix" in item:
        install_args.append("PREFIX=\"" + item["prefix"] + "\"")

    install_args.append("DESTDIR=\"" + os.path.abspath(output) + "\"")

    args_str = " ".join(args)
    install_args_str = " ".join(install_args)

    env = {}
    env.update(item.get("env_change", []))
    deleteAllNones(env)

    cmd = f"make -j$(nproc) {install_args_str} {args_str} {' '.join(item.get('make_args', []))}"
    buildRawExecute(cmd, True, path, env)

    cmd = f"make install {install_args_str} {' '.join(item.get('make_install_args', []))}"
    buildRawExecute(cmd, True, path, env)

# --------------------------------------------------------------------- get dependencies

def getDependenciesDebian(item):
    return rawGetDependencies(item, [], ["hook-directory"])

def getDependenciesDirectory(item):
    return rawGetDependencies(item, ["items"], [], "directory")

def getDependenciesFullDiskImage(item):
    dependencies = rawGetDependencies(item, ["partitions"], [])
    if item.get("bootloader", {}).get("config", None):
        dependencies.append(getDependenciesFieldChecksum(item["bootloader"]["config"], False))
    return dependencies

def getDependenciesGccBuild(item):
    return rawGetDependencies(item, ["sources-dirs"], [])

def getDependenciesGrubIsoImage(item):
    return rawGetDependencies(item, ["kernel", "initramfs", "config"], [])

def getDependenciesUnpackInitramfs(item):
    return rawGetDependencies(item, ["initramfs"], [])

def getDependenciesKernel(item):
    return rawGetDependencies(item, ["patches", "kernel_config", "kernel_config_changes_files", "items", "items_once_before_patches", "items_once_after_patches"], [])

def getDependenciesPatches(item):
    return rawGetDependencies(item, ["source", "patches"], [])

def getDependenciesDebianExportInitramfs(item):
    return rawGetDependencies(item, ["kernel_config", "source"], [])

def getDependenciesSmartChroot(item):
    return rawGetDependencies(item, ["scripts", "source"], [])

def getDependenciesSingleboard(item):
    return rawGetDependencies(item, ["bootloader", "initramfs", "kernel", "rootfs", "dtbList", "dtboList", "bootloaderDtb", "boot_part_items", "prepandPartitions", "appendPartitions", "uboot_script"], [])

def getDependencies_source_item(item):
    return rawGetDependencies(item, ["source"], [])

def getDependencies_archive_item(item):
    return rawGetDependencies(item, ["archive"], [])

# ---------------------------------------------------------------------

syslbuild_push_getDependencies({
    "debian": getDependenciesDebian,
    "directory": getDependenciesDirectory,
    "tar": getDependencies_source_item,
    "filesystem": getDependencies_source_item,
    "full-disk-image": getDependenciesFullDiskImage,
    "from-directory": getDependencies_source_item,
    "gcc-build": getDependenciesGccBuild,
    "initramfs": getDependencies_source_item,
    "grub-iso-image": getDependenciesGrubIsoImage,
    "unpack-initramfs": getDependenciesUnpackInitramfs,
    "kernel": getDependenciesKernel,
    "patches": getDependenciesPatches,
    "debian-update-initramfs": getDependencies_source_item,
    "debian-export-initramfs": getDependenciesDebianExportInitramfs,
    "smart-chroot": getDependenciesSmartChroot,
    "singleboard": getDependenciesSingleboard,
    "execute-commands": getDependencies_source_item,
    "unpack-archive": getDependencies_archive_item,
    "unpack-tar-gz": getDependencies_archive_item,
    "unpack-tar-auto": getDependencies_archive_item,
    "build-configure-make": getDependencies_source_item,
    "build-make": getDependencies_source_item
})

syslbuild_push_buildItems({
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
    "patches": buildPatches,
    "debian-update-initramfs": debianUpdateInitramfs,
    "debian-export-initramfs": debianExportInitramfs,
    "smart-chroot": smartChroot,
    "singleboard": singleboardBuild,
    "gitclone": gitcloneBuild,
    "execute-commands": executeCommands,
    "unpack-archive": unpackArchive,
    "unpack-tar-gz": unpackTarGz,
    "unpack-tar-auto": unpackTarAuto,
    "build-configure-make": buildConfigureMake,
    "build-make": buildMake
})
