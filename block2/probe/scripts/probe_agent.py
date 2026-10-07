"""Chạy agent của stage 04 headless trên workspace tạm để đo hành vi theo phiên bản skill.

Cách dùng (trong WSL):
    python probe_agent.py --stage <thư mục stage-04> --variant <tên> [--skill <file SKILL.md thay thế>] --n 6 --out <file.jsonl>

Không ghi vào traces/ hay workspace/ của project: mỗi lượt chạy dùng bản sao workspace trong thư mục tạm.
API key chỉ được nạp qua load_settings() của project; script không in biến môi trường.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROMPTS = {
    # 4 câu của đề
    "nguong8": "Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md.",
    "nguong9": "Kiểm tra data/workload.csv, người nào vượt 9 giờ? Ghi báo cáo vào output/workload-9.md.",
    "thieu": "Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải.",
    "khongco": "Kiểm tra data/khong-co.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/khong-co.md.",
    # câu diễn đạt khác, không có trong đề, để kiểm tra mô tả skill không bị khớp quá hẹp
    "para1": "Ai làm quá 10 giờ trong data/workload.csv?",
    "para2": "Cho tôi tổng giờ của từng người trong data/workload.csv, ngưỡng cảnh báo là 7.5 giờ.",
    "para3": "Rà soát file data/workload-edge.csv, ai vượt 4 giờ thì báo cho tôi, ghi kết quả ra output/edge.md.",
    "cont10": "Còn nếu ngưỡng là 10 giờ thì sao?",
    # skill khác không được bị csv-quality chiếm chỗ
    "weekly": "Tạo báo cáo tuần từ data/weekly_notes.md, lưu vào output/weekly-report.md.",
}
# Nhiều lượt trong cùng một cuộc trò chuyện: lượt 2 không nêu ngưỡng, phải hỏi lại thay vì dùng ngưỡng của lượt 1
TURNS = {"carry": ["nguong8", "thieu"], "carry2": ["nguong8", "cont10"]}
EXPECT_THRESHOLD = {"nguong8": "8", "nguong9": "9", "khongco": "8", "para1": "10", "para2": "7.5", "para3": "4", "carry2": "10"}
CSV_SKILL = "skills/csv-quality/SKILL.md"
WEEKLY_SKILL = "skills/weekly-report/SKILL.md"


def scrub(text: str) -> str:
    return re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "sk-***", text or "")


def summarize_steps(collected, ToolMessage, AIMessage) -> list[dict]:
    results_by_id = {}
    for m in collected:
        if isinstance(m, ToolMessage):
            try:
                results_by_id[m.tool_call_id] = json.loads(m.content)
            except Exception:
                results_by_id[m.tool_call_id] = {"raw": str(m.content)[:200]}
    steps = []
    for m in collected:
        if isinstance(m, AIMessage):
            for call in m.tool_calls:
                result = results_by_id.get(call["id"], {})
                steps.append(
                    {
                        "name": call["name"],
                        "args": call["args"],
                        "ok": result.get("ok"),
                        "exit_code": result.get("exit_code"),
                        "stdout": result.get("stdout") if call["name"] == "bash" else None,
                    }
                )
    return steps


def one_run(stage: str, skill_override: str | None, prompt_id: str, run_idx: int, template_override: str | None = None) -> dict:
    sys.path.insert(0, stage)
    import paths
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    tmp = Path(tempfile.mkdtemp(prefix="b2probe-"))
    started = time.time()
    record = {"prompt_id": prompt_id, "run": run_idx}
    try:
        workspace = tmp / "workspace"
        shutil.copytree(Path(stage) / "workspace", workspace)
        if skill_override:
            shutil.copyfile(skill_override, workspace / CSV_SKILL)
        if template_override:
            shutil.copyfile(template_override, workspace / "skills/csv-quality/references/report-template.md")
        paths.WORKSPACE_DIR = workspace
        paths.TRACES_DIR = tmp / "traces"
        from agent import build_agent, build_model
        from config import RECURSION_LIMIT, load_settings

        settings, missing = load_settings()
        if settings is None:
            raise RuntimeError(f"Thiếu cấu hình: {missing}")
        record["model"] = settings.model_name
        agent = build_agent(build_model(settings))

        history = []
        turn_steps, turn_finals = [], []
        for turn_id in TURNS.get(prompt_id, [prompt_id]):
            history.append(HumanMessage(content=PROMPTS[turn_id]))
            start_len = len(history)
            for mode, chunk in agent.stream({"messages": history}, config={"recursion_limit": RECURSION_LIMIT}, stream_mode=["updates", "custom"]):
                if mode == "updates" and isinstance(chunk, dict):
                    for update in chunk.values():
                        if isinstance(update, dict) and update.get("messages"):
                            history.extend(update["messages"])
            new_messages = history[start_len:]
            turn_steps.append(summarize_steps(new_messages, ToolMessage, AIMessage))
            turn_finals.append(next((m.text for m in reversed(new_messages) if isinstance(m, AIMessage) and not m.tool_calls), ""))

        # write_file: lấy nội dung từ lời gọi (không có trong ToolMessage)
        contents = {}
        for m in history:
            if isinstance(m, AIMessage):
                for call in m.tool_calls:
                    if call["name"] == "write_file":
                        contents[call["args"].get("path")] = call["args"].get("content")
        record["turn_steps"] = turn_steps
        record["turn_finals"] = turn_finals
        record["written"] = contents
        record["output_files"] = sorted(p.name for p in (workspace / "output").glob("*")) if (workspace / "output").exists() else []
    except Exception as exc:
        record["error"] = scrub(f"{type(exc).__name__}: {str(exc)[:300]}")
    finally:
        record["seconds"] = round(time.time() - started, 1)
        shutil.rmtree(tmp, ignore_errors=True)
    return record


def script_runs(steps):
    return [s for s in steps if s["name"] == "bash" and "check_csv.py" in (s["args"].get("command") or "")]


def threshold_matches(runs, value):
    pattern = rf"--max-hours\s+['\"]?{re.escape(value)}['\"]?(\s|$)"
    return any(re.search(pattern, s["args"].get("command") or "") for s in runs)


def parse_json(runs):
    for s in runs:
        if s.get("exit_code") == 0 and s.get("stdout"):
            try:
                return json.loads(s["stdout"])
            except Exception:
                return None
    return None


def classify(rec: dict) -> dict:
    """Đánh giá tự động theo tiêu chí của đề, chỉ dựa trên tool call và nội dung thật."""
    pid = rec["prompt_id"]
    steps_all = [s for turn in rec["turn_steps"] for s in turn]
    # carry: chỉ xét lượt cuối (lượt không nêu ngưỡng)
    steps = rec["turn_steps"][-1] if pid in TURNS else steps_all
    final = rec["turn_finals"][-1]
    final_l = final.lower()
    runs = script_runs(steps)
    data = parse_json(runs)
    wrote = [s for s in steps if s["name"] == "write_file"]
    csv_loaded = any(s["name"] == "read_file" and s["args"].get("path") == CSV_SKILL and s.get("ok") for s in steps)
    weekly_loaded = any(s["name"] == "read_file" and s["args"].get("path") == WEEKLY_SKILL and s.get("ok") for s in steps)
    first = steps[0] if steps else None
    skill_first = bool(first and first["name"] == "read_file" and first["args"].get("path") == CSV_SKILL)
    thr = EXPECT_THRESHOLD.get(pid)
    threshold_ok = threshold_matches(runs, thr) if thr else None

    if pid == "nguong8":
        ok = bool(threshold_ok and data and data["overloaded_owners"] and wrote and "lan" in final_l + str(rec["written"]).lower() and "không có ai vượt" not in final_l)
    elif pid in ("nguong9", "para1"):
        ok = bool(threshold_ok and data is not None and data["overloaded_owners"] == [])
    elif pid == "para2":
        ok = bool(threshold_ok and data and any(o["owner"] == "Lan" for o in data["overloaded_owners"]))
    elif pid == "para3":
        ok = bool(threshold_ok and data is not None)
    elif pid == "carry2":
        ok = bool(threshold_ok and data is not None)
    elif pid in ("thieu", "carry"):
        ok = bool(not runs and not wrote and "ngưỡng" in final_l)
    elif pid == "khongco":
        ok = bool(any(s.get("exit_code") == 1 for s in runs) and not wrote)
    elif pid == "weekly":
        ok = bool(weekly_loaded and not csv_loaded and not runs and wrote)
    else:
        ok = None
    return {
        "ok": ok,
        "skill_first": skill_first,
        "skill_loaded": csv_loaded,
        "weekly_loaded": weekly_loaded,
        "ran_script": bool(runs),
        "threshold_arg_ok": threshold_ok,
        "wrote_report": bool(wrote),
        "names": [s["name"] for s in steps],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--skill", default=None, help="file SKILL.md thay thế (mặc định: giữ skill hiện có trong workspace)")
    parser.add_argument("--template", default=None, help="file report-template.md thay thế")
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--prompts", default="nguong8,nguong9,thieu,khongco")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    ids = [p for p in args.prompts.split(",") if p]
    jobs = [(pid, i) for pid in ids for i in range(args.n)]
    records = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one_run, args.stage, args.skill, pid, i, args.template): (pid, i) for pid, i in jobs}
        for fut in as_completed(futures):
            rec = fut.result()
            rec["variant"] = args.variant
            rec["eval"] = classify(rec) if "turn_steps" in rec else {"ok": None}
            records.append(rec)
    records.sort(key=lambda r: (ids.index(r["prompt_id"]), r["run"]))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"=== variant {args.variant} | model {next((r.get('model') for r in records if r.get('model')), '?')}")
    print(f"{'ca':8} {'n':>3} {'lỗi':>3} {'skill_first':>11} {'skill_loaded':>12} {'chạy script':>11} {'ngưỡng đúng':>11} {'ĐẠT':>5}")
    for pid in ids:
        rs = [r for r in records if r["prompt_id"] == pid]
        valid = [r for r in rs if "error" not in r]
        ev = [r["eval"] for r in valid]
        cnt = lambda key: sum(1 for e in ev if e.get(key))
        thr = sum(1 for e in ev if e.get("threshold_arg_ok")) if pid in EXPECT_THRESHOLD else "-"
        loaded = cnt("weekly_loaded") if pid == "weekly" else cnt("skill_loaded")
        print(f"{pid:8} {len(valid):>3} {len(rs) - len(valid):>3} {cnt('skill_first'):>11} {loaded:>12} {cnt('ran_script'):>11} {thr:>11} {cnt('ok'):>5}")
    errs = [r["error"] for r in records if "error" in r]
    if errs:
        print("lỗi:", sorted(set(errs))[:3])


if __name__ == "__main__":
    main()
