"""Utility to locate likely demo/example files to clean up.

This script prints candidate demo files and directories. It does not delete by default;
pass `--delete` to actually remove them. Use carefully.
"""
import argparse
import os
from pathlib import Path


def find_demo_paths(root: Path):
    candidates = []
    for p in root.rglob("*"):
        name = p.name.lower()
        if any(k in name for k in ("demo", "example", "sample")):
            candidates.append(p)
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Project root to scan")
    parser.add_argument("--delete", action="store_true", help="Delete found demo files")
    args = parser.parse_args()

    root = Path(args.root)
    candidates = find_demo_paths(root)

    if not candidates:
        print("No demo/example files found.")
        return

    print("Found demo/example files:")
    for c in candidates:
        print(c)

    if args.delete:
        for c in candidates:
            try:
                if c.is_file():
                    c.unlink()
                else:
                    # careful: only remove empty dirs
                    try:
                        c.rmdir()
                    except Exception:
                        pass
                print(f"Removed {c}")
            except Exception as e:
                print(f"Failed to remove {c}: {e}")


if __name__ == "__main__":
    main()
