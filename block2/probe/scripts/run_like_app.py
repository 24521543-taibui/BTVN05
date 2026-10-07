"""Chạy agent của một stage theo đúng đường chạy của app (app.run_turn) nhưng không cần giao diện.

Dùng cùng Observer, TraceWriter, build_agent, build_model, cùng cách stream và cùng system prompt.
Khác app ở hai điểm: không có Streamlit, và workspace là bản sao tạm (kết quả ghi vào output/ của bản sao
được chép sang thư mục báo cáo), nên không làm thay đổi workspace của project.

    python run_like_app.py --stage <thư mục stage> --case <tên ca> --traces-out <dir> --reports-out <dir> --answers-out <file.md>
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

CASES = {
    "nguong8": "Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md.",
    "nguong9": "Kiểm tra data/workload.csv, người nào vượt 9 giờ? Ghi báo cáo vào output/workload-9.md.",
    "thieu": "Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải.",
    "khongco": "Kiểm tra data/khong-co.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/khong-co.md.",
    "stage03": "Dùng Python qua Bash để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng.",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--case", required=True, choices=sorted(CASES))
    parser.add_argument("--traces-out", required=True)
    parser.add_argument("--reports-out", required=True)
    parser.add_argument("--answers-out", required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--text", default=None, help="thay câu hỏi mặc định của ca (ghi rõ trong tài liệu khi dùng)")
    args = parser.parse_args()

    stage = Path(args.stage).resolve()
    sys.path.insert(0, str(stage))
    import paths
    from langchain_core.messages import AIMessage, HumanMessage

    tmp = Path(tempfile.mkdtemp(prefix="b2run-"))
    try:
        workspace = tmp / "workspace"
        shutil.copytree(stage / "workspace", workspace)
        shutil.rmtree(workspace / "output", ignore_errors=True)  # không mang file báo cáo của các lần chạy trước
        (workspace / "output").mkdir()
        paths.WORKSPACE_DIR = workspace

        from agent import build_agent, build_model, capabilities
        from config import PROJECT_NAME, RECURSION_LIMIT, load_settings
        from observer import Observer
        from trace import TraceWriter

        settings, missing = load_settings()
        if settings is None:
            raise SystemExit(f"Thiếu cấu hình: {missing}")

        text = args.text or CASES[args.case]
        observer = Observer(conversation_id=uuid.uuid4().hex)
        run_id = uuid.uuid4().hex
        observer.start_turn(run_id)
        writer = TraceWriter(Path(args.traces_out), PROJECT_NAME, observer.conversation_id, run_id, observer.chat_turn)
        working = [HumanMessage(content=text)]

        def emit(event_type: str, data: dict | None = None) -> None:
            writer.write(observer.record(event_type, data))

        caps = capabilities()
        emit("user_submitted", {"text": text, "tools": caps["tools"], "skills": caps["skills"]})
        observer.sync_messages(working)

        answer, error = "", None
        try:
            agent = build_agent(build_model(settings))
            for mode, chunk in agent.stream({"messages": working}, config={"recursion_limit": RECURSION_LIMIT}, stream_mode=["updates", "custom"]):
                if mode == "custom" and isinstance(chunk, dict) and chunk.get("observer"):
                    emit(chunk["event"], chunk["data"])
                elif mode == "updates" and isinstance(chunk, dict):
                    for update in chunk.values():
                        if isinstance(update, dict) and update.get("messages"):
                            working.extend(update["messages"])
                            observer.sync_messages(working)
            answer = next((m.text for m in reversed(working[1:]) if isinstance(m, AIMessage) and not m.tool_calls), "")
            emit("run_completed", {"answer_chars": len(answer)})
        except Exception as exc:  # giống app: ghi run_failed, không bịa kết quả
            error = f"{type(exc).__name__}: {str(exc)[:300]}"
            emit("run_failed", {"error": error})

        out_dir = Path(args.reports_out)
        out_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        output = workspace / "output"
        if output.is_dir():
            for f in sorted(output.iterdir()):
                if f.is_file():
                    shutil.copyfile(f, out_dir / f.name)
                    copied.append(f.name)

        with open(args.answers_out, "a", encoding="utf-8") as fh:
            fh.write(f"## {args.label or args.case}\n\n")
            fh.write(f"- Trace: `{writer.path.name}`\n")
            fh.write(f"- Câu hỏi: {text}\n")
            fh.write(f"- File báo cáo agent ghi: {', '.join(copied) if copied else '(không có)'}\n")
            if error:
                fh.write(f"- Lỗi: {error}\n")
            fh.write(f"\nCâu trả lời cuối của agent:\n\n```\n{answer}\n```\n\n")
        print(f"{args.label or args.case}: trace={writer.path.name} báo cáo={copied or '-'} lỗi={error or '-'}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
