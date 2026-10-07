"""Đếm báo cáo còn sót hướng dẫn của template. argv: <jsonl>..."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
MARKERS = {"'Nếu `' (hướng dẫn điều kiện)": "Nếu `", "'Nêu rằng' (hướng dẫn Đánh giá)": "Nêu rằng", "'Diễn giải mã lý do' (chú giải mã)": "Diễn giải mã lý do",
           "còn '{...}' chưa thay": "{"}
for path in sys.argv[1:]:
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    print("==", path.replace("\\", "/").split("/")[-1])
    for pid, rp in (("nguong8", "output/workload.md"), ("nguong9", "output/workload-9.md")):
        rs = [r for r in recs if r["prompt_id"] == pid and "error" not in r]
        if not rs:
            continue
        ok = sum(1 for r in rs if r["eval"].get("ok"))
        tpl = sum(any(s["name"] == "read_file" and s["args"].get("path", "").endswith("report-template.md") for s in r["turn_steps"][0]) for r in rs)
        codes = sum(1 for r in rs if all(x in (r["written"].get(rp) or "") for x in ("invalid_hours", "duplicate_id", "missing_owner")))
        leaks = {k: sum(1 for r in rs if m in (r["written"].get(rp) or "")) for k, m in MARKERS.items()}
        print(f"   {pid}: n={len(rs)} ĐẠT={ok} đọc template={tpl} đủ 3 mã lý do={codes}")
        print("      sót:", ", ".join(f"{k}: {v}" for k, v in leaks.items()))
