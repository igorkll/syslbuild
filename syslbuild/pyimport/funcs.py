from __main__ import *
import __main__

def changeAccessRights(path, changeRights):
    """
    Устанавливает права и владельца на путь path.
    
    Старый формат changeRights:
        [owner, group, perms]  или [owner, group] — perms применяется рекурсивно через chmod -R.
    
    Новый формат changeRights:
        [[owner, group, perms_files], [owner, group, perms_dirs]]
        — perms_files применяется только к файлам (find -type f)
        — perms_dirs применяется только к каталогам (find -type d)
        — владельцы применяются отдельно для файлов и каталогов (по соответствующим подспискам)
    """

    if (isinstance(changeRights, list) and len(changeRights) == 2 and
        isinstance(changeRights[0], list) and len(changeRights[0]) >= 3 and
        isinstance(changeRights[1], list) and len(changeRights[1]) >= 3):
        
        file_owner, file_group, file_perms = changeRights[0][0], changeRights[0][1], changeRights[0][2]
        dir_owner,  dir_group,  dir_perms  = changeRights[1][0], changeRights[1][1], changeRights[1][2]
        
        if file_perms is not None:
            buildExecute(["find", path, "-type", "f", "-exec", "chmod", file_perms, "{}", "+"])
        
        if dir_perms is not None:
            buildExecute(["find", path, "-type", "d", "-exec", "chmod", dir_perms, "{}", "+"])
    
        if file_owner is not None or file_group is not None:
            chown_files = chownStr(file_owner, file_group)
            if chown_files:
                buildExecute(["find", path, "-type", "f", "-exec", "chown", chown_files, "{}", "+"])
        
        if dir_owner is not None or dir_group is not None:
            chown_dirs = chownStr(dir_owner, dir_group)
            if chown_dirs:
                buildExecute(["find", path, "-type", "d", "-exec", "chown", chown_dirs, "{}", "+"])
    else:
        if len(changeRights) >= 3 and changeRights[2]:
            buildExecute(["chmod", "-R", changeRights[2], path])
        
        chown_str = chownStr(changeRights[0], changeRights[1])
        if chown_str:
            buildExecute(["chown", "-R", chown_str, path])

def makedirsChangeRights(path, changeRights=None):
    if not os.path.exists(path):
        os.makedirs(path)
        changeAccessRights(path, changeRights or DEFAULT_RIGHTS_0700)

def isUserItem(itemName):
    itemName = resolveItemName(itemName)
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
