from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool

import paths

MAX_READ_BYTES = 200_000

def _error(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def _resolve(workspace: Path, path: str) -> tuple[Path | None, dict | None]:
    raw = (path or "").strip()
    if not raw:
        return None, _error("INVALID_PATH", "Path rỗng. Dùng đường dẫn tương đối workspace, ví dụ data/weekly_notes.md.")
    if Path(raw).is_absolute() or raw.startswith("~"):
        return None, _error("PATH_OUTSIDE_WORKSPACE", f"Không chấp nhận đường dẫn tuyệt đối: {raw}. Dùng đường dẫn tương đối workspace.")
    root = workspace.resolve()
    target = (root / raw).resolve()
    if not target.is_relative_to(root):
        return None, _error("PATH_OUTSIDE_WORKSPACE", f"Đường dẫn thoát ra ngoài workspace: {raw}")
    return target, None

def _list(workspace: Path, path: str) -> dict:
    target, error = _resolve(workspace, path)
    if error:
        return error
    rel = target.relative_to(workspace.resolve()).as_posix()
    if not target.exists():
        return _error("PATH_NOT_FOUND", f"Không tìm thấy file: {rel}")
    if not target.is_dir():
        return _error("NOT_A_DIRECTORY", f"Đây không phải là thư mục: {rel}, nên dùng read_file")

    entries = []
    for child in sorted(target.iterdir(), key=lambda p : p.name):
        entries.append({
            "name": child.name,
            "path": child.relative_to(workspace.resolve()).as_posix(),
            "type": "directory" if child.is_dir() else "file",
        })
    return {"ok": True, "path": rel, "entries" : entries}


@tool 
def list_files(path : str) -> str:
    """
    Liệt kê các mục trực tiếp (không đệ quy) trong một thư mục. Dùng để tìm file khi chưa biết tên
    chính xác, rồi đọc bằng read_file.
    
    path là đường dẫn tương đối workspace, ví dụ ./data, ./output.
    Thành công: {"ok": true, "path": ..., "entries": [...]}, lỗi trả {"ok": false, "error": {...}}
    """
    return json.dumps(_list(paths.WORKSPACE_DIR, path), ensure_ascii=False)
