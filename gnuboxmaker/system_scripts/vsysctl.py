#!/usr/bin/env python3
"""
vsysctl — minimal systemctl replacement for chroot environments.

Supported commands:
    enable, disable, mask, unmask, set-default

Mimics systemd's symlink semantics as closely as possible:
  * searches units in the same order as systemd
  * creates absolute symlinks in <target>.wants/ and <target>.requires/
  * processes Alias= and Also= from the [Install] section
  * disable removes .wants/.requires links and Alias= links
  * mask creates a symlink to /dev/null
  * unmask removes it (no-op if not masked)
  * set-default writes /etc/systemd/system/default.target

Compatible with Python 3.6+ (Debian 10 / 11 / 12 / sid).
Only the standard library is required.
"""

import argparse
import os
import sys
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UNIT_SEARCH_PATHS = [
    "/etc/systemd/system",
    "/run/systemd/system",
    "/usr/local/lib/systemd/system",
    "/usr/lib/systemd/system",
    "/lib/systemd/system",
]

SYSTEMD_ETC_DIR = "/etc/systemd/system"
SYSTEMD_RUN_DIR = "/run/systemd/system"
DEV_NULL = "/dev/null"

# Suffixes used for name normalization (foo -> foo.service)
KNOWN_SUFFIXES = (
    ".service", ".socket", ".target", ".mount", ".automount",
    ".swap", ".timer", ".path", ".slice", ".scope", ".device",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def debug(msg):
    # type: (str) -> None
    """Print a debug message to stderr if VSYSCTL_DEBUG is set."""
    if os.environ.get("VSYSCTL_DEBUG"):
        sys.stderr.write("[vsysctl] {}\n".format(msg))


def error(msg):
    # type: (str) -> None
    """Print an error message to stderr in systemctl-like style."""
    sys.stderr.write("Failed to {}\n".format(msg))


def find_unit(name):
    # type: (str) -> Optional[str]
    """
    Locate a unit file by name across the standard search paths.
    Returns the absolute path or None if not found.
    """
    for base in UNIT_SEARCH_PATHS:
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate):
            debug("found unit: {}".format(candidate))
            return candidate
    debug("unit not found: {}".format(name))
    return None


def normalize_unit_name(name):
    # type: (str) -> str
    """
    If 'name' has no known suffix and the exact file does not exist,
    try name + '.service'. Mirrors systemd's default suffix rule.
    """
    if find_unit(name):
        return name
    has_suffix = any(name.endswith(s) for s in KNOWN_SUFFIXES)
    if not has_suffix:
        candidate = name + ".service"
        if find_unit(candidate):
            debug("normalized unit name: {} -> {}".format(name, candidate))
            return candidate
    return name


