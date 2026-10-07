# Phân tích bài luyện tập D05 / 02: Kiểm tra quá tải theo người

- Model: `gpt-4o-mini` (ghi trong snapshot `model_request` của mọi trace). Ngày chạy: 2026-10-07 và 2026-10-08.
- Đường dẫn tính từ gốc repo (thư mục này là `block2/`). "Dòng N" của trace là dòng thứ N trong file JSONL, trùng với `sequence` của event.
- Công cụ hỗ trợ: coding assistant (Claude Code) được dùng để viết mã, chạy thử và soạn tài liệu này, theo cho phép của đề ("Được dùng coding assistant hỗ trợ viết mã nguồn").
- Agent được chạy theo ba cách. Cần biết cách nào khi đọc bằng chứng:

| Cách chạy | Mô tả | Dùng ở |
|---|---|---|
| Giao diện Streamlit | Người học chạy `app.py` trong WSL và gõ câu hỏi | Lần 1, lần 2 |
| `probe/scripts/run_like_app.py` | Chạy agent đúng đường chạy của `app.run_turn` (cùng `Observer`, `TraceWriter`, `build_agent`, system prompt, tools và model), không qua giao diện, trong bản sao workspace tạm | Lần 3, lần 4, các lượt Stage 03 bổ sung |
| `probe/scripts/probe_agent.py` | Chạy hàng loạt để đo tỉ lệ, **không** phải trace nộp bài | `probe/` |

Trace của lần 3, lần 4 và Stage 03 chạy không giao diện có cùng định dạng với trace của giao diện (cùng module `trace.py`).

## 1. Tóm tắt kết quả

| Hạng mục | Kết quả |
|---|---|
| Script, ngưỡng 8 | **Đạt.** Lan 9, Minh 3. Chỉ Lan quá tải. Loại dòng 5 `invalid_hours`, dòng 6 `duplicate_id`, dòng 7 `missing_owner` |
| Script, ngưỡng 9 | **Đạt.** Tổng giờ và dòng bị loại giữ nguyên. Không ai quá tải |
| Script, trường hợp đặc biệt (ngưỡng 0) | **Đạt.** Chỉ Minh 0 giờ, không ai quá tải. Dòng 2 `invalid_hours`, dòng 3 `duplicate_id`. Không cộng 5 giờ cho Lan |
| Script, thiếu hoặc sai `--max-hours` | **Đạt.** Lỗi ghi ra stderr, exit 2 |
| Script, file không tồn tại | **Đạt.** Lỗi ghi ra stderr, exit 1, stdout rỗng |
| Kiểm thử tự động | **Đạt.** Stage 04: 75/75 pass. Stage 03: 48/48 pass |
| Stage 03: tính tổng giờ bằng Python qua Bash | **Đạt sau khi diễn đạt lại câu hỏi.** Câu hỏi gốc: 0/12 lượt gọi bash. Câu hỏi nêu tên tool: 7/16 lượt. Lệnh pandas của agent cho `Lan 455`, `Minh 3abc` (mục 7) |
| Stage 04, agent, ngưỡng 8 | **Đạt** (lần 4). Lan 9, Minh 3, chỉ Lan quá tải, loại dòng 5, 6, 7 |
| Stage 04, agent, ngưỡng 9 | **Đạt** (lần 4). Không ai quá tải, tổng giờ và dòng bị loại không đổi |
| Stage 04, agent, thiếu ngưỡng | **Đạt** (lần 4). Nạp skill rồi hỏi ngưỡng, chưa kết luận |
| Stage 04, agent, file không tồn tại | **Đạt** (lần 4). Script exit 1, agent báo không phân tích được, không có tổng giờ hay báo cáo |
| Độ ổn định của bản chốt | 80/80 lượt đạt ở 4 câu của đề (20 lượt mỗi ca). 60/60 ở câu diễn đạt khác, `weekly-report`, ngưỡng nối tiếp (12 lượt mỗi ca) |
| Lịch sử | Lần 1 (skill đầu) và lần 2 (skill v2) **không đạt** ở nhiều chỗ, được ghi đầy đủ ở mục 8 |
| Giới hạn còn lại | Nhiều lượt trong cùng một cuộc trò chuyện, lượt sau không nêu ngưỡng: agent dùng lại hoặc tự đặt ngưỡng (mục 8.9) |

Trace nộp theo yêu cầu đề (bản chốt, lần 4):

| Trường hợp | Trace | Báo cáo agent tạo |
|---|---|---|
| Ngưỡng 8 | `block2/traces/lan4/stage-04-script-skill/20261008-011649_256be798_turn01_e35753ba.jsonl` | `block2/reports/lan4/nguong8/workload.md` |
| Ngưỡng 9 | `block2/traces/lan4/stage-04-script-skill/20261008-011703_9a36635a_turn01_3beb60ae.jsonl` | `block2/reports/lan4/nguong9/workload-9.md` |
| Thiếu ngưỡng | `block2/traces/lan4/stage-04-script-skill/20261008-011718_8e8add9a_turn01_9574f6a7.jsonl` | không có, agent hỏi ngưỡng |
| File không tồn tại | `block2/traces/lan4/stage-04-script-skill/20261008-011722_74163354_turn01_ccb25786.jsonl` | không có, script lỗi |
| Stage 03 (có gọi bash) | `block2/traces/stage03-chay-khong-giao-dien/20261008-010946_6602f226_turn01_e7c4031a.jsonl` | không có |

Câu trả lời cuối của agent (trace không lưu nội dung câu trả lời, chỉ lưu `answer_chars`) nằm ở `block2/outputs/tra-loi-agent-lan4.md` và `block2/outputs/tra-loi-agent-lan3-va-stage03.md`.

## 2. Môi trường chạy

Tool `bash` của lab gọi `bash -c` với PATH kiểu POSIX. Trên Windows, lệnh `bash` trỏ vào launcher WSL `C:\WINDOWS\system32\bash.EXE`. Mọi lệnh đều trả `exit_code: 1` với thông báo `Bash/Service/0x8007072c`, kể cả `echo hello`. README của lab cũng ghi rõ stage 03 và 04 "cần môi trường POSIX có bash. Trên Windows dùng WSL2".

Vì đề chỉ cho sửa skill và script, không sửa tool, stage 03 và 04 được chạy bên trong **WSL2 Ubuntu**:
- Cài `uv` 0.12.23 vào `~/.local/bin` của WSL.
- Tạo môi trường Linux riêng ở `~/.venvs/agent-tools-skills-lab` (biến `UV_PROJECT_ENVIRONMENT`), không đụng `.venv` Windows của stage 00 đến 02.
- Trong WSL, tool `bash` chạy đúng: `python` trỏ vào Python 3.12.3 của môi trường lab. Bộ test gốc pass toàn bộ trước khi sửa (stage 03: 48, stage 04: 61).

