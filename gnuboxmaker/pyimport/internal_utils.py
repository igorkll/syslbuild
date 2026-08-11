from __main__ import *
import __main__

def get_name_without_all_extensions(filepath):
    p = Path(filepath)
    while p.suffix:
        p = p.with_suffix('')
    return p.name

def raw_load_project(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json5.load(f)
        return Project(**data)

def raw_save_project(path, proj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(proj), f, indent=2, ensure_ascii=False)

# -1 - версия проекта ниже версии тула
# 0 - версии совпадают
# 1 - версия проекта выше чем версия тула (не катит)
def checkVersion(project):
    minVersion = syslbuild.VERSION

    for index, vernum in enumerate(project.gnubox_version):
        if vernum > minVersion[index]:
            return 1
        elif vernum < minVersion[index]:
            return -1
    
    return 0

def exclude_string(lstr, exclude_list):
    parts = lstr.split()
    filtered = [p for p in parts if p not in exclude_list]
    return ' '.join(filtered)

def exclude_array(arr, exclude_list):
    return [item for item in arr if item not in exclude_list]

def deleteAny(path):
    if os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

def writeText(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)

def copyFile(path, fromPath):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.copy(fromPath, path)

def copy_files(from_path, to_path):
    buildExecute(["cp", "-a", from_path + "/.", to_path])

def buildLog(logstr, quiet=False):
    if not quiet:
        logstr = f"---------------- GNUBOX MAKER: {logstr}"
    
    print(logstr)

def read_gnubox_file(name):
    path = os.path.join("gnuboxmaker", name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
    
    return []

def read_project_file(name):
    path = os.path.join(__main__.current_project_directory, name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
    
    return []
