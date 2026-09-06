VERSION = [1, 10, 2]

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