Lệnh chạy app (từ PowerShell):

```powershell
wsl -d Ubuntu -e bash -lc 'cd /mnt/d/Downloads/agent-tools-skills-lab/agent-tools-skills-lab/stage-04-script-skill && UV_PROJECT_ENVIRONMENT=$HOME/.venvs/agent-tools-skills-lab $HOME/.local/bin/uv run --frozen streamlit run app.py --server.port 8504'
```

## 3. Các thay đổi đã làm

Bản nộp của skill nằm ở `block2/skill/csv-quality/` (giống hệt `stage-04-script-skill/workspace/skills/csv-quality/` và `fixtures/skills/csv-quality/`, đã kiểm tra bằng `diff -r`).

| File | Thay đổi |
|---|---|
| `scripts/check_csv.py` | Thêm tham số bắt buộc `--max-hours`. Thêm các trường `max_hours`, `hours_by_owner`, `overloaded_owners`, `excluded_rows`. Giữ nguyên các trường kiểm tra chất lượng cũ |
| `SKILL.md` | Viết lại hai lần sau khi chạy agent (mục 8). Bản cuối: mô tả bám cách người dùng hỏi, quy trình bắt buộc 5 bước, quy tắc ngưỡng (có số giờ N thì N là ngưỡng, thiếu thì hỏi lại), cách đọc exit code 0/1/2, ý nghĩa JSON mới, cách viết báo cáo. Bỏ quy tắc cũ "không tính tổng giờ khi còn dữ liệu lỗi" |
| `references/report-template.md` | Thêm các mục ngưỡng, tổng giờ theo người, người vượt ngưỡng, dòng bị loại kèm mã và diễn giải lý do. Viết lại một lần để agent không chép hướng dẫn của template vào báo cáo (mục 8.6) |
| `stage-04-script-skill/{workspace,fixtures}/data/workload.csv`, `workload-edge.csv` | Dữ liệu đầu vào theo đề (bản sao ở `block2/data/`) |
| `stage-03-bash/{workspace,fixtures}/data/workload.csv` | Dữ liệu đầu vào cho stage 03 |
| `stage-04-script-skill/tests/test_check_csv.py` | Truyền `--max-hours` khi chạy script. Thêm test cho tổng giờ, ngưỡng, dòng bị loại, tham số sai và trường hợp đặc biệt (bản sao ở `block2/tests/`) |
| `stage-04-script-skill/tests/test_agent.py` | Lệnh giả lập trong luồng skill thêm `--max-hours 4`, kiểm tra thêm `overloaded_owners` |

Ràng buộc của đề:
- Không thêm tool, không sửa `agent.py`, `prompts.py` hay `tools/`.
- Không có ngưỡng 8 viết cố định: tìm số `8` đứng riêng trong `SKILL.md`, `report-template.md` và `check_csv.py` không có kết quả nào (chỉ có `utf-8`). Skill dùng chỗ trống `<N>` và mô tả "vượt N giờ".
- Không viết cố định kết quả: mọi con số tính từ CSV đầu vào. Test chạy cùng script trên nhiều bộ dữ liệu khác nhau (`tasks.csv`, `workload.csv`, `workload-edge.csv` và CSV tạm).
- Mô tả skill không chứa tên script hay tên template, nên system prompt ban đầu vẫn không lộ nội dung skill (test `test_initial_prompt_has_catalog_but_no_body_or_reference` pass).

## 4. Script tính như thế nào

Script dùng lại phần có sẵn: đọc CSV (`csv.reader`, `strict=True`, `utf-8-sig`), hàm `parse_hours` kiểm tra số giờ, vòng lặp phát hiện lỗi từng dòng (`issues`), và `InputError` cho lỗi đầu vào. Phần thêm vào bám theo vòng lặp đó:

| Quy tắc của đề | Cách làm trong `check_csv.py` |
|---|---|
| Bỏ khoảng trắng đầu/cuối ở `task_id`, `owner`, `hours` | Hàm `cell()` có sẵn đã `strip()` |
| Không gộp owner khác tên hoặc khác hoa/thường | Key của `totals` là owner nguyên văn sau `strip()` |
| ID chỉ giữ lần xuất hiện đầu tiên, kể cả khi lần đầu không hợp lệ | `first_seen` có sẵn ghi nhận lần đầu mà không xét dòng đó hợp lệ hay không. Lần sau có lỗi `duplicate_id` |
| Chỉ cộng dòng đủ số trường, có ID, có owner, hours hợp lệ | Mỗi dòng ghi lại vị trí bắt đầu trong `issues` (`row_start`). Dòng không phát sinh issue nào mới được cộng |
| Mỗi dòng bị loại xuất hiện một lần, kèm mọi lý do | `reasons` gom mọi loại issue của dòng, sắp theo `REASON_ORDER` cố định |
| Bỏ qua dòng trống | Giữ nguyên `continue` có sẵn |
| Quá tải khi lớn hơn ngưỡng, bằng thì không | `totals[owner] > max_hours` |
| Thống kê chất lượng cũ phân tích mọi dòng | Không đổi phần đếm `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_ids`, `issues` |
| `--max-hours` bắt buộc, số hữu hạn không âm | `argparse` `required=True` với `type=parse_max_hours`, hàm này dùng lại `parse_hours`. Sai thì argparse ghi lỗi ra stderr, exit 2 |
| Exit 0 khi phân tích được | Có dòng bị loại hay có người quá tải vẫn exit 0. Lỗi đầu vào giữ nguyên exit 1 |

Tổng giờ được cộng và so với ngưỡng bằng `Decimal`, không dùng `float`. Lý do: với `float`, `0.1 + 0.2 = 0.30000000000000004`, nên một người có tổng đúng bằng ngưỡng 0.3 sẽ bị tính nhầm là quá tải. Test `test_total_equal_to_decimal_threshold_is_not_overloaded` kiểm tra trường hợp này. Trong JSON, số nguyên in dạng `9` thay vì `9.0`.

## 5. Kết quả chạy script trực tiếp

Chạy từ thư mục `stage-04-script-skill`, trong WSL2. Lệnh, exit code và stderr của mọi lần chạy được lưu trong `block2/outputs/chay-truc-tiep.txt`.

### 5.1 Ngưỡng 8: `block2/outputs/json-max-8.json`

```
uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 8
```

Exit 0. Phần mới của JSON:

```json
"max_hours": 8,
"hours_by_owner": {"Lan": 9, "Minh": 3},
"overloaded_owners": [{"owner": "Lan", "total_hours": 9}],
"excluded_rows": [
  {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
  {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
  {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]}
]
```

