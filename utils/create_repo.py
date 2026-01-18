#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///

import os
import pathlib
import shutil
import subprocess
import traceback

from utils import shared

def create_repo(
    destination: pathlib.Path,
    container_name: str,
):
    """Creates a new git repository based on a devcontainer template."""
    root = pathlib.Path(os.getcwd())
    
    # Verify container exists
    source_path = root / container_name
    if not source_path.exists() or not (source_path / shared.DEVCONTAINER_FOLDER).exists():
        # Check if it is one of the valid container paths
        valid_paths = shared.get_container_paths(root)
        valid_names = [p.name for p in valid_paths]
        raise ValueError(f"Container '{container_name}' not found. Available containers: {', '.join(valid_names)}")

    if destination.exists():
        if any(destination.iterdir()):
             raise ValueError(f"Destination '{destination}' is not empty.")
    
    print(f"Initializing new repository at {destination} using '{container_name}' template...")

    def ignore_patterns(path, names):
        paths = [f'{os.path.join(path, name)}' for name in names]
        paths_by_name = {n: p for n, p in zip(names, paths)}
        paths_str = ' '.join(paths)
        check_ignore_stdout = subprocess.run(f'git check-ignore {paths_str}', capture_output=True).stdout
        if check_ignore_stdout is not None:
            ignored = check_ignore_stdout.decode().split('\n')
        else:
            ignored = []
        return [n for n in names if os.fspath(paths_by_name[n]) in ignored]

    shutil.copytree(source_path, destination, dirs_exist_ok=True, ignore=ignore_patterns, ignore_dangling_symlinks=True)

    # Initialize git
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=destination, check=True)
        subprocess.run(["git", "add", "."], cwd=destination, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=destination, check=True)
        print(f"Initialized new Git repository in {destination}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {traceback.format_exc()}")

def main(
    destination: pathlib.Path,
    container: str,
):
    create_repo(destination, container)
