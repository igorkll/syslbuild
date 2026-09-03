from __main__ import *
import __main__

import os

def changeAccessRights(path, changeRights, recursion=True):
    """
    Устанавливает права и владельца на путь path.
    
    Старый формат changeRights:
        [owner, group, perms]  или [owner, group] — perms применяется рекурсивно через chmod -R.
    
    Новый формат changeRights:
        [[owner, group, perms_files], [owner, group, perms_dirs]]
        — perms_files применяется только к файлам (find -type f)
        — perms_dirs применяется только к каталогам (find -type d)
        — владельцы применяются отдельно для файлов и каталогов (по соответствующим подспискам)
    
    Параметр recursion:
        Если False, то действия выполняются только над самим path, без рекурсивного обхода.
    """

    # --- Проверка нового формата ---
    if (isinstance(changeRights, list) and len(changeRights) == 2 and
        isinstance(changeRights[0], list) and len(changeRights[0]) >= 3 and
        isinstance(changeRights[1], list) and len(changeRights[1]) >= 3):
        
        file_owner, file_group, file_perms = changeRights[0][0], changeRights[0][1], changeRights[0][2]
        dir_owner,  dir_group,  dir_perms  = changeRights[1][0], changeRights[1][1], changeRights[1][2]
        
        if recursion:
            # Рекурсивный режим: применяем права отдельно к файлам и каталогам

            # ------------ права доступа
            
            # файлы
            if file_perms is not None:
                buildExecute(["find", path, "-type", "f", "-exec", "chmod", file_perms, "{}", "+"])
        
            # каталоги
            if dir_perms is not None:
                buildExecute(["find", path, "-type", "d", "-exec", "chmod", dir_perms, "{}", "+"])

            # ------------ владельцы/группы

            # файлы
            if file_owner is not None or file_group is not None:
                chown_files = chownStr(file_owner, file_group)
                if chown_files:
                    buildExecute(["find", path, "-type", "f", "-exec", "chown", chown_files, "{}", "+"])
            
            # каталоги
            if dir_owner is not None or dir_group is not None:
                chown_dirs = chownStr(dir_owner, dir_group)
                if chown_dirs:
                    buildExecute(["find", path, "-type", "d", "-exec", "chown", chown_dirs, "{}", "+"])
        else:
            # Нерекурсивный режим: применяем права только к самому path
            # Определяем тип объекта
            if os.path.isdir(path):
                # Это каталог – применяем dir-права

                if dir_perms is not None:
                    buildExecute(["chmod", dir_perms, path])
                
                if dir_owner is not None or dir_group is not None:
                    chown_str = chownStr(dir_owner, dir_group)
                    if chown_str:
                        buildExecute(["chown", chown_str, path])
            else:
                # Это файл (или симлинк) – применяем file-права

                if file_perms is not None:
                    buildExecute(["chmod", file_perms, path])
                
                if file_owner is not None or file_group is not None:
                    chown_str = chownStr(file_owner, file_group)
                    if chown_str:
                        buildExecute(["chown", chown_str, path])

    else:
        if len(changeRights) >= 3 and changeRights[2]:
            arr = ["chmod", changeRights[2], path]
            if recursion:
                arr.insert(1, "-R")
            buildExecute(arr)
        
        chown_str = chownStr(changeRights[0], changeRights[1])
        if chown_str:
            arr = ["chown", chown_str, path]
            if recursion:
                arr.insert(1, "-R")
            buildExecute(arr)

def makedirsChangeRights(path, changeRights=None, chainDirsRights=None):
    if not os.path.lexists(path):
        if changeRights is None:
            changeRights = DEFAULT_RIGHTS_0700

        defaultChainRights = False
        if chainDirsRights is None:
            defaultChainRights = True
            chainDirsRights = DEFAULT_RIGHTS_0700
            
        chainParts = Path(path).parts
        chainPartsCount = len(chainParts)

        currentPath = ""
        currentIndex = 0
        for pathPart in chainParts:
            currentIndex += 1
            
            if currentIndex == 1:
                currentPath = pathPart
            else:
                currentPath = os.path.join(currentPath, pathPart)

            if currentIndex == chainPartsCount:
                localRights = changeRights
                currentChain = False
            else:
                localRights = chainDirsRights
                currentChain = True

            if not os.path.lexists(currentPath):
                if currentChain and defaultChainRights:
                    buildWarning(f"chain directory creating with default rights: {currentPath}")
                os.makedirs(currentPath)
                changeAccessRights(currentPath, localRights, False)

def isUserItem(itemName):
    itemName = resolveItemName(itemName)
    path = pathConcat(__main__.path_build, itemName)
    if os.path.exists(path):
        return False
    else:
        path = pathConcat(__main__.path_output_target, itemName)
        if os.path.exists(path):
            return False
        else:
            path = pathConcat(".", itemName)
            if os.path.exists(path):
                return True

    return False

def makeAllFilesExecutable(path):
    for entry in os.scandir(path):
        if entry.is_file():
            st = os.stat(entry.path)
            os.chmod(entry.path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def recursionDeleleSymlinks(directoryPath):
    buildRawExecute("find . -type l -exec rm -f {} +", True, directoryPath)

def moveAccessRules(src, dst):
    st = os.stat(src)
    os.chown(dst, st.st_uid, st.st_gid)
    os.chmod(dst, st.st_mode)
    os.utime(dst, (st.st_atime, st.st_mtime))

def copyItemFiles(fromPath, toPath, changeRights=None, copySymlinksAsFiles=False, changeRightsOnTargetRoot=False):
    # проходит по симлинкам в целевом каталоге копируя в целевой каталог на который указывает симлинк
    # то скопирует ли он симлинки или целевой обьект симлинка зависит от переменной copySymlinksAsFiles

    rsync_arg = "-aUN"
    if copySymlinksAsFiles:
        rsync_arg += "L"

    if os.path.isdir(fromPath):
        makedirsChangeRights(toPath)

        tempFolder = getTempFolder("changeRights")
        buildExecute(["rsync", rsync_arg, "--keep-dirlinks", fromPath + "/.", tempFolder])
        if changeRights:
            changeAccessRights(tempFolder, changeRights) # рекурсивно устанавливаем права доступа для всего внутри каталога

        # тут выбирается будут ли перенесены права с корня fromPath на toPath
        targetRulesRightsReference = toPath
        if changeRightsOnTargetRoot:
            targetRulesRightsReference = fromPath
        buildExecute(["chmod", "--reference=" + targetRulesRightsReference, tempFolder])
        buildExecute(["chown", "--reference=" + targetRulesRightsReference, tempFolder])

        # копирую временый каталог в целевой
        buildExecute(["rsync", rsync_arg, "--keep-dirlinks", tempFolder + "/.", toPath])
    else:
        # this is necessary to correctly overwrite the symlink that links to a working file in the host system.
        deleteAny(toPath)

        file_dir = os.path.dirname(toPath)
        if not os.path.isdir(file_dir):
            makedirsChangeRights(file_dir)

        buildExecute(["rsync", rsync_arg, "--keep-dirlinks", fromPath, toPath])

        if changeRights:
            changeAccessRights(toPath, changeRights)