Đối chiếu với CSV:
- Lan được cộng dòng 2 (T01, 4) và dòng 3 (T02, 5), tổng 9. Dòng 6 lặp T02 nên không cộng lần hai.
- Minh được cộng dòng 4 (T03, 3), tổng 3. Dòng 5 có hours `abc` nên bị loại.
- Dòng 7 (T05) không có owner nên bị loại.
- 9 > 8, nên chỉ Lan quá tải.

Các trường cũ vẫn giữ: `row_count` 6, `missing_owner_count` 1, `invalid_hours_count` 1, `duplicate_ids` `["T02"]`, `issues` 3 mục.

### 5.2 Ngưỡng 9: `block2/outputs/json-max-9.json`

Exit 0. `max_hours: 9`. `hours_by_owner` và `excluded_rows` giống hệt ngưỡng 8. `overloaded_owners: []`: Lan có 9 giờ, bằng ngưỡng, nên không quá tải.

### 5.3 Trường hợp đặc biệt: `block2/outputs/json-edge-max-0.json`

```
uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload-edge.csv --max-hours 0
```

Exit 0.

```json
"max_hours": 0,
"hours_by_owner": {"Minh": 0},
"overloaded_owners": [],
"excluded_rows": [
  {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
  {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]}
]
```

E01 lần đầu (dòng 2) có hours không hợp lệ, nhưng vẫn là lần xuất hiện đầu tiên. Vì vậy dòng 3 bị loại vì trùng ID, dù dòng 3 có hours hợp lệ. Lan không có dòng nào được cộng nên không có trong `hours_by_owner`. Minh có 0 giờ, bằng ngưỡng 0, nên không quá tải.

### 5.4 Lỗi tham số và lỗi đầu vào

| Lệnh (rút gọn) | Exit | stdout | stderr |
|---|---|---|---|
| `--input workspace/data/workload.csv` (thiếu `--max-hours`) | 2 | rỗng | `error: the following arguments are required: --max-hours` |
| `... --max-hours -1` | 2 | rỗng | `error: argument --max-hours: '-1' không phải số hữu hạn không âm.` |
| `... --max-hours abc` | 2 | rỗng | `error: argument --max-hours: 'abc' không phải số hữu hạn không âm.` |
| `--input workspace/data/khong-co.csv --max-hours 8` | 1 | rỗng | `ERROR: Không đọc được file workspace/data/khong-co.csv: No such file or directory` |

Script không sửa CSV đầu vào: mã SHA-256 của các file CSV lưu trong `block2/outputs/sha256-csv.txt`, và test `test_script_does_not_modify_input` so sánh nội dung trước và sau khi chạy.

## 6. Kiểm thử tự động

File `block2/tests/test_check_csv.py` (bản trong project: `stage-04-script-skill/tests/test_check_csv.py`), viết theo cách của project: chạy script bằng `subprocess` với Python hiện tại, đọc JSON từ stdout. Chạy trong WSL2 bằng `uv run pytest`. Kết quả lưu ở `block2/outputs/pytest.txt`.

| Test | Kiểm tra |
|---|---|
| `test_first_occurrence_with_invalid_hours_still_blocks_later_duplicate` | **Test đề yêu cầu.** Chạy `fixtures/data/workload-edge.csv` với ngưỡng 0: chỉ Minh 0 giờ, không ai quá tải, dòng 2 `invalid_hours`, dòng 3 `duplicate_id`, không cộng 5 giờ cho Lan |
| `test_workload_totals_and_overloaded_owners[8]`, `[9]` | `workload.csv` với ngưỡng 8 và 9, kèm thống kê chất lượng vẫn tính trên mọi dòng |
| `test_fixture_statistics` | `tasks.csv` có sẵn: trường cũ không đổi. Ngưỡng 4: An 5 quá tải, Lan 4 bằng ngưỡng nên không quá tải |
| `test_each_excluded_row_listed_once_with_all_reasons_in_order` | Một dòng có nhiều lỗi chỉ xuất hiện một lần, lý do đúng thứ tự `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours` |
| `test_values_are_trimmed_and_owner_case_is_kept` | Bỏ khoảng trắng; `Lan` và `lan` là hai người; dòng trống bị bỏ qua; ID có khoảng trắng vẫn bị coi là trùng |
| `test_total_equal_to_decimal_threshold_is_not_overloaded` | 0.1 + 0.2 bằng ngưỡng 0.3 không bị tính là quá tải |
| `test_missing_max_hours_exit_non_zero`, `test_invalid_max_hours_exit_non_zero[-1, abc, nan, inf, rỗng]` | Thiếu hoặc sai ngưỡng: exit khác 0, stdout rỗng, stderr nhắc `--max-hours` |
| Các test cũ (hours không hợp lệ, file không tồn tại, thiếu cột, lỗi parse, không sửa input) | Vẫn pass; test không sửa input chạy thêm trên `workload.csv` và `workload-edge.csv` |

| Bộ test | Kết quả |
|---|---|
| `stage-04-script-skill/tests/test_check_csv.py` | 26 pass |
| Toàn bộ `stage-04-script-skill` | 75 pass (trước khi sửa: 61) |
| Toàn bộ `stage-03-bash` | 48 pass |

## 7. Stage 03: tính tổng giờ bằng Python qua Bash

### 7.1 Câu hỏi gốc của đề: agent không gọi bash

Câu hỏi: "Dùng Python qua Bash để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng."

Kết quả: **0/12 lượt gọi bash**. Gồm 1 lượt trên giao diện, 3 lượt chính thức không giao diện và 8 lượt đo thử (`block2/probe/stage03-do-thu/P0-goc/`). Agent trả lời kiểu "Hiện tại, tôi không có công cụ để thực thi mã Python trực tiếp" rồi đưa mã mẫu để người dùng tự chạy.

Bằng chứng: lượt trên giao diện `block2/traces/lan1/stage-03-bash/20261007-235743_048c6d83_turn01_900e3842.jsonl`.
- Dòng 1 (`user_submitted`): `"tools": ["read_file", "write_file", "bash"]`. Tool `bash` đã được cấp.
- Dòng 2 (`model_request`): schema có 3 tool, system prompt 1733 ký tự mô tả `bash`.
- Dòng 3 (`model_response`): `"tool_calls_requested": []`. Dòng 4 (`run_completed`).

Agent nói sai về khả năng của chính nó: nó có tool `bash`. Ba lượt không giao diện cho kết quả tương tự (`block2/traces/stage03-chay-khong-giao-dien/20261008-0103*.jsonl`).

### 7.2 Câu hỏi nêu tên tool: agent chạy lệnh pandas và cho kết quả sai

Đề yêu cầu đọc lệnh và kết quả của tool, nên mình đo xem cách diễn đạt nào làm agent gọi bash (`probe/scripts/probe_stage03.py`, 8 lượt mỗi câu):

