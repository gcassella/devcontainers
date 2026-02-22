#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# ///

from utils import build_images
from utils import sync_files

def main():
  """Update all containers; sync files, build, and push."""
  sync_files.main()
  build_images.main()


if __name__ == '__main__':
  main()
