import pathlib

def get_name_without_all_extensions(filepath):
    p = pathlib.Path(filepath)
    while p.suffix:
        p = p.with_suffix('')
    return p.name