| Câu hỏi | Lượt gọi bash |
|---|---|
| Gốc của đề | 0/8 |
| "Hãy dùng tool bash để chạy lệnh Python tính tổng hours ..." | 0/8 |
| "Dùng tool bash chạy Python để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Sau khi chạy, cho biết cách xử lý dòng lỗi và task_id trùng." | 6/8 |
| Gốc của đề cộng "Bạn có tool bash, hãy gọi nó để chạy." | 4/8 |

Câu thứ ba được dùng cho các lượt chính thức: 1/8 lượt gọi bash. Gộp với đợt đo thử là **7/16**. Chênh lệch giữa 6/8 và 1/8 là ngẫu nhiên của model: câu hỏi, system prompt và tools của hai đợt giống hệt nhau (đã so sánh).

Bằng chứng (lượt có gọi bash): `block2/traces/stage03-chay-khong-giao-dien/20261008-010946_6602f226_turn01_e7c4031a.jsonl`
- Dòng 1 (`user_submitted`): tools có `bash`, catalog chỉ có `weekly-report`.
- Dòng 3 (`model_response`): model yêu cầu gọi `bash`.
- Dòng 4 (`tool_started`): lệnh `python -c "import pandas as pd; df = pd.read_csv('data/workload.csv'); total_hours = df.groupby('owner')['hours'].sum(); print(total_hours)"`.
- Dòng 5 (`tool_finished`): `exit_code: 0`, stdout `owner / Lan 455 / Minh 3abc / Name: hours, dtype: str`.
- Dòng 6 đến 8: agent trả lời (652 ký tự), trình bày `Lan 455`, `Minh 3abc` như kết quả, rồi khuyên kiểm tra lại cột `hours` và quyết định cách xử lý task_id trùng.

### 7.3 Những dòng nào được cộng vào tổng

Mình chạy lại đúng lệnh đó trên workspace của stage 03 (`block2/outputs/stage03-phan-tich-lenh-pandas.txt`):

| Dòng | task_id | owner | hours | Có nằm trong kết quả? | Lý do |
|---|---|---|---|---|---|
| 2 | T01 | Lan | 4 | Có | `"4"` |
| 3 | T02 | Lan | 5 | Có | `"5"` |
| 4 | T03 | Minh | 3 | Có | `"3"` |
| 5 | T04 | Minh | abc | Có, bị ghép chuỗi | `abc` không bị loại, cột trở thành chuỗi |
| 6 | T02 | Lan | 5 | **Có, cộng trùng** | task_id T02 lặp nhưng lệnh không loại |
| 7 | T05 | (trống) | 2 | Không | owner là NaN, `groupby` bỏ dòng này mà không báo |

- Vì có giá trị `abc`, pandas đọc cả cột `hours` thành chuỗi (`dtype: str`), và `sum()` **ghép chuỗi** thay vì cộng số: Lan là `"4" + "5" + "5"` = `455`, Minh là `"3" + "abc"` = `3abc`.
- Dòng bị cộng trùng là dòng 6 (T02 lặp). Chữ số thứ ba của `455` chính là giá trị của dòng này.
- Trên bản sao đã đổi `abc` thành `0`, cùng lệnh cho **Lan 14**, Minh 3. Đúng kịch bản của đề: tổng của Lan là 14 vì cộng cả dòng 6.
- Thêm `drop_duplicates(subset='task_id', keep='first')` trước khi cộng thì Lan là **9**, Minh 3 (cùng bản sao).
- Lệnh của agent không có đoạn nào loại task_id trùng, không kiểm tra `hours` hợp lệ, và không báo dòng nào bị bỏ.

Kết luận: lệnh viết nhanh cho kết quả sai mà không báo lỗi gì, và agent chuyển kết quả đó cho người dùng. Đây là lý do cần script ở stage 04: cùng dữ liệu, script cho Lan 9, Minh 3 và liệt kê rõ dòng 5, 6, 7 bị loại kèm lý do (mục 5.1).

## 8. Stage 04: agent dùng skill

Skill đi qua nhiều phiên bản. Bảng này cho thấy toàn bộ lịch sử, kể cả những lần không đạt:

| Vòng | Skill | Cách chạy | Kết quả |
|---|---|---|---|
| Lần 1 | v1 (`block2/skill-v1-truoc-khi-sua/`) | Giao diện, 1 lượt mỗi ca | Ngưỡng 8: không đạt. Ngưỡng 9: không đạt. Thiếu ngưỡng: đạt. File không tồn tại: đạt một phần |
| Lần 2 | v2 (viết lại `SKILL.md`) | Giao diện, 1 lượt (ngưỡng 8) | Không đạt, kết luận sai |
| Đo thử | v2 | `probe_agent.py`, 8 lượt mỗi ca | Ngưỡng 8: 1/8. Ngưỡng 9: 0/8. Thiếu ngưỡng: 7/8. File không tồn tại: 0/8 |
| Đo thử | Nhiều biến thể mô tả và quy trình | `probe_agent.py` | Xem `block2/probe/KET-QUA-DO-THU.md`. Chọn biến thể G2 |
| Lần 3 | v3 (mô tả B + quy trình G2) với template cũ | Không giao diện, 1 lượt mỗi ca | 4/4 đạt, nhưng báo cáo chép hướng dẫn của template |
| Lần 4 | v3 với template mới (**bản chốt**) | Không giao diện, 1 lượt mỗi ca | 4/4 đạt |
| Xác nhận | Bản chốt | `probe_agent.py`, 20 và 12 lượt mỗi ca | 80/80 và 60/60 |

### 8.1 Lần 1 (giao diện, skill v1)

Mỗi trường hợp là một cuộc trò chuyện mới. Trace ở `block2/traces/lan1/stage-04-script-skill/`.

| Trường hợp | Câu hỏi | Kết quả cần đạt | Kết quả thực tế | Đạt |
|---|---|---|---|---|
| Ngưỡng 8 | "Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md." | Lan 9, Minh 3, chỉ Lan quá tải, loại dòng 5, 6, 7 | Hỏi lại ngưỡng, không chạy script, không ghi báo cáo | **Không** |
| Ngưỡng 9 | "Kiểm tra data/workload.csv, người nào vượt 9 giờ? Ghi báo cáo vào output/workload-9.md." | Tổng giờ và dòng bị loại không đổi, không ai quá tải | Ghi báo cáo 1 câu "Không có ai vượt quá 9 giờ", không chạy script | **Không** (kết luận khớp, quy trình sai) |
| Thiếu ngưỡng | "Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải." | Hỏi ngưỡng trước khi kết luận | Nạp skill rồi hỏi ngưỡng | Có |
| File không tồn tại | "Kiểm tra data/khong-co.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/khong-co.md." | Báo không phân tích được, không đưa tổng giờ hay báo cáo | Báo file không tồn tại, không có tổng giờ hay báo cáo, nhưng không qua skill và script | Một phần |

