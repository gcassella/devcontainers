# Devcontainer Templates & Management

Contains a set of devcontainer configurations and a management utility to maintain them. Implements a hierarchical system where a `base` configuration is propagated to derived containers (like `python`).

## Structure

*   **`base/`**: The core devcontainer configuration. Contains the base `Dockerfile`, scripts, and `devcontainer.json` settings shared by all derived containers.
*   **`python/`**: A derived devcontainer specialized for Python development. It inherits from `base` but adds Python-specific extensions and tools.
*   **`manage.py`**: A CLI utility to manage the lifecycle of these containers (create, sync, build).
*   **`utils/`**: Implementation details for the management scripts.

## Usage

Uses `uv` for dependency management and script execution.

### Prerequisites

*   [uv](https://github.com/astral-sh/uv)
*   Docker

### Management CLI

The `manage.py` script is the entry point for all operations.

```bash
# List available commands
uv run ./manage.py --help
```

#### Commands

*   **`create <name>`**
    Create a new devcontainer derived from `base`.
    ```bash
    ./manage.py create my-new-language
    ```
    This creates a new directory `my-new-language`, sets up the folder structure, and performs an initial sync from `base`.

*   **`sync-files`**
    Propagate changes from `base` to all derived containers.
    ```bash
    ./manage.py sync-files
    ```
    Use this after modifying `base` files to update downstream containers. See [Syncing Mechanism](#syncing-mechanism) for details.

*   **`build-images`**
    Build and push Docker images for all containers.
    ```bash
    ./manage.py build-images
    ```
    Images are tagged as `{REGISTRY}/devcontainer-{name}:latest`.
    *   Default registry: `gwmcassella`
    *   Override via env var: `DOCKER_REGISTRY_PATH`

*   **`update-all`**
    Run `sync-files` followed by `build-images`.
    ```bash
    ./manage.py update-all
    ```

## Syncing Mechanism

The `sync-files` utility ensures derived containers stay up-to-date with `base` using a few rules:

1.  **JSON Files (e.g., `devcontainer.json`)**:
    *   Lists (like `extensions`) are merged. derived containers inherit all base extensions and can add their own.
    *   Other keys in derived files are overwritten by values from `base` if they exist in `base`.
    *   *Special Case*: The `image` property in `devcontainer.json` is automatically updated to reflect the derived container.

2.  **Text Files (Code/Scripts)**:
    *   **Full Copy**: If a file exists in `base` but not in the derived folder, it is copied over entirely.
    *   **Partial Sync**: You can define sync regions using tags in comments:
        ```python
        # [SYNC: region_name]
        shared_code = "this comes from base"
        # [/SYNC: region_name]
        ```
        Content within these tags in `base` will overwrite the corresponding tagged content in derived files. Note that the sync tags are format agnostic and can be used in any file, but you may need to register a suitable comment prefix in `utils.sync_files.COMMENT_PREFIX_BY_FILE_SUFFIX`. The default comment prefix is `#`, suitable for bash and python files.

3.  **Dockerfiles**:
    *   If a derived container is missing a `Dockerfile`, a template inheriting from the base image is created:
        ```dockerfile
        FROM gwmcassella/devcontainer-base:latest
        ```

## Development

To add a new feature to all containers:
1.  Modify `base`.
2.  Run `./manage.py sync-files`.
3.  Commit changes in `base` and the updates in derived folders.
