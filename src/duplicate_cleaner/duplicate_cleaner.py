import argparse
import errno
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path

B_RED = "\033[1;31m"
GREEN = "\033[0;32m"
RST = "\033[0m"


def color_print(color: str, msg: str) -> None:
    if color not in [B_RED, GREEN]:
        raise RuntimeError(f"ERROR: color '{color!r}' undefined")
    print(f"{color}{msg}{RST}")


def calculate_file_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, FileNotFoundError, OSError) as e:
        color_print(B_RED, f"Failed reading '{file_path}': {e}")
        return None


def find_duplicate_files(root_dir: Path, recurse: bool) -> dict[str, list]:
    size_groups = defaultdict(list)
    duplicates = defaultdict(list)

    color_print(GREEN, "Scanning directories structures for file sizes...")

    search_pattern = "**/*" if recurse else "*"
    for fpath in root_dir.glob(search_pattern):
        try:
            if fpath.is_dir() and not fpath.is_symlink():
                continue

            fsize = fpath.stat().st_size
            size_groups[fsize].append(fpath)
        except OSError as e:
            if os.path.islink(fpath):
                if e.errno == errno.ENOENT:
                    color_print(B_RED, f"[Broken Symlink] '{fpath}' is broken.")
                elif e.errno == errno.ELOOP:
                    color_print(B_RED, f"[Symlink Loop] '{fpath}' forms a loop")
                else:
                    color_print(
                        B_RED, f"[OSError Symlink] Failed to access link '{fpath}': {e}"
                    )
            else:
                color_print(
                    B_RED, f"[OSError File] Failed to get size for '{fpath}': {e}"
                )
            continue

    color_print(GREEN, "Calculating file hashes...")
    for paths in size_groups.values():
        if len(paths) < 2:
            continue

        for file_path in paths:
            file_hash = calculate_file_hash(file_path)
            if file_hash:
                duplicates[file_hash].append(file_path)
    result = {h: paths for h, paths in duplicates.items() if len(paths) > 1}
    for file_paths in result.values():
        file_paths.sort(key=lambda p: len(str(p)))
    return result


def symlink_depth(path: Path) -> int:
    path = path.absolute()
    depth = 0
    seen = set()

    while path.is_symlink():
        if path in seen:
            raise RuntimeError("Symlink loop detected")
        seen.add(path)

        target = Path(path.readlink())
        if not target.is_absolute():
            target = path.parent / target

        path = target.absolute()
        depth += 1
    return depth


def flatten_symlink_chain(first: Path) -> None:
    first = first.absolute()
    current = first
    links = []
    seen = set()

    while current.is_symlink():
        current = current.absolute()
        if current in seen:
            raise RuntimeError("Symlink loop detected")
        seen.add(current)
        links.append(current)

        target = Path(current.readlink())
        current = target if target.is_absolute() else current.parent / target

    final_target = current.resolve(strict=True)  # existence guaranteed

    for link in links[1:]:
        link.unlink()

    first.unlink()
    first.symlink_to(final_target)


def remove_empty_directories(root_folder: Path):
    color_print(GREEN, "Cleaning up empty directories...")

    all_dirs = [p for p in root_folder.rglob("*") if p.is_dir() and not p.is_symlink()]
    all_dirs.sort(key=lambda p: len(p.parts), reverse=True)

    for dir_path in all_dirs:
        if not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
                color_print(GREEN, "[Removed Empty Dir] -> {dir_path}")
            except OSError as e:
                color_print(B_RED, f"ERROR: failed removing a dir:{e}")


def remove_duplicate_files(duplicates: dict) -> None:
    for file_paths in duplicates.values():
        color_print(GREEN, f"Duplicates found (keeping: {file_paths[0]}):")
        for to_delete in file_paths[1:]:
            color_print(GREEN, f"[Deleting] -> {to_delete}")
            try:
                if to_delete.is_symlink():
                    flatten_symlink_chain(to_delete)
                    to_delete.unlink(missing_ok=True)
                else:
                    to_delete.unlink(missing_ok=True)
            except OSError as e:
                color_print(B_RED, f"[Error] Failed deleting {to_delete}: {e}")


def parse_args():
    parser = argparse.ArgumentParser("Duplicate cleaner script")
    parser.add_argument(
        "-t",
        "--target",
        dest="root_dir",
        type=Path,
        default=Path.home(),
        help="Path to target directory",
    )

    parser.add_argument(
        "-r",
        "--recurse",
        dest="recursive",
        action="store_true",
        help="Scan subdirectories recursively",
    )

    parser.add_argument(
        "-nc",
        "--no-confirm",
        dest="no_confirm",
        action="store_true",
        help="Delete duplicates without confirmation prompt",
    )

    parser.add_argument(
        "-re",
        "--remove-empty",
        dest="remove_empty_dirs",
        action="store_true",
        help="Remove empty directories after cleanup",
    )

    def check_root_dir(rd: Path) -> None:
        if not rd.exists():
            color_print(B_RED, f"Error: path '{rd}' not found")
            parser.print_help()
            sys.exit(-1)

        if not rd.is_dir():
            color_print(B_RED, f"Error: '{rd.__str__()}' is not a directory. Aborted")
            parser.print_help()
            sys.exit(-1)

    try:
        args = parser.parse_args()
        args.root_dir = args.root_dir.resolve()
        check_root_dir(args.root_dir)
        return args
    except argparse.ArgumentError as e:
        color_print(B_RED, f"Error parsing args: {e}")
        parser.print_help()
        sys.exit(-1)


def main():
    args = parse_args()

    duplicates: dict = find_duplicate_files(args.root_dir, args.recursive)

    if not duplicates:
        color_print(GREEN, "Duplicates not found")
    else:
        if args.no_confirm:
            remove_duplicate_files(duplicates)
            if args.remove_empty_dirs:
                remove_empty_directories(args.root_dir)
        else:
            duplicate_count = len(duplicates)
            decision = input(
                f"{GREEN}\nFound {duplicate_count} duplicate groups. "
                f"Remove them?(y/N): "
            )
            if decision.lower() == "y":
                remove_duplicate_files(duplicates)
                if args.remove_empty_dirs:
                    remove_empty_directories(args.root_dir)
            else:
                color_print(B_RED, "File deletion aborted")