Chi tiết:
- **Ngưỡng 8** (`20261008-000054_522ee2ff_turn01_6b653826.jsonl`): dòng 3 đến 5 `read_file("data/workload.csv")`, dòng 7 đến 9 `read_file("skills/csv-quality/SKILL.md")`, dòng 11, 12 trả lời "Bạn cần cung cấp ngưỡng giờ để kiểm tra ai vượt quá 8 giờ. Xin vui lòng xác nhận ngưỡng này ...". Agent đọc CSV trước khi nạp skill, rồi hiểu sai "vượt 8 giờ" là chưa có ngưỡng. Không `bash`, không `write_file`. Lần gửi đầu lúc 00:00:43 (`20261008-000043_1ae2b1d9_turn01_dccfe99f.jsonl`, dòng 3) bị lỗi mạng `OpenAIConnectionError`, câu hỏi được gửi lại.
- **Ngưỡng 9** (`20261008-000227_d9def8bd_turn01_d03933cf.jsonl`): dòng 3 đến 5 `read_file("data/workload.csv")`, dòng 7 đến 9 `write_file("output/workload-9.md", ...)` với nội dung 79 byte `Không có ai vượt quá 9 giờ.`. Không nạp skill, không `bash`. Báo cáo ở `block2/reports/lan1/workload-9.md`: một câu, không có ngưỡng, tổng giờ, dòng bị loại. Câu "Tôi đã kiểm tra" chỉ ứng với việc đọc file, không có phép tính hay script nào đứng sau.
- **Thiếu ngưỡng** (`20261008-000347_49359746_turn01_3061c8fa.jsonl`): dòng 3 đến 5 nạp skill, dòng 7, 8 hỏi ngưỡng. Đạt.
- **File không tồn tại** (`20261008-000441_c43b57cf_turn01_f0fdb8f7.jsonl`): dòng 3 đến 5 `read_file("data/khong-co.csv")` trả `FILE_NOT_FOUND`, dòng 7, 8 báo file không tồn tại. Không bịa số, nhưng không nạp skill và không chạy script nên không có phần "script ghi lỗi ra stderr" trong trace.

### 8.2 Nguyên nhân của lần 1

- Ở 3 trong 4 trường hợp, model call đầu tiên là `read_file` trên CSV, trước khi nạp skill. System prompt dặn nạp `SKILL.md` trước khi làm khi task khớp mô tả.
- Không trường hợp nào chạy `bash`, nên lần 1 không có JSON của script trong trace nào.
- Ở ngưỡng 8, dù đã nạp skill, agent coi như chưa có ngưỡng. Ở ngưỡng 9, agent ghi báo cáo mà không dựa vào script.
- Model `gpt-4o-mini` không cố định tham số sinh, nên hành vi có thể khác nhau giữa các lần chạy với cùng đầu vào.

### 8.3 Lần 2 (giao diện, skill v2): vẫn sai

Sau lần 1, `SKILL.md` được viết lại: đưa điều kiện kích hoạt lên đầu mô tả, thêm mục "Quy trình bắt buộc" 5 bước, nói rõ "có số giờ N thì N chính là ngưỡng".

Ngưỡng 8, 1 lượt trên giao diện (`block2/traces/lan2/20261008-001847_88d42461_turn01_9d2f8f51.jsonl`):
- Dòng 2: system prompt 2180 ký tự, catalog đã hiện mô tả mới.
- Dòng 3 đến 5: `read_file("data/workload.csv")`. Vẫn đọc thẳng CSV.
- Dòng 7 đến 9: `write_file("output/workload.md", ...)` với nội dung `Không có ai vượt quá 8 giờ làm việc.` (76 byte). Báo cáo ở `block2/reports/lan2/workload.md`.
- Dòng 11, 12: trả lời "Báo cáo đã được ghi vào file output/workload.md, xác nhận không có ai vượt quá 8 giờ làm việc."

Kết luận này **sai**: Lan có 9 giờ, lớn hơn ngưỡng 8 (`block2/outputs/json-max-8.json`). Agent đã đọc `T01,Lan,4` và `T02,Lan,5`, không dùng script, ghi sai vào file báo cáo rồi "xác nhận". Đây đúng là rủi ro của việc để model tự tính thay vì dùng script.

### 8.4 Đo hành vi theo phiên bản skill

Để tìm cách viết skill cho agent dùng đúng, mình chạy agent hàng loạt với từng phiên bản (`probe/scripts/probe_agent.py`: cùng agent, system prompt, tools và model với app, mỗi lượt là một cuộc trò chuyện mới trong workspace tạm). Kết quả đầy đủ ở `block2/probe/KET-QUA-DO-THU.md`, dữ liệu từng lượt ở `block2/probe/ket-qua/`.

Mốc so sánh là skill v2 đang dùng ở lần 2: ngưỡng 8 đạt 1/8, ngưỡng 9 đạt 0/8, thiếu ngưỡng 7/8, file không tồn tại 0/8. Nghĩa là lần 2 trên giao diện không phải xui: v2 thật sự yếu.

Các phát hiện chính:
- **Mô tả là phần quyết định agent có nạp skill hay không**, vì đó là phần duy nhất agent luôn nhìn thấy. Mô tả bám sát cách người dùng hỏi và có câu "Luôn gọi read_file đọc SKILL.md này trước khi gọi read_file hay bash với file CSV" (biến thể B) đạt 100% ở cả 4 ca. Mô tả ngắn chỉ nêu từ khoá (C) hầu như không tác dụng (0/8 ở ngưỡng 8, 9 và file không tồn tại).
- **Không nên đưa quy tắc ngưỡng vào mô tả.** Thêm câu về ngưỡng vào mô tả (B2, B3) làm các ca của đề kém đi (ngưỡng 8 chỉ đạt 2/8 và 0/8), vì agent hỏi lại ngưỡng dù đã có. Quy tắc ngưỡng nằm ở thân skill.
- **Agent gần như không bao giờ đọc template** khi chỉ được dặn ở bước cuối quy trình: 0/24 lượt. Dặn đọc template **cùng lượt** với lệnh chạy script, và đặt điều kiện "chỉ `write_file` sau khi đã nhận template" làm tỉ lệ đọc template lên 100% (biến thể F3, G2).
- Một số thay đổi nhỏ trong quy trình làm agent hỏi lại ngưỡng sai ở câu diễn đạt khác "Ai làm quá 10 giờ trong data/workload.csv?" (E1 4/8, F1 6/10, F3 7/12, G1 3/12). Biến thể G2 thêm câu "vượt N giờ", "quá N giờ" là đã có ngưỡng và giữ được 12/12.
- Đã thử nhiều biến thể trên mẫu nhỏ nên dễ chọn trúng kết quả may mắn. Vì vậy bản chọn được đo lại bằng lượt chạy mới trên chính file đã áp dụng (mục 8.8).

