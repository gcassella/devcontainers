import pathlib

DEVCONTAINER_FOLDER = ".devcontainer"


def get_container_paths(root: pathlib.Path) -> list[pathlib.Path]:
  """Get all paths in root containing a .devcontainer subdirectory."""
  return [
    path
    for path in pathlib.Path(root).iterdir()
    if path.is_dir() and (path / DEVCONTAINER_FOLDER).exists()
  ]
