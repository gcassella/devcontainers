#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///

import os
import pathlib
import subprocess
import sys

from utils import shared

BASE_DIR = "base"
DEVCONTAINER_FOLDER = ".devcontainer"
DOCKERFILE_NAME = "Dockerfile"
REGISTRY_PATH = os.environ.get('DOCKER_REGISTRY_PATH') or 'gwmcassella'

def run_command(command: list[str], cwd: pathlib.Path | None = None) -> None:
  """Run a shell command in cwd and raise an exception on failure."""
  cmd_str = " ".join(command)
  print(f"Running: {cmd_str}")
  try:
    subprocess.run(command, check=True, cwd=cwd)
  except subprocess.CalledProcessError as e:
    print(f"Error executing command: {cmd_str}")
    sys.exit(e.returncode)


def build_and_push_image(
  *,
  dockerfile_path: pathlib.Path,
  image_name: str,
) -> None:
  """Build image at dockerfile_path and pushes image_name to registry."""
  if not dockerfile_path.exists():
    raise ValueError(f"Dockerfile not found at {dockerfile_path}")

  build_cmd = [
    "docker",
    "build",
    "-f",
    str(dockerfile_path),
    "-t",
    image_name,
    # Use equivalent of 'base' directory as build context.
    str(dockerfile_path.parents[1]),
  ]

  run_command(build_cmd)
  run_command(["docker", "push", image_name])


def main():
  """Build all devcontainer images and push to registry."""
  root = pathlib.Path(os.getcwd())
  container_paths = shared.get_container_paths(root)
  container_paths = sorted(
    container_paths, key=lambda path: 0 if path.name == BASE_DIR else 1
  )
  for container_path in container_paths:
    image_name = f"{REGISTRY_PATH}/devcontainer-{container_path.name}"
    build_and_push_image(
      dockerfile_path=container_path / DEVCONTAINER_FOLDER / DOCKERFILE_NAME,
      image_name=image_name,
    )


if __name__ == "__main__":
  main()