### 8.5 Skill cuối (v3)

Giữ nguyên: ràng buộc của đề, các quy tắc ngưỡng, ý nghĩa JSON, cách đọc exit code. Thay đổi chính so với v2, chỉ ở `SKILL.md`:

| Phần | Nội dung |
|---|---|
| Mô tả (agent luôn thấy) | "Kiểm tra file CSV công việc (cột task_id, owner, hours), người nào vượt N giờ, ai quá tải, tổng giờ theo người, rồi ghi báo cáo vào output/. Dùng cho mọi yêu cầu kiểm tra hoặc phân tích file CSV công việc, kể cả khi file có thể không tồn tại. Luôn gọi read_file đọc SKILL.md này trước khi gọi read_file hay bash với file CSV." |
| Bước 1 | Xác định ngưỡng. Yêu cầu có số giờ như "vượt N giờ", "quá N giờ" thì đã có ngưỡng N, đi tiếp. Chưa có số giờ nào thì hỏi người dùng rồi dừng |
| Bước 2 | Gọi **đồng thời**, trong cùng một lượt, cả hai tool: `bash` chạy script và `read_file` đọc template. Không dùng `read_file` để đọc CSV rồi tự tính |
| Bước 3 | Kiểm tra `exit_code`. Lỗi thực thi thì dừng, không ghi báo cáo |
| Bước 4 | Chỉ gọi `write_file` sau khi đã nhận nội dung template, báo cáo theo đúng các mục của template |
| Bước 5 | Trả lời: ngưỡng đã dùng, tổng giờ theo người, ai quá tải, dòng bị loại, đường dẫn báo cáo |

Kiểm tra offline: catalog đọc được cả hai skill không có cảnh báo; mô tả không chứa tên script hay `report-template.md`; không có số `8` đứng riêng; `fixtures/` đồng bộ; test stage 04 pass 75/75, stage 03 pass 48/48.

### 8.6 Lần 3 và việc sửa template

Lần 3 (v3 với template cũ, `block2/traces/lan3/stage-04-script-skill/`, 1 lượt mỗi ca): cả 4 ca đạt. Ngưỡng 8 và 9 có đủ chuỗi nạp skill, `bash`, đọc template, `write_file`. Thiếu ngưỡng hỏi ngưỡng. File không tồn tại báo lỗi.

Nhưng báo cáo chép nguyên các dòng hướng dẫn của template. Đo trên 40 báo cáo (`xacnhan-G2-de`): dòng hướng dẫn "Nếu `excluded_rows` rỗng, ghi: ..." xuất hiện ở 33/40 báo cáo, phần chú giải mã lý do ở 33/40, và câu hướng dẫn "Nêu rằng ..." ở mục Đánh giá ở 40/40. Số liệu vẫn đúng, chỉ là trình bày chưa sạch.

Cách sửa (chỉ `report-template.md`): chuyển hướng dẫn có điều kiện sang dạng `{...}` mà agent luôn thay thế, bỏ phần chú giải mã lý do (đã có ở `SKILL.md`). Kết quả đo: 0/24 báo cáo còn sót hướng dẫn, vẫn đọc template 24/24 và đủ 3 mã lý do 24/24. Template mới áp dụng cho bản chốt.

### 8.7 Lần 4 (bản chốt): từng trường hợp

Skill cuối và template mới, mỗi ca một cuộc trò chuyện mới và đúng một lượt chính thức, không chọn lọc kết quả. Trace ở `block2/traces/lan4/stage-04-script-skill/`.

#### Ngưỡng 8: đạt

