"""Đo tỉ lệ agent stage 03 gọi bash theo cách diễn đạt câu hỏi. Chạy trong WSL."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
LAB = "/mnt/d/Downloads/agent-tools-skills-lab/agent-tools-skills-lab"
SP = Path(__file__).resolve().parent
PY = str(Path.home() / ".venvs/agent-tools-skills-lab/bin/python")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6

VARIANTS = {
    "P0-goc": None,
    "P1": "Hãy dùng tool bash để chạy lệnh Python tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng.",
    "P2": "Dùng tool bash chạy Python để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Sau khi chạy, cho biết cách xử lý dòng lỗi và task_id trùng.",
    "P3": "Dùng Python qua Bash để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng. Bạn có tool bash, hãy gọi nó để chạy.",
}


def run(job):
    name, i = job
    out = SP / "probe_stage03" / name
    out.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(SP / "run_like_app.py"), "--stage", f"{LAB}/stage-03-bash", "--case", "stage03",
           "--traces-out", str(out), "--reports-out", str(out / "reports"), "--answers-out", str(out / "answers.md"), "--label", f"{name}-{i}"]
    if VARIANTS[name]:
        cmd += ["--text", VARIANTS[name]]
    subprocess.run(cmd, capture_output=True, text=True, timeout=300)


jobs = [(n, i) for n in VARIANTS for i in range(N)]
with ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(run, jobs))

print(f"{'câu hỏi':8} {'n':>2} {'gọi bash':>8} {'dedupe task_id':>14}  ghi chú")
for name in VARIANTS:
    traces = sorted((SP / "probe_stage03" / name).glob("*.jsonl"))
    used, dedupe, notes = 0, 0, []
    for t in traces:
        cmds = []
        for line in t.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e["type"] == "tool_started" and e["tool_name"] == "bash":
                cmds.append(e["arguments"].get("command", ""))
        if cmds:
            used += 1
            joined = "\n".join(cmds)
            if any(k in joined for k in ("seen", "drop_duplicates", "set()", "unique")):
                dedupe += 1
    print(f"{name:8} {len(traces):>2} {used:>8} {dedupe:>14}")
