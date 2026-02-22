#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer",
# ]
# ///

import pathlib
from typing import Annotated

import typer # pyright: ignore[reportMissingImports]

from utils import build_images
from utils import create_repo
from utils import sync_files
from utils import update_all

app = typer.Typer()


@app.command(name="build-images")
def build_images_command():
    """Build and push docker images."""
    build_images.main()


@app.command(name="create-repo")
def create_repo_command(
    path: Annotated[pathlib.Path, typer.Argument(help="Path to the new repository.")],
    container: Annotated[str, typer.Argument(help="Name of the devcontainer to use.")]
):
    """Create a new git repository based on a devcontainer."""
    create_repo.main(destination=path, container=container)


@app.command(name="sync-files")
def sync_files_command():
    """Sync files from base to derived containers."""
    sync_files.main()


@app.command(name="update-all")
def update_all_command():
    """Sync files and then build images."""
    update_all.main()


@app.command(name="create")
def create_command(name: Annotated[str, typer.Argument(help="The name of the new devcontainer.")]):
    """Create a new devcontainer from base."""
    new_path = pathlib.Path(name)
    new_path.mkdir()
    (new_path / '.devcontainer').mkdir()

    sync_files.main()

    # Re-sync devcontainer.json to update the image name.
    sync_files.sync_json(
        base_path=pathlib.Path('base') / '.devcontainer' / 'devcontainer.json',
        derived_path=new_path / '.devcontainer' / 'devcontainer.json',
    )


if __name__ == "__main__":
    app()
