# tools/__init__.py
from tools.files import read_file, write_file, list_files

__all__ = ["read_file", "write_file", "list_files"]

# agent.py
from tools import read_file, write_file, list_files

TOOLS = [read_file, write_file, list_files]
