#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///

from collections.abc import Sequence
import dataclasses
import json
import os
import pathlib
import re
import shutil
from typing import Any

from utils import shared

OPEN_SYNC_PATTERN = r"{}\s*?\[SYNC:\s+([\w\d]+)\]\n?"
CLOSE_SYNC_PATTERN = r"{}\s*?\[\/SYNC:\s+([\w\d]+)\]\n?"
DOCKERFILE_TEMPLATE = """FROM gwmcassella/devcontainer-base:latest\n"""
COMMENT_PREFIX_BY_FILE_SUFFIX = {}


@dataclasses.dataclass(frozen=True)
class SyncPart:
  """Part of file to be synchronized from base content to derived content.

  Fields:
      start: Index of start of sync part in base file.
      end: Index of end of sync part in base file, exclusive.
      tag: Tag of sync part.
      content: Contents of sync part.
  """

  start: int
  end: int
  tag: str
  content: str


class JSONWithCommentsDecoder(json.JSONDecoder):
  """JSON Decoder which strips C-style comments before decoding."""

  _pattern: re.Pattern = re.compile(
    r"[ \t\n\r]*", re.VERBOSE | re.MULTILINE | re.DOTALL
  )

  def decode(
    self,
    s: str,
    _w=_pattern.match,
  ) -> Any:
    lines = s.split("\n")
    non_comment_lines = [l for l in lines if not l.lstrip().startswith("//")]
    s = "\n".join(non_comment_lines)
    return super().decode(s, _w)


def read_sync_parts(
  *,
  content: str,
  comment_prefix: str = "#",
) -> dict[str, SyncPart]:
  """Extract lines between sync tags from content.

  Args:
      content: String containing [SYNC: x] -> [/SYNC: x] tags.
      comment_prefix: Substring indicating beginning of comment, used to extend
          match for sync tags so we don't clone comment prefixes.

  Returns:
      Dictionary mapping sync tag labels (e.g. x for [SYNC: x]) to content
      between opening and closing sync tag.
  """
  # Match every pair of opening / closing sync tags and build dict.
  parts_by_tag: dict[str, SyncPart] = {}
  for open_match, close_match in zip(
    re.finditer(OPEN_SYNC_PATTERN.format(comment_prefix), content),
    re.finditer(CLOSE_SYNC_PATTERN.format(comment_prefix), content),
    strict=True,
  ):
    open_match_name = open_match.group(1)
    close_match_name = close_match.group(1)

    if open_match_name != close_match_name:
      raise ValueError(
        f"{open_match_name=} does not match {close_match_name=}. "
        "Overlapping sync tags not allowed."
      )

    if open_match_name in parts_by_tag:
      raise ValueError(
        f"Found duplicate sync tag {open_match_name}. Sync tags must be unique."
      )

    # Take content from end of open tag to start of close tag.
    parts_by_tag[open_match_name] = SyncPart(
      start=open_match.span(0)[1],
      end=close_match.span(0)[0],
      tag=open_match_name,
      content=content[open_match.span(0)[1] : close_match.span(0)[0]],
    )
  return parts_by_tag


def substitute_sync_parts(
  *,
  content: str,
  sync_parts: dict[str, SyncPart],
  comment_prefix: str = "#",
) -> str:
  """Substitute parts from sync_parts into content between sync tags.

  Args:
      content: String containing [SYNC: x] tags.
      sync_parts: Dictionary mapping sync tag labels (e.g. x for [SYNC: x]) to
          content to substitute after sync tag.
      comment_prefix: Substring indicating beginning of comment, used to extend
          match for sync tags so we don't snip comment prefixes.

  Returns:
      Content with sync_parts inserted after tags.
  """
  open_pattern = OPEN_SYNC_PATTERN.format(comment_prefix)
  close_pattern = CLOSE_SYNC_PATTERN.format(comment_prefix)

  return re.sub(
    f"({open_pattern}).*?({close_pattern})",
    lambda match: f"{match.group(1)}{sync_parts[match.group(2)].content}{match.group(3)}",
    content,
    flags=re.DOTALL,
  )


def apply_sync_tags(
  *,
  base_path: pathlib.Path,
  derived_path: pathlib.Path,
  comment_prefix: str = "#",
) -> None:
  """Apply all sync tags from base_path to derived_path.

  Args:
    base_path: Path to base file containing [SYNC: x] tags.
    derived_path: Path to derived file containing [SYNC: x] tags.
    comment_prefix: Substring indicating beginning of comment, used to extend
          match for sync tags so we don't snip comment prefixes.
  """
  base_content = base_path.read_text()
  derived_content = derived_path.read_text()

  sync_parts = read_sync_parts(content=base_content, comment_prefix=comment_prefix)
  derived_sync_parts = read_sync_parts(
    content=derived_content,
    comment_prefix=comment_prefix,
  )

  # Ensure all derived_sync_parts exist in sync_parts.
  if not (derived_set := set(derived_sync_parts.keys())).issubset(
    (base_set := set(sync_parts.keys()))
  ):
    mismatch_tags = ", ".join(derived_set - base_set)
    raise ValueError(
      "Sync tags in derived file must be subset of sync tags in base file."
      f" {mismatch_tags=}."
    )

  synced_content = substitute_sync_parts(
    content=derived_content,
    sync_parts=sync_parts,
    comment_prefix=comment_prefix,
  )
  derived_path.write_text(synced_content)