Trace `20261008-011649_256be798_turn01_e35753ba.jsonl`:
- Dòng 2 (`model_request`): system prompt 2193 ký tự, catalog có `csv-quality` và `weekly-report`.
- Dòng 3 đến 5: `read_file("skills/csv-quality/SKILL.md")`, `ok: true`. Nội dung skill vào history.
- Dòng 7: model yêu cầu đồng thời `bash` và `read_file`. Dòng 8: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8`. Dòng 9, 10: `read_file("skills/csv-quality/references/report-template.md")`, `ok: true`. Nội dung reference vào history.
- Dòng 11: `bash` trả `exit_code: 0`, stdout là JSON của script.
- Dòng 13 đến 15: `write_file("output/workload.md")`, 2079 byte.
- Dòng 17, 18: trả lời. 4 tool call.

Câu trả lời: "Báo cáo đã được ghi vào file `output/workload.md`. Ngưỡng sử dụng: 8 giờ. Người vượt ngưỡng: Lan (9 giờ)."

Báo cáo `block2/reports/lan4/nguong8/workload.md` theo đúng template: ngưỡng 8 giờ, bảng tổng giờ (Lan 9 "Có", Minh 3 "Không"), người vượt ngưỡng Lan 9 giờ, bảng dòng bị loại (dòng 5 `T04` `invalid_hours`, dòng 6 `T02` `duplicate_id`, dòng 7 `T05` `missing_owner`), thống kê chất lượng toàn bộ dòng (6 dòng, 1 thiếu owner, 1 hours không hợp lệ, 1 task_id lặp), chi tiết lỗi, đánh giá, khuyến nghị.

#### Ngưỡng 9: đạt

Trace `20261008-011703_9a36635a_turn01_3beb60ae.jsonl`: cùng chuỗi như ngưỡng 8, dòng 8 chạy `--max-hours 9`, dòng 14 `write_file("output/workload-9.md")` 2045 byte. Câu trả lời: ngưỡng 9 giờ, người vượt ngưỡng "Không ai", tổng giờ Lan 9, Minh 3. Báo cáo `block2/reports/lan4/nguong9/workload-9.md`: Lan 9 "Không", Minh 3 "Không", "Không ai vượt ngưỡng 9 giờ.", cùng các dòng bị loại 5, 6, 7 như ngưỡng 8. Lan đúng 9 giờ, bằng ngưỡng nên không quá tải.

#### Thiếu ngưỡng: đạt

Trace `20261008-011718_8e8add9a_turn01_9574f6a7.jsonl`:
- Dòng 3 đến 5: `read_file("skills/csv-quality/SKILL.md")`, `ok: true`.
- Dòng 7, 8: trả lời "Cần biết ngưỡng giờ để tiếp tục. Bạn vui lòng cho biết ngưỡng giờ tối đa mà bạn muốn xác định cho việc quá tải?". 2 model call, 1 tool call.
- Không đọc CSV, không `bash`, không `write_file`. Chưa nêu tổng giờ hay người quá tải.

#### File không tồn tại: đạt

Trace `20261008-011722_74163354_turn01_ccb25786.jsonl`:
- Dòng 3 đến 5: nạp skill.
- Dòng 7: model yêu cầu đồng thời `bash` và `read_file` template. Dòng 8: `python skills/csv-quality/scripts/check_csv.py --input data/khong-co.csv --max-hours 8`.
- Dòng 11 (`tool_finished`): `exit_code: 1`, stdout rỗng, stderr `ERROR: Không đọc được file data/khong-co.csv: No such file or directory`.
- Dòng 13, 14: trả lời "Lệnh kiểm tra file `data/khong-co.csv` không thành công do file này không tồn tại ...".
- Không có `write_file`, không có tổng giờ hay báo cáo.

Agent có đọc template song song với lệnh như skill dặn, dù cuối cùng không ghi báo cáo. Việc đó vô hại, chỉ tốn một lần đọc file.

### 8.8 Độ ổn định của bản chốt

Mỗi trường hợp chạy lặp trên chính file skill đã áp dụng, mỗi lượt là một cuộc trò chuyện mới (`block2/probe/ket-qua/xacnhan-final-de.jsonl`, `xacnhan-final-mo-rong.jsonl`):

| Ca | Lượt đạt |
|---|---|
| Ngưỡng 8 | 20/20 |
| Ngưỡng 9 | 20/20 |
| Thiếu ngưỡng | 20/20 |
| File không tồn tại | 20/20 |
| "Ai làm quá 10 giờ trong data/workload.csv?" | 12/12 |
| "... tổng giờ của từng người ..., ngưỡng cảnh báo là 7.5 giờ." (số thập phân) | 12/12 |
| "Rà soát file data/workload-edge.csv, ai vượt 4 giờ ..." | 12/12 |
| "Tạo báo cáo tuần từ data/weekly_notes.md ..." (skill `weekly-report` phải được nạp, `csv-quality` không được chiếm chỗ) | 12/12 |
| Nhiều lượt: lượt 1 ngưỡng 8, lượt 2 "Còn nếu ngưỡng là 10 giờ thì sao?" | 12/12 |

Thêm: ở ngưỡng 8 và 9, cả 40/40 lượt đều nạp skill đầu tiên, chạy script với đúng ngưỡng, đọc template, và ghi báo cáo có đủ ngưỡng, tổng giờ theo người, người vượt ngưỡng và 3 mã lý do `invalid_hours`, `duplicate_id`, `missing_owner`. Không báo cáo nào còn sót hướng dẫn của template. Ở ca file không tồn tại, 20/20 lượt chạy script và nhận `exit_code: 1`, không lượt nào ghi báo cáo. Ở ca thiếu ngưỡng, 20/20 lượt không chạy script và không ghi báo cáo.

### 8.9 Giới hạn còn lại

Kịch bản nhiều lượt trong **cùng một cuộc trò chuyện**, lượt sau không nêu ngưỡng ("Tính tổng giờ theo người ... và xác định người quá tải" sau khi đã hỏi ngưỡng 8), **chưa được giải quyết** bằng cách chỉnh skill. Với G2: 0/12 lượt hỏi lại ngưỡng. Agent dùng lại ngưỡng 8 của lượt trước (6/12) hoặc tự đặt `--max-hours 0` (6/12) rồi trả lời. Đã thử các cách siết quy tắc trong cả mô tả và thân skill (B2, B3, E1, E2, E3) mà không có cách nào ổn định, và vài cách làm các ca của đề kém đi. Ca "thiếu ngưỡng" của đề mở cuộc trò chuyện mới nên không bị ảnh hưởng, nhưng đây là điểm yếu cần biết: agent chưa tôn trọng chắc chắn quy tắc "không dùng ngưỡng từ cuộc trò chuyện cũ" khi cuộc trò chuyện vẫn tiếp diễn.

## 9. Câu hỏi cuối bài

**Phần nào do script tính, phần nào do model diễn giải? Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu thông tin gì?**

### Phần do script tính

Script làm mọi việc cần chính xác và lặp lại được:
- Đọc CSV, bỏ khoảng trắng đầu/cuối, bỏ dòng trống.
- Kiểm tra từng dòng: đúng số trường, có task_id, có owner, hours là số hữu hạn không âm. Gán mã lý do theo thứ tự cố định.
- Giữ lần xuất hiện đầu tiên của mỗi task_id, kể cả khi lần đó không hợp lệ, và loại các lần sau.
- Cộng giờ theo owner (không gộp tên khác hoa/thường), bằng `Decimal` để tổng bằng đúng ngưỡng không bị sai số số thực.
- So sánh với ngưỡng: lớn hơn thì quá tải, bằng thì không.
- Sắp xếp và xuất JSON, đặt exit code.

Cùng đầu vào cho cùng đầu ra: ngưỡng 8 và 9 trên `workload.csv` cho tổng giờ và dòng bị loại giống hệt nhau, chỉ `overloaded_owners` đổi (`block2/outputs/json-max-8.json`, `json-max-9.json`). Các quy tắc này có test tự động, không phụ thuộc model. Stage 03 cho thấy việc tính toán này không thể giao cho model viết nhanh: lệnh pandas của agent cho `Lan 455`, `Minh 3abc` mà không báo lỗi (mục 7).

### Phần do model diễn giải

- Nhận ra yêu cầu khớp skill và nạp skill. Phần này không chắc chắn: ở skill v2, ba ca có đường dẫn file trong câu hỏi nạp skill chỉ 1/24 lượt; ở bản chốt là 80/80.
- Lấy ngưỡng từ câu tiếng Việt tự nhiên ("vượt 8 giờ" nghĩa là ngưỡng 8, "quá 10 giờ", "ngưỡng cảnh báo là 7.5 giờ") và quyết định hỏi lại hay chạy. Lần 1, ca ngưỡng 8 hỏi lại sai.
- Ghép đúng lệnh và tham số, đọc `exit_code` và `stderr`, phân biệt lỗi dữ liệu (exit 0) với lỗi thực thi (exit khác 0).
- Viết báo cáo tiếng Việt theo mẫu: chuyển JSON thành bảng và câu, đưa mã lý do và diễn giải, đề xuất cách sửa, tóm tắt cho người dùng.

Model không nên tự cộng hay tự so sánh với ngưỡng. Khi nó bỏ qua script (ngưỡng 9 lần 1, ngưỡng 8 lần 2), câu trả lời chỉ là phát biểu của model: lần 1 trùng đáp án nhưng không có phép tính nào đứng sau, lần 2 sai và được ghi vào file báo cáo.

### Nếu chỉ sửa script, không cập nhật skill và reference

Đã chạy thử đúng lệnh trong `SKILL.md` gốc của bài mẫu (không có `--max-hours`) với script mới: **exit 2, stdout rỗng**, stderr `error: the following arguments are required: --max-hours` (`block2/outputs/skill-cu-voi-script-moi.txt`). Từ đó và từ các lần chạy agent, các hậu quả:

1. **Lệnh trong skill chạy hỏng.** Skill cũ không có `--max-hours`, nên mọi lần chạy theo skill đều thất bại. Skill cũ chỉ giải thích exit 0 và exit 1, không có exit 2, nên agent không biết xử lý. Nó có thể báo lỗi mơ hồ hoặc tự thêm một ngưỡng.
2. **Ngưỡng bị bịa.** Skill cũ không nói phải hỏi ngưỡng khi thiếu và không cấm tự chọn. Ngay cả khi skill đã có quy tắc đó, ở kịch bản nhiều lượt agent vẫn tự đặt `--max-hours 0` ở 6/12 lượt (mục 8.9). Khi không có quy tắc nào thì không có gì ngăn việc này. `overloaded_owners` vẫn là JSON thật nhưng trả lời cho một câu hỏi người dùng chưa đặt ra.
3. **Mất thông tin do quy tắc cũ.** Skill cũ có dòng "Không tính tổng giờ hay KPI khi còn dữ liệu lỗi; ghi rõ lý do" và template cũ có mục "Dữ liệu có dùng được để tính tổng giờ/KPI chưa? Nếu còn lỗi: chưa". Script mới đã tính được tổng giờ trên các dòng hợp lệ, nhưng báo cáo theo hướng dẫn cũ sẽ từ chối nêu tổng giờ và kết luận "chưa dùng được" cho `workload.csv`, ngược với JSON.
4. **Báo cáo thiếu các mục chính của bài.** Template cũ không có chỗ cho ngưỡng, tổng giờ theo người, người vượt ngưỡng và dòng bị loại kèm lý do. Các trường này có trong JSON nhưng không có chỉ dẫn nào buộc đưa vào báo cáo. Lần 1 cho thấy hậu quả khi agent không có khung báo cáo: báo cáo ngưỡng 9 chỉ một câu "Không có ai vượt quá 9 giờ", không có ngưỡng, tổng giờ hay dòng bị loại (`block2/reports/lan1/workload-9.md`). Với template mới và quy trình đọc template, 40/40 báo cáo của bản chốt có đủ các mục.
5. **Dễ diễn giải sai.** Skill cũ không giải thích `excluded_rows`, các mã lý do, quy tắc "lần xuất hiện đầu tiên của ID" và "bằng ngưỡng không phải quá tải". Agent có thể không đưa các dòng bị loại vào báo cáo, hoặc giải thích sai lý do một dòng bị loại.

Lần chạy này còn cho thấy một điều nữa: **cập nhật nội dung chưa đủ, cách nối skill và reference vào quy trình mới quyết định agent có dùng chúng hay không.** Skill v1 có đủ thông tin nhưng 3/4 trường hợp agent không nạp nó trước. Template có đủ các mục nhưng khi chỉ được dặn ở bước cuối, agent đọc nó 0/24 lượt; khi được dặn đọc cùng lượt với lệnh chạy script, agent đọc 100%. Vì vậy sửa script thì phải sửa cả skill (cách gọi, cách xử lý lỗi, ý nghĩa JSON), reference (cấu trúc báo cáo), và kiểm tra lại bằng trace.

## 10. Danh mục nộp bài

| Yêu cầu của đề | Vị trí |
|---|---|
| Skill `csv-quality` đã cập nhật (script, hướng dẫn, reference) | `block2/skill/csv-quality/` |
| Bản đồng bộ trong fixtures | `stage-04-script-skill/fixtures/skills/csv-quality/` (giống hệt `block2/skill/csv-quality/`) |
| CSV đầu vào | `block2/data/workload.csv`, `block2/data/workload-edge.csv` |
| Kiểm thử tự động cho ID đầu tiên có hours không hợp lệ | `block2/tests/test_check_csv.py::test_first_occurrence_with_invalid_hours_still_blocks_later_duplicate` |
| JSON chạy trực tiếp với ngưỡng 8 và 9, kết quả trường hợp đặc biệt | `block2/outputs/json-max-8.json`, `json-max-9.json`, `json-edge-max-0.json` |
| Báo cáo agent tạo | `block2/reports/lan4/` (bản chốt). Các lần trước: `lan1/`, `lan2/`, `lan3/` |
| Trace ngưỡng 8, ngưỡng 9, thiếu ngưỡng, file không tồn tại | `block2/traces/lan4/stage-04-script-skill/` (bản chốt). Các lần trước: `lan1/`, `lan2/`, `lan3/` |
| Trace Stage 03 | `block2/traces/lan1/stage-03-bash/` (giao diện), `block2/traces/stage03-chay-khong-giao-dien/` |
| analysis.md | `block2/analysis.md` |
| Bằng chứng bổ sung | `block2/outputs/` (kết quả chạy trực tiếp, test, phân tích lệnh Stage 03, câu trả lời của agent), `block2/skill-v1-truoc-khi-sua/`, `block2/probe/` |

Không có `.env` hay API key trong thư mục này. Ảnh chụp giao diện không được đưa vào.

## 11. Hạn chế và những điều cần biết khi đọc

- Lần 3, lần 4 và các lượt Stage 03 bổ sung được chạy bằng script `run_like_app.py`, không qua giao diện Streamlit, bằng cấu hình model của người học. Script dùng đúng đường chạy của `app.run_turn`, nên trace có cùng định dạng và nội dung. Lần 1 và lần 2 chạy trên giao diện.
- Câu hỏi Stage 03 phải diễn đạt lại để nêu tên tool bash. Câu hỏi gốc cho 0/12 lượt gọi bash và vẫn nằm trong các trace. Câu diễn đạt lại chỉ cho 7/16 lượt gọi bash.
- Các phép đo dùng mẫu nhỏ (8 đến 20 lượt mỗi ca) và model không cố định tham số sinh. Kết quả 80/80 và 60/60 nghĩa là bản chốt rất ổn định trên các câu đã thử, không phải bảo đảm tuyệt đối cho mọi câu hỏi.
- Skill được chỉnh dựa trên hành vi của `gpt-4o-mini`. Model khác có thể không cần các chỉ dẫn mạnh này. Các biến thể và dữ liệu đo ở `block2/probe/`.
- Giới hạn về kịch bản nhiều lượt: mục 8.9.
- Tool `bash` của lab không chạy được trên Windows; mọi lần chạy stage 03 và 04 dùng WSL2 (mục 2).
