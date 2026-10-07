"""Thống kê việc đọc template và độ đầy đủ của báo cáo. argv: <file jsonl>..."""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
TEMPLATE = "skills/csv-quality/references/report-template.md"
REPORT_PATH = {"nguong8": "output/workload.md", "nguong9": "output/workload-9.md"}

for path in sys.argv[1:]:
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    print("==", path.split("/")[-1])
    for pid in ["nguong8", "nguong9", "thieu", "khongco", "para1"]:
        rs = [r for r in recs if r["prompt_id"] == pid and "error" not in r]
        if not rs:
            continue
        tpl = sum(any(s["name"] == "read_file" and s["args"].get("path") == TEMPLATE for s in r["turn_steps"][0]) for r in rs)
        ok = sum(1 for r in rs if r["eval"].get("ok"))
        extra = ""
        if pid in REPORT_PATH:
            reports = [r["written"].get(REPORT_PATH[pid]) or "" for r in rs]
            header = sum(1 for c in reports if "check_csv.py" in c)  # dòng "Công cụ: ..." của template
            code = sum(1 for c in reports if all(x in c for x in ("invalid_hours", "duplicate_id", "missing_owner")) or pid == "nguong9" and False)
            extra = f" | báo cáo có dòng 'Công cụ' của template {header}/{len(rs)} | có đủ 3 mã lý do {code}/{len(rs)}"
        print(f"   {pid:8} n={len(rs):>2} ĐẠT={ok:>2} đọc template={tpl:>2}{extra}")