def sync_json(
  *,
  base_path: pathlib.Path,
  derived_path: pathlib.Path,
):
  """Sync JSON contents from base_path to derived_path.

  Values are synced according to the rules:
    - If value is a list, insert any entries from base list missing from
      derived list
    - Otherwise, overwrite derived values

  Args:
    base_path: Path to base file.
    derived_path: Path to derived file.
  """
  base_dict = json.loads(base_path.read_text(), cls=JSONWithCommentsDecoder)
  derived_dict = json.loads(derived_path.read_text(), cls=JSONWithCommentsDecoder)

  def traverse_derived(path: Sequence[str]) -> dict:
    dict_ref = derived_dict
    # Traverse to the end of the path.
    for path_entry in path[:-1]:
      if not path_entry in dict_ref:
        dict_ref[path_entry] = {}
      dict_ref = dict_ref[path_entry]
    return dict_ref

  def write_to_path(
    path: Sequence[str],
    value: dict | list | str | int | float | bool | None,
  ):
    dict_ref = traverse_derived(path)
    # Make an exception for writing the 'image' field in devcontainer.json.
    # Substitute 'base' for the name of the derived container.
    if path[-1] == 'image' and base_path.name == 'devcontainer.json':
      assert isinstance(value, str)
      idx = base_path.parts.index('base')
      dict_ref[path[-1]] = value.replace('base', derived_path.parts[idx])
    else:
      dict_ref[path[-1]] = value

  def get_from_path(
    path: Sequence[str],
  ) -> dict | list | str | int | float | bool | None:
    dict_ref = traverse_derived(path)
    return dict_ref.get(path[-1])

  def recursive_sync(
    base_entry: dict | list | str | int | float | bool | None,
    base_path: list[str],
  ):
    if isinstance(base_entry, dict):
      for key, value in base_entry.items():
        recursive_sync(value, base_path + [key])
    elif isinstance(base_entry, list):
      derived_entry = get_from_path(base_path)
      if derived_entry is None or not isinstance(derived_entry, list):
        combined_entry = []
      else:
        difference = set(base_entry) - set(derived_entry)
        combined_entry = derived_entry + list(difference)
      write_to_path(base_path, combined_entry)
    else:
      write_to_path(base_path, base_entry)

  recursive_sync(base_dict, [])
  derived_path.write_text(json.dumps(derived_dict, indent=4))


def sync_file(
  *,
  base_path: pathlib.Path,
  derived_path: pathlib.Path,
) -> None:
  """Synchronize a file from base_path to derived_path.

  Files are synchronized according to the following rules in order:
    - Dockerfiles that do not exist at derived are instantiated to empty template.
    - Non-Dockerfiles that exist at base but not derived are copied.
    - Non JSON files with sync tags have tagged portions written from base to derived.
    - JSON files are synced from base to derived, ovewriting entries in derived
      with values from base.

  Args:
    base_path: Path to base file.
    derived_path: Path to derived file.

  Raises:
    ValueError if base path does not exist, or path names do not match.
  """
  if not base_path.exists():
    raise ValueError(f"Trying to sync a path from base that doesn't exist {base_path}")

  if not base_path.name == derived_path.name:
    raise ValueError(
      f"Trying to sync files with different names: {base_path} <-> {derived_path}"
    )

  if not derived_path.exists():
    if derived_path.name == "Dockerfile":
      derived_path.write_text(DOCKERFILE_TEMPLATE)
      return
    else:
      shutil.copyfile(base_path, derived_path)
      return

  if derived_path.suffix == ".json":
    sync_json(
      base_path=base_path,
      derived_path=derived_path,
    )
    return
  else:
    apply_sync_tags(
      base_path=base_path,
      derived_path=derived_path,
      comment_prefix=COMMENT_PREFIX_BY_FILE_SUFFIX.get(derived_path.suffix, '#'),
    )
    return


def recursive_sync_files(
  *,
  base_path: pathlib.Path,
  derived_path: pathlib.Path,
):
  """Recurse through files in base_path and sync to derived_path."""
  if base_path.is_dir():
    if not derived_path.exists():
      derived_path.mkdir(parents=True)

    for path in base_path.iterdir():
      leaf_path = path.relative_to(base_path)
      recursive_sync_files(base_path=path, derived_path=derived_path / leaf_path)
  else:
    # Make sure everything is using LF not CRLF. Windows is dumb.
    base_path.write_bytes(base_path.read_bytes().replace(b"\r\n", b"\n"))
    sync_file(
      base_path=base_path,
      derived_path=derived_path,
    )
    derived_path.write_bytes(derived_path.read_bytes().replace(b"\r\n", b"\n"))


def main():
  """Synchronize all files from base to derived containers."""
  root = pathlib.Path(os.getcwd())

  container_paths_by_name = {
    path.name: path for path in shared.get_container_paths(root)
  }
  base_path = container_paths_by_name["base"]
  del container_paths_by_name["base"]

  for container_path in container_paths_by_name.values():
    recursive_sync_files(
      base_path=base_path,
      derived_path=container_path,
    )


if __name__ == "__main__":
  main()