def parse_install_section(unit_path):
    # type: (str) -> Dict[str, List[str]]
    """
    Manually parse the [Install] section of a systemd unit file.

    We do not use configparser on purpose:
      * systemd allows the same key multiple times (e.g. two WantedBy=
        lines) and concatenates the values; configparser would silently
        drop duplicates.
      * systemd does not perform %-interpolation on values, but
        configparser's BasicInterpolation raises on stray '%'.
    A tiny manual parser gives us exact systemd semantics.
    """
    install = {}  # type: Dict[str, List[str]]
    in_install = False
    try:
        with open(unit_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if line.startswith("["):
                    in_install = (line == "[Install]")
                    continue
                if not in_install:
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if not value:
                    continue
                install.setdefault(key, []).extend(value.split())
    except (IOError, OSError) as e:
        debug("failed to read {}: {}".format(unit_path, e))
        return {}

    if not install:
        debug("no [Install] section in {}".format(unit_path))
    return install


def ensure_dir(path):
    # type: (str) -> None
    """Create a directory (and its parents) if it doesn't exist."""
    if path and not os.path.isdir(path):
        os.makedirs(path)
        debug("ensured directory: {}".format(path))


def create_symlink(target, link_path):
    # type: (str, str) -> bool
    """
    Create symlink 'link_path' -> 'target'.

    Refuses to overwrite a real file or a real directory (matching
    systemd's behaviour). Replaces existing symlinks.
    """
    ensure_dir(os.path.dirname(link_path))

    if os.path.lexists(link_path):
        if os.path.isdir(link_path) and not os.path.islink(link_path):
            error(
                "create symlink at {}: path is a directory".format(link_path)
            )
            return False
        if not os.path.islink(link_path):
            error(
                "create symlink at {}: path is an existing file".format(link_path)
            )
            return False
        debug("removing existing symlink: {}".format(link_path))
        os.remove(link_path)

    try:
        os.symlink(target, link_path)
        debug("created symlink: {} -> {}".format(link_path, target))
        return True
    except OSError as e:
        error("create symlink {} -> {}: {}".format(link_path, target, e))
        return False


def remove_symlink(link_path):
    # type: (str) -> bool
    """Remove a symlink if it exists. Returns True if removed."""
    if os.path.lexists(link_path):
        os.remove(link_path)
        debug("removed symlink: {}".format(link_path))
        return True
    debug("symlink not found: {}".format(link_path))
    return False


def _resolve_link_target(link_path):
    # type: (str) -> str
    """Read a symlink and return its absolute target."""
    target = os.readlink(link_path)
    if not os.path.isabs(target):
        target = os.path.normpath(os.path.join(os.path.dirname(link_path), target))
    return target


def _is_symlink_to_devnull(path):
    # type: (str) -> bool
    """Return True if 'path' is a symlink pointing at /dev/null."""
    if not os.path.islink(path):
        return False
    return _resolve_link_target(path) == DEV_NULL


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_enable(name, runtime=False, visited=None):
    # type: (str, bool, Optional[Set[str]]) -> int
    """
    Enable a unit: create .wants/ and .requires/ symlinks from its
    [Install] section. Recursively processes Also=, protecting against
    cycles. Skips a unit that has already been processed.
    """
    if visited is None:
        visited = set()

    name = normalize_unit_name(name)
    if name in visited:
        debug("already processed: {}".format(name))
        return 0
    visited.add(name)

    unit_path = find_unit(name)
    if not unit_path:
        error("enable unit {}: Unit {} not found.".format(name, name))
        return 1

    install = parse_install_section(unit_path)
    if not install:
        error(
            "enable unit {}: Unit {} has no installation config.".format(name, name)
        )
        return 1

    base_dir = SYSTEMD_RUN_DIR if runtime else SYSTEMD_ETC_DIR
    success = True

    # WantedBy=  -> <target>.wants/<name> -> <unit_path>
    for target in install.get("WantedBy", []):
        link_path = os.path.join(base_dir, target + ".wants", name)
        if create_symlink(unit_path, link_path):
            print("Created symlink {} -> {}".format(link_path, unit_path))
        else:
            success = False

    # RequiredBy= -> <target>.requires/<name> -> <unit_path>
    for target in install.get("RequiredBy", []):
        link_path = os.path.join(base_dir, target + ".requires", name)
        if create_symlink(unit_path, link_path):
            print("Created symlink {} -> {}".format(link_path, unit_path))
        else:
            success = False

    # Alias= -> <base_dir>/<alias> -> <unit_path>
    for alias in install.get("Alias", []):
        link_path = os.path.join(base_dir, alias)
        if create_symlink(unit_path, link_path):
            print("Created symlink {} -> {}".format(link_path, unit_path))
        else:
            success = False

    # Also= pulls in additional units recursively
    for also in install.get("Also", []):
        if cmd_enable(also, runtime=runtime, visited=visited) != 0:
            success = False

    return 0 if success else 1


def _remove_wants_requires_links(base_dir, unit_path, name):
    # type: (str, Optional[str], str) -> bool
    """
    Walk subdirectories of base_dir whose name ends with .wants or
    .requires, and remove symlinks pointing at unit_path or having
    the same basename as 'name'.

    Only these two kinds of subdirectories are visited, so user-created
    override symlinks in the root of base_dir are never touched.
    """
    removed_any = False
    if not os.path.isdir(base_dir):
        return False

    for entry in os.listdir(base_dir):
        sub = os.path.join(base_dir, entry)
        # Skip non-directories and symlinks-to-directories
        if not os.path.isdir(sub) or os.path.islink(sub):
            continue
        if not (entry.endswith(".wants") or entry.endswith(".requires")):
            continue
        for item in os.listdir(sub):
            full = os.path.join(sub, item)
            if not os.path.islink(full):
                continue
            target = _resolve_link_target(full)
            if target == unit_path or os.path.basename(full) == name:
                if remove_symlink(full):
                    print("Removed {}".format(full))
                    removed_any = True
    return removed_any


def cmd_disable(name, runtime=False):
    # type: (str, bool) -> int
    """
    Disable a unit: remove .wants/.requires symlinks and Alias= symlinks
    that were created by enable. Never removes override files.
    """
    name = normalize_unit_name(name)
    unit_path = find_unit(name)
    if not unit_path:
        debug("unit file not found, still removing symlinks: {}".format(name))

    base_dir = SYSTEMD_RUN_DIR if runtime else SYSTEMD_ETC_DIR

    # 1) Remove links inside any <target>.wants / <target>.requires
    removed = _remove_wants_requires_links(base_dir, unit_path, name)

    # 2) Remove Alias= symlinks in the root of base_dir, but only those
    #    that resolve exactly to our unit path.
    if unit_path:
        install = parse_install_section(unit_path)
        for alias in install.get("Alias", []):
            link = os.path.join(base_dir, alias)
            if not os.path.islink(link):
                continue
            if _resolve_link_target(link) == unit_path:
                if remove_symlink(link):
                    print("Removed {}".format(link))
                    removed = True

    if not removed:
        debug("no symlinks found for {}".format(name))
    return 0


def cmd_mask(name, runtime=False):
    # type: (str, bool) -> int
    """
    Mask a unit: create a symlink <name> -> /dev/null.
    Refuses if anything already exists at that path.
    """
    base_dir = SYSTEMD_RUN_DIR if runtime else SYSTEMD_ETC_DIR
    link_path = os.path.join(base_dir, name)

    if os.path.lexists(link_path):
        if _is_symlink_to_devnull(link_path):
            error("mask unit {}: Unit {} is already masked.".format(name, name))
        else:
            error(
                "mask unit {}: Unit {} is already present in {}.".format(
                    name, name, base_dir
                )
            )
        return 1

    if create_symlink(DEV_NULL, link_path):
        print("Created symlink {} -> {}".format(link_path, DEV_NULL))
        return 0
    return 1


def cmd_unmask(name, runtime=False):
    # type: (str, bool) -> int
    """
    Unmask a unit: remove the /dev/null symlink created by mask.
    No-op (returns 0) if the unit is not masked.
    """
    base_dir = SYSTEMD_RUN_DIR if runtime else SYSTEMD_ETC_DIR
    link_path = os.path.join(base_dir, name)

    if not os.path.lexists(link_path):
        debug("nothing to unmask: {}".format(link_path))
        return 0

    if not _is_symlink_to_devnull(link_path):
        error("unmask unit {}: Unit {} is not masked.".format(name, name))
        return 1

    if remove_symlink(link_path):
        print("Removed {}".format(link_path))
        return 0
    return 1


def cmd_set_default(name, runtime=False):
    # type: (str, bool) -> int
    """
    Set the default target:
        <base_dir>/default.target -> <unit_path>
    """
    name = normalize_unit_name(name)
    unit_path = find_unit(name)
    if not unit_path:
        error("set-default {}: Unit {} not found.".format(name, name))
        return 1

    base_dir = SYSTEMD_RUN_DIR if runtime else SYSTEMD_ETC_DIR
    default_link = os.path.join(base_dir, "default.target")

    if os.path.lexists(default_link):
        if os.path.isdir(default_link) and not os.path.islink(default_link):
            error(
                "set-default: {} is a directory".format(default_link)
            )
            return 1
        os.remove(default_link)
        print("Removed {}".format(default_link))

    if create_symlink(unit_path, default_link):
        print("Created symlink {} -> {}".format(default_link, unit_path))
        return 0
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _add_runtime_flag(p, sub=False):
    # type: (argparse.ArgumentParser, bool) -> None
    """
    Add --runtime. On subparsers we use SUPPRESS so that the value from
    the top-level parser is not clobbered when the flag is missing.
    This lets both 'vsysctl --runtime enable foo' and
    'vsysctl enable --runtime foo' work identically.
    """
    kwargs = dict(
        action="store_true",
        help="Operate on /run/systemd/system instead of /etc/systemd/system",
    )
    if sub:
        kwargs["default"] = argparse.SUPPRESS
    p.add_argument("--runtime", **kwargs)


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    parser = argparse.ArgumentParser(
        prog="vsysctl",
        description="Minimal systemctl replacement for chroot environments.",
    )
    _add_runtime_flag(parser)

    sub = parser.add_subparsers(dest="command")
    # Python 3.6-compatible way to make the subcommand required.
    # (add_subparsers(required=True) exists only since 3.7.)
    sub.required = True

    p_enable = sub.add_parser("enable", help="Enable a unit")
    p_enable.add_argument("units", nargs="+", help="Unit name(s)")
    _add_runtime_flag(p_enable, sub=True)

    p_disable = sub.add_parser("disable", help="Disable a unit")
    p_disable.add_argument("units", nargs="+", help="Unit name(s)")
    _add_runtime_flag(p_disable, sub=True)

    p_mask = sub.add_parser("mask", help="Mask a unit")
    p_mask.add_argument("units", nargs="+", help="Unit name(s)")
    _add_runtime_flag(p_mask, sub=True)

    p_unmask = sub.add_parser("unmask", help="Unmask a unit")
    p_unmask.add_argument("units", nargs="+", help="Unit name(s)")
    _add_runtime_flag(p_unmask, sub=True)

    p_setdefault = sub.add_parser("set-default", help="Set default target")
    p_setdefault.add_argument("target", help="Target name (e.g. multi-user.target)")
    _add_runtime_flag(p_setdefault, sub=True)

    args = parser.parse_args(argv)
    runtime = bool(getattr(args, "runtime", False))

    if args.command == "enable":
        visited = set()  # type: Set[str]
        rc = 0
        for unit in args.units:
            rc |= cmd_enable(unit, runtime=runtime, visited=visited)
        return rc

    if args.command == "disable":
        rc = 0
        for unit in args.units:
            rc |= cmd_disable(unit, runtime=runtime)
        return rc

    if args.command == "mask":
        rc = 0
        for unit in args.units:
            rc |= cmd_mask(unit, runtime=runtime)
        return rc

    if args.command == "unmask":
        rc = 0
        for unit in args.units:
            rc |= cmd_unmask(unit, runtime=runtime)
        return rc

    if args.command == "set-default":
        return cmd_set_default(args.target, runtime=runtime)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())