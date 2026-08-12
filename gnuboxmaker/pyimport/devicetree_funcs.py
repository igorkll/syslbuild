from __main__ import *
import __main__

def compile_dts(source_path, output_path):
    """Компилирует .dts/.dtso файл в .dtb/.dtbo с символами (-@)."""
    cmd = ['dtc', '-@', '-I', 'dts', '-O', 'dtb', '-o', output_path, source_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        if os.path.isfile(output_path):
            buildLog(f"[OK] {source_path} -> {output_path}")
        else:
            stop_error(f"[FAIL] {source_path}")
    except subprocess.CalledProcessError as e:
        stop_error(f"[FAIL] {source_path}:\n  {e.stderr}", file=sys.stderr)

def prepair_devicetree(devicetree):
    for plat_name in os.listdir(devicetree):
        plat_path = os.path.join(devicetree, plat_name)
        if not os.path.isdir(plat_path):
            continue

        for file in os.listdir(plat_path):
            full_path = os.path.join(plat_path, file)
            if not os.path.isfile(full_path):
                continue

            if file.endswith('.dts'):
                out_ext = '.dtb'
            elif file.endswith('.dtso'):
                out_ext = '.dtbo'
            else:
                continue

            base_name = os.path.splitext(file)[0]
            out_file = base_name + out_ext
            out_full = os.path.join(plat_path, out_file)
            compile_dts(full_path, out_full)

def get_devicetree_override(platform):
    dt_dir = os.path.join(__main__.path_temp_syslbuild, "files", "devicetree", platform)
    if os.path.isdir(dt_dir):
        override_path = os.path.join(dt_dir, 'override.txt')
        if os.path.isfile(override_path):
            with open(override_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if len(content) > 0:
                    return content
    
    return None

def get_devicetree_overlays(platform):
    dt_dir = os.path.join(__main__.path_temp_syslbuild, "files", "devicetree", platform)
    if os.path.isdir(dt_dir):
        overlays_path = os.path.join(dt_dir, 'overlays.txt')
        if os.path.isfile(overlays_path):
            with open(overlays_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if len(content) > 0:
                    return content.splitlines()
    
    return []

def devicetree_get_files(platform, extension):
    files = []

    dt_dir = os.path.join(__main__.path_temp_syslbuild, "files", "devicetree", platform)
    if os.path.isdir(dt_dir):
        for file in sorted(os.listdir(dt_dir)):
            full_path = os.path.join(dt_dir, file)
            if not os.path.isfile(full_path):
                continue
            
            if full_path.endswith('.' + extension):
                files.append(os.path.join("files", "devicetree", platform, file))
    
    return files

def init_devicetree(name):
    devicetree = os.path.join(__main__.path_resources, "devicetree", name)

    os.makedirs(devicetree, exist_ok=True)

    devicetree_override = os.path.join(devicetree, "override.txt")
    if not os.path.isfile(devicetree_override):
        with open(devicetree_override, "w", encoding="utf-8") as f:
            pass

    devicetree_overlays = os.path.join(devicetree, "overlays.txt")
    if not os.path.isfile(devicetree_overlays):
        with open(devicetree_overlays, "w", encoding="utf-8") as f:
            pass
