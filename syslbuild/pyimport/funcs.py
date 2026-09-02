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
    if changeRights is None:
        changeRights = DEFAULT_RIGHTS_0700

    defaultChainRights = False
    if chainDirsRights is None:
        defaultChainRights = True
        chainDirsRights = DEFAULT_RIGHTS_0700
    
    if not os.path.lexists(path):
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
    """
    Копирует владельца, группу и права доступа с src на dst.
    Игнорирует ошибки (PermissionError, OSError).
    """
    try:
        st = os.stat(src)
        os.chown(dst, st.st_uid, st.st_gid)
        os.chmod(dst, st.st_mode)
    except (PermissionError, OSError):
        pass

def moveAccessRulesRecursion(fromPath, toPath, dontProcessTargetPathRoot=False, # ТУТ ЕБАНЫЙ ПИЗДЕЦ ИИШНЫЙ. ЭТО ПОЛНЕЙШИЙ НЕЛИКВИД СДЕЛАНЫЙ ДЛЯ ТЕСТА. Я ПЕРЕДЕЛАЮ ЭТО ЗАВТРА
                             overrideRightsForExistingDirectories=False,
                             existing_dirs_set=None):
    """
    Рекурсивно применяет права доступа от объектов внутри fromPath
    к соответствующим объектам внутри toPath.

    Параметры:
        fromPath: исходный каталог
        toPath: целевой каталог
        dontProcessTargetPathRoot: если True, не применять права к корню toPath
        overrideRightsForExistingDirectories: если True, применять права ко всем каталогам,
                                               если False – не трогать существовавшие каталоги
        existing_dirs_set: множество абсолютных путей каталогов,
                           которые существовали в toPath ДО копирования
    """
    if existing_dirs_set is None:
        existing_dirs_set = set()

    # --- Обработка корневого каталога ---
    if not dontProcessTargetPathRoot:
        # Если корень toPath существовал ранее, то применяем права только
        # если overrideRightsForExistingDirectories == True
        if toPath in existing_dirs_set:
            if overrideRightsForExistingDirectories:
                moveAccessRules(fromPath, toPath)
        else:
            # Новый каталог — применяем права всегда
            moveAccessRules(fromPath, toPath)

    # --- Обход всех подкаталогов и файлов ---
    for root, dirs, files in os.walk(fromPath):
        relpath = os.path.relpath(root, fromPath)
        if relpath == '.':
            # Корень уже обработан (или пропущен), но продолжаем обход вложенных объектов
            continue

        # Целевой каталог для текущего root
        dst_root = os.path.join(toPath, relpath)

        # Обработка вложенных каталогов
        for d in dirs:
            src_dir = os.path.join(root, d)
            dst_dir = os.path.join(dst_root, d)

            # Если каталог существовал до копирования
            if dst_dir in existing_dirs_set:
                if overrideRightsForExistingDirectories:
                    moveAccessRules(src_dir, dst_dir)
                # иначе пропускаем (не меняем права)
            else:
                # Новый каталог — применяем права всегда
                moveAccessRules(src_dir, dst_dir)

        # Обработка файлов (права обновляются всегда)
        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(dst_root, f)
            moveAccessRules(src_file, dst_file)
"""
if changeRights:
    tempFolder = getTempFolder("changeRights")
    buildExecute(["cp", "-a", fromPath + "/.", tempFolder])
    changeAccessRights(tempFolder, changeRights) # рекурсивно устанавливаем права доступа для всего внутри каталога
    buildExecute(["chmod", "--reference=" + toPath, tempFolder]) # не меняем права доступа на сам каталог, для этого переносим оригинальные на него
    buildExecute(["chown", "--reference=" + toPath, tempFolder])
    copypath = tempFolder
else:
    copypath = fromPath
"""

def copyItemFiles(fromPath, toPath, changeRights=None, allowSymlinks=True, copySymlinksAsFiles=False, overrideRightsForExistingDirectories=False, moveRightsToTargetDir=False):
    rsync_arg = "-a"
    if copySymlinksAsFiles:
        rsync_arg += "L"

    if os.path.isdir(fromPath):
        makedirsChangeRights(toPath)

        if allowSymlinks:
            # проходит по симлинкам в целевом каталоге копируя в целевой каталог на который указывает симлинк
            # то скопирует ли он симлинки или целевой обьект симлинка зависит от переменной copySymlinksAsFiles
            buildExecute(["rsync", rsync_arg, "--no-perms", "--no-owner", "--no-group", "--keep-dirlinks", fromPath + "/.", toPath])
        else:
            # всегда копирует симлинки как симлинки
            buildExecute(["cp", "-a", "--no-preserve=mode,ownership", fromPath + "/.", toPath])

        moveAccessRulesRecursion(fromPath, toPath, not moveRightsToTargetDir, overrideRightsForExistingDirectories)
    else:
        # this is necessary to correctly overwrite the symlink that links to a working file in the host system.
        deleteAny(toPath)

        file_dir = os.path.dirname(toPath)
        if not os.path.isdir(file_dir):
            makedirsChangeRights(file_dir)

        if allowSymlinks:
            buildExecute(["rsync", rsync_arg, "--keep-dirlinks", fromPath, toPath])
        else:
            # всегда копирует симлинки как файлы
            # shutil.copy2(fromPath, toPath)
            buildExecute(["cp", "-Lp", fromPath, toPath])

        if changeRights:
            changeAccessRights(toPath, changeRights)
