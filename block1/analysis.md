# Phân tích bài luyện tập D05 / 01: Tra cứu chính sách đúng phiên bản

- Model: `gpt-4o-mini` (ghi trong snapshot `model_request` của mọi trace).
- Ngày chạy: 2026-10-07.
- Đường dẫn trace tính từ thư mục `agent-tools-skills-lab/`. "Dòng N" là dòng thứ N của file trace JSONL, trùng với `sequence` của event.
- Ảnh chụp màn hình nằm trong thư mục `analysis-images/`.

## 1. Tóm tắt kết quả

| Hạng mục | Kết quả |
|---|---|
| Kiểm tra tool trực tiếp | **Đạt.** Thư mục hợp lệ trả danh sách. Đường dẫn là file, không tồn tại, vượt workspace đều trả lỗi rõ ràng |
| Trường hợp A | **Đạt.** Chính sách cũ, 8 ngày, không đủ điều kiện. Sai lệch nhỏ: vẫn ghi phí 10% dù không đủ điều kiện |
| Trường hợp B | **Đạt.** Chính sách mới, 10 ngày, đủ điều kiện, không phí |
| Đổi tên file, chạy lại B | **Đạt.** Tìm được `refund-b.md`, kết luận không đổi |
| Đổi tên file, chạy lại A | **Không đạt.** Tìm và đọc đúng file mới, chọn đúng chính sách cũ, nhưng kết luận đổi thành "đủ điều kiện, không phí" |
| Thiếu thông tin | **Đạt.** Hỏi lại trạng thái kích hoạt, chưa kết luận, không tự giả định "chưa kích hoạt" |

Trace nộp theo yêu cầu đề:

| Trường hợp | Trace |
|---|---|
| A | `stage-02-skills/traces/20261007-223009_0f11ef7e_turn01_f5569244.jsonl` |
| B sau khi đổi tên file | `stage-02-skills/traces/20261007-224003_043bb805_turn01_26e282ed.jsonl` |
| Thiếu thông tin | `stage-02-skills/traces/20261007-224231_2f5d85d0_turn01_c0e60327.jsonl` |

Các trace khác có dùng làm bằng chứng được dẫn ở từng mục bên dưới.

## 2. Những gì đã thay đổi

| Vị trí | Thay đổi |
|---|---|
| `stage-01-files/tools/files.py`, `stage-02-skills/tools/files.py` | Thêm hàm `_list(workspace, path)` và tool `list_files(path)` |
| `tools/__init__.py`, `agent.py` (cả hai stage) | Đăng ký tool: `TOOLS = [read_file, write_file, list_files]` |
| `tests/test_agent.py`, `tests/test_app.py` (cả hai stage) | Cập nhật các khẳng định cũ "chỉ có 2 tool" thành 3 tool |
| `stage-01-files/workspace/data/policies/` (và `fixtures/data/policies/`) | `policy-before-oct.md`, `policy-from-oct.md`, nội dung đúng đề |
| `stage-02-skills/workspace/data/policies/` | Hai file trên, sau đó đổi tên thành `refund-a.md`, `refund-b.md`, giữ nguyên nội dung |
| `stage-02-skills/workspace/skills/refund-policy/` (và `fixtures/skills/refund-policy/`) | `SKILL.md`, `references/answer-template.md` |

Không sửa `prompts.py`. Đã kiểm tra `prompts.py`, `agent.py` và `tools/` của cả hai stage: không có tên file chính sách, nội dung chính sách hay đáp án. System prompt thực tế trong trace stage 02 (1816 ký tự) chỉ có quy tắc chung, mô tả workspace và catalog skill.

### Cách `list_files` hoạt động

1. Gọi `_resolve` (dùng chung với `read_file`): chặn path rỗng, đường dẫn tuyệt đối, `..`, và đường dẫn sau khi resolve (kể cả qua symlink/junction) nằm ngoài workspace.
2. Đường dẫn không tồn tại trả `PATH_NOT_FOUND`. Đường dẫn là file trả `NOT_A_DIRECTORY`, kèm gợi ý dùng `read_file`.
3. Liệt kê các mục trực tiếp bằng `iterdir()`, không đệ quy, sắp xếp theo tên. Mỗi mục có `name`, `path` (tương đối workspace) và `type` (`file` hoặc `directory`).
4. Cấu trúc kết quả giống `read_file`: `{"ok": true, "path": ..., "entries": [...]}` hoặc `{"ok": false, "error": {"code": ..., "message": ...}}`.
5. Docstring nói rõ khi nào dùng: tìm file khi chưa biết tên chính xác, rồi đọc bằng `read_file`.

## 3. Stage 00: giới hạn của agent

Câu hỏi trường hợp A, không dán chính sách vào chat:

![Stage 00: nhập câu hỏi trường hợp A](analysis-images/01-stage00-cau-hoi-a.png)

![Stage 00: câu trả lời](analysis-images/02-stage00-tra-loi.png)

Kết quả:
- 1 model call, **0 tool call**. Agent không đọc tài liệu nào.
- Agent trả lời bằng kiến thức chung: "thường là từ vài ngày đến vài tuần sau khi mua", rồi khuyên người dùng tự kiểm tra chính sách của nhà cung cấp. Nó không nêu hạn hoàn tiền hay phí của công ty, và không dẫn tài liệu nào.
- Con số "8 ngày" chỉ suy ra từ hai ngày trong câu hỏi, không dựa trên chính sách nào.

Agent còn thiếu:
1. Khả năng xem thư mục có những file gì, để tìm ra tài liệu chính sách.
2. Khả năng đọc nội dung file (stage 00 không có `read_file`).
3. Quy trình nghiệp vụ: chọn chính sách theo ngày mua, cách tính số ngày, hỏi lại khi thiếu thông tin, trả lời theo mẫu có dẫn tài liệu.

Bằng chứng: `stage-00-chat/traces/20261007-184549_4b2386df_turn01_f6308b60.jsonl`
- Dòng 1 (`user_submitted`): `"tools": []`, `"skills": []`.
- Dòng 2 (`model_request`): `"tools": []`. System prompt ghi "Project này không cấp tool nào: bạn không đọc được file...".
- Dòng 3 (`model_response`): `"tool_calls_requested": []`, 209 input / 102 output token.
- Dòng 4 (`run_completed`).

Nhận xét: system prompt đã dặn "không có tool phù hợp thì nói rõ giới hạn thay vì đoán", nhưng model vẫn trả lời bằng kiến thức chung chung. Chỉ dặn trong prompt không tạo ra được dữ liệu mà agent không truy cập được.

## 4. Kết quả kiểm tra tool

### 4.1 Gọi `list_files` trực tiếp

Stage 02, workspace thật, sau khi đổi tên file:

| Trường hợp | path | Kết quả |
|---|---|---|
| Thư mục hợp lệ | `data/policies` | `ok: true`, entries: `data/policies/refund-a.md` (file), `data/policies/refund-b.md` (file) |
| Đường dẫn là file | `data/policies/refund-a.md` | `ok: false`, `NOT_A_DIRECTORY`: "Đây không phải là thư mục: data/policies/refund-a.md, nên dùng read_file" |
| Không tồn tại | `data/khong-ton-tai` | `ok: false`, `PATH_NOT_FOUND`: "Không tìm thấy file: data/khong-ton-tai" |
| Vượt workspace bằng `..` | `../..` | `ok: false`, `PATH_OUTSIDE_WORKSPACE`: "Đường dẫn thoát ra ngoài workspace: ../.." |
| Đường dẫn tuyệt đối | `<đường dẫn tuyệt đối tới workspace/data>` | `ok: false`, `PATH_OUTSIDE_WORKSPACE`: "Không chấp nhận đường dẫn tuyệt đối" |

Stage 01, trước khi đổi tên, cho kết quả tương tự:
- `data/policies` trả `policy-before-oct.md` và `policy-from-oct.md`.
- `data/weekly_notes.md` trả `NOT_A_DIRECTORY`.
- `data/khong-co` trả `PATH_NOT_FOUND`.
- `../../` trả `PATH_OUTSIDE_WORKSPACE`.
- `.` liệt kê gốc workspace.

Ba trường hợp lỗi đều trả lỗi có mã, không trả danh sách rỗng như thể thư mục hợp lệ.

**Symlink dẫn ra ngoài.** Máy chạy bài không có quyền tạo symlink (`WinError 1314`). Vì vậy mình thử bằng junction, là liên kết thư mục của Windows, tạo được mà không cần quyền admin. Phép thử dùng một workspace giả trong thư mục tạm, chỉ chứa dữ liệu giả, và gọi thẳng `_list`:

| Trường hợp | path | Kết quả |
|---|---|---|
| Junction trỏ ra ngoài workspace | `data/link` | `ok: false`, `PATH_OUTSIDE_WORKSPACE` |
| Thư mục chứa junction | `data` | `ok: true`, liệt kê `data/link` (directory) và `data/note.md` (file) |

**Giới hạn đã biết.** Gọi thẳng vào liên kết trỏ ra ngoài thì bị chặn, và nội dung bên ngoài không bị đọc. Nhưng khi liệt kê thư mục cha, tool vẫn hiện tên liên kết và cho biết đích là thư mục. Cách khắc phục: trong vòng lặp, bỏ qua các mục có `child.resolve()` nằm ngoài workspace.

### 4.2 Test tự động (`uv run pytest -q`)

| Stage | Kết quả |
|---|---|
| `stage-01-files` | 32 pass, 2 fail |
| `stage-02-skills` | 39 pass, 2 fail |

Ở mỗi stage, 2 test fail là `test_read_symlink_escape_blocked` và `test_write_absolute_and_symlink_escape_rejected`. Cả hai lỗi `WinError 1314` khi tạo symlink vì Windows thiếu quyền, không phải lỗi logic. Hai test này fail cả trên code gốc của stage 01, trước khi thêm `list_files`.

### 4.3 Agent thật gọi `list_files` (stage 01)

Câu 1: "Trong thư mục data/policies có những file nào?". Câu hỏi không nhắc tên tool.

![Stage 01: agent dùng list_files](analysis-images/03-stage01-list-files.png)

Bằng chứng: `stage-01-files/traces/20261007-213448_5f9ad82f_turn01_6f87a117.jsonl`
- Dòng 1, 2: tool được cấp và schema gửi model có 3 tool, gồm `list_files`.
- Dòng 3: model tự yêu cầu gọi `list_files`.
- Dòng 4: `arguments = {"path": "data/policies"}`.
- Dòng 5: `status: success`, `ok: true`, đủ 2 file.
- Dòng 6 đến 8: model nhận kết quả và trả lời, không gọi thêm tool.

Câu 2, cùng cuộc trò chuyện: "Cho tôi biết nội dung các file trong data/policies."

![Stage 01: đọc nội dung các file](analysis-images/04-stage01-list-roi-read.png)

Bằng chứng: `stage-01-files/traces/20261007-213526_5f9ad82f_turn02_8fd7ab70.jsonl`
- Dòng 2: request có 5 message, gồm kết quả `list_files` của lượt 1.
- Dòng 3 đến 7: model gọi 2 `read_file` song song với đúng hai đường dẫn đã tìm được, cả hai `ok: true`.
- Dòng 8 đến 10: trả lời.

Agent không gọi lại `list_files` vì danh sách file đã nằm trong history. Chuỗi "tìm file rồi đọc" diễn ra qua hai lượt.

## 5. Kết quả từng trường hợp (stage 02)

### 5.1 Skill `refund-policy`

- `SKILL.md` có frontmatter `name: refund-policy` và `description`. Description nêu nhiệm vụ (tra cứu chính sách hoàn tiền, đánh giá yêu cầu hoàn tiền) và điều kiện dùng (người dùng hỏi về điều kiện, thời hạn hoặc phí hoàn tiền).
- Các bước:
  1. Kiểm tra đủ ngày mua, ngày yêu cầu, trạng thái kích hoạt. Thiếu thì hỏi lại.
  2. Tìm tài liệu trong `data/policies/` bằng `list_files`, đọc bằng `read_file`, không dựa vào tên file cố định.
  3. Chọn chính sách theo ngày mua và phạm vi hiệu lực.
  4. Tính chênh lệch ngày lịch.
  5. Đối chiếu điều kiện. Ngày bằng giới hạn vẫn trong hạn.
  6. Đọc template.
  7. Tự kiểm tra trước khi trả lời.
- Không yêu cầu Bash hoặc script.
- `references/answer-template.md` gồm: chính sách áp dụng, số ngày đã qua, kết luận, phí (ghi "Không áp dụng" nếu không đủ điều kiện), đường dẫn tài liệu căn cứ.

Cách skill được nạp, giống nhau ở mọi trace stage 02:
- System prompt chỉ chứa metadata của skill trong `<available_skills>` (tên, mô tả, vị trí `skills/refund-policy/SKILL.md`), kèm câu "nội dung skill chưa được nạp".
- Khi câu hỏi khớp mô tả, model gọi `read_file("skills/refund-policy/SKILL.md")` ở dòng 3 đến 5. Lúc đó nội dung skill mới vào history.

### 5.2 Bảng kết quả

| Trường hợp | Kết quả cần đạt | Kết quả thực tế | Đạt | Trace | Ảnh |
|---|---|---|---|---|---|
| A | Chính sách cũ, 8 ngày, không đủ điều kiện | Chính sách trước tháng 10, 8 ngày, không đủ điều kiện, dẫn `data/policies/policy-before-oct.md` | Đạt (sai lệch nhỏ ở mục phí) | `..._0f11ef7e_turn01_f5569244` | 05 |
| B | Chính sách mới, 10 ngày, đủ điều kiện, không phí | Chính sách từ tháng 10, 10 ngày, đủ điều kiện, không thu phí, dẫn `data/policies/policy-from-oct.md` | Đạt | `..._364db552_turn01_a2f1c385` | 06 |
| A sau đổi tên | Kết luận như A | Chọn đúng chính sách cũ nhưng kết luận "đủ điều kiện, không bị phí" | **Không đạt** | `..._a6431f35_turn01_700c2abe` | 08 |
| B sau đổi tên | Kết luận như B | Chính sách từ tháng 10, 10 ngày, đủ điều kiện, không phí, dẫn `data/policies/refund-b.md` | Đạt | `..._043bb805_turn01_26e282ed` | 09 |
| Thiếu thông tin | Hỏi trạng thái kích hoạt, chưa kết luận | Đề nghị xác nhận trạng thái kích hoạt, không kết luận đủ hay không đủ điều kiện | Đạt | `..._2f5d85d0_turn01_c0e60327` | 10 |

Tất cả trace ở bảng trên nằm trong `stage-02-skills/traces/` (tên file bắt đầu bằng `20261007-`).

Số ngày đúng theo quy ước của đề:
- A: 28/09/2026 đến 06/10/2026 là 2 ngày cuối tháng 9 cộng 6 ngày tháng 10, tức 8 ngày. Lớn hơn 7, nên không đủ điều kiện.
- B: 02/10/2026 đến 12/10/2026 là 10 ngày. Nhỏ hơn hoặc bằng 14, chưa kích hoạt, nên đủ điều kiện, không phí.

### 5.3 Trường hợp A

![Stage 02: trường hợp A](analysis-images/05-stage02-case-a.png)

Bằng chứng: `stage-02-skills/traces/20261007-223009_0f11ef7e_turn01_f5569244.jsonl`
- Dòng 1: tool được cấp có `list_files`. Catalog có `refund-policy` và `weekly-report`.
- Dòng 3 đến 5: `read_file("skills/refund-policy/SKILL.md")`, `ok: true`. Nội dung skill vào history.
- Dòng 7 đến 11: `list_files("data/policies/")` tìm ra `policy-before-oct.md` và `policy-from-oct.md`. Đồng thời `read_file("skills/refund-policy/references/answer-template.md")`, `ok: true`.
- Dòng 13 đến 17: đọc cả hai chính sách, trong đó có chính sách cũ `data/policies/policy-before-oct.md`.
- Dòng 19, 20: trả lời, không gọi thêm tool (4 model call, 5 tool call).

Trace của một lượt không lưu nội dung câu trả lời cuối, chỉ lưu `answer_chars`. Câu trả lời này được lưu nguyên văn trong history của lượt sau: `stage-02-skills/traces/20261007-223131_0f11ef7e_turn02_22edaafd.jsonl`, dòng 2, message #9. Nội dung khớp ảnh:

> Chính sách áp dụng: Chính sách hoàn tiền trước tháng 10. Số ngày đã qua: 8 ngày. Kết luận: Không đủ điều kiện vì bạn đã quá thời hạn 7 ngày yêu cầu hoàn tiền. Phí hoàn tiền: 10% giá trị đơn hàng. Tài liệu căn cứ: `data/policies/policy-before-oct.md`.

Sai lệch nhỏ: template yêu cầu ghi "Không áp dụng" ở mục phí khi không đủ điều kiện, nhưng agent vẫn ghi "10% giá trị đơn hàng". Chính sách, số ngày và kết luận đều đúng.

### 5.4 Trường hợp B

Lần chạy đầu ở lượt 2 của cuộc trò chuyện trên bị lỗi mạng: `stage-02-skills/traces/20261007-223131_0f11ef7e_turn02_22edaafd.jsonl`, dòng 3, `run_failed: OpenAIConnectionError: Connection error.`. `stage-02-skills/traces/debug.log` ghi lỗi `WinError 10054` lúc 22:31:33. Trường hợp B được chạy lại trong một cuộc trò chuyện mới.

![Stage 02: trường hợp B](analysis-images/06-stage02-case-b.png)

Bằng chứng: `stage-02-skills/traces/20261007-223152_364db552_turn01_a2f1c385.jsonl`
- Dòng 3 đến 5: đọc `SKILL.md`.
- Dòng 7 đến 11: `list_files("data/policies/")` và đọc `answer-template.md`.
- Dòng 13 đến 17: đọc hai chính sách.
- Dòng 19, 20: trả lời (4 model call, 5 tool call).

Kết quả: chính sách từ tháng 10, 10 ngày (trong giới hạn 14 ngày), đủ điều kiện, không thu phí, căn cứ `data/policies/policy-from-oct.md`.

### 5.5 Đổi tên file

Đổi tên `policy-before-oct.md` thành `refund-a.md` và `policy-from-oct.md` thành `refund-b.md`. Nội dung giữ nguyên: đã đối chiếu, nội dung `refund-a.md` trùng chính sách trước tháng 10, `refund-b.md` trùng chính sách từ tháng 10. Không sửa code, prompt hay skill.

![Tên file sau khi đổi](analysis-images/07-stage02-doi-ten-file.png)

Mỗi trường hợp chạy trong một cuộc trò chuyện mới. Ở cả hai trace, dòng 2 có `message_count = 1`: request đầu chỉ chứa câu hỏi, không có history cũ, nên không thể dùng lại tài liệu từ lần chạy trước.

#### Trường hợp A sau khi đổi tên: không đạt

![Stage 02: trường hợp A sau khi đổi tên](analysis-images/08-stage02-case-a-sau-doi-ten.png)

Bằng chứng: `stage-02-skills/traces/20261007-223827_a6431f35_turn01_700c2abe.jsonl`
- Dòng 2: `message_count = 1`, cuộc trò chuyện mới.
- Dòng 3 đến 5: đọc `SKILL.md`.
- Dòng 7 đến 9: `list_files("data/policies/")` trả về **tên mới** `refund-a.md`, `refund-b.md`.
- Dòng 11 đến 15: `read_file` đúng hai file mới, cả hai `ok: true`.
- **Không có** lệnh đọc `references/answer-template.md`. Panel "Tài nguyên đã đọc (2)" trong ảnh chỉ có `refund-a.md` và `refund-b.md`.
- Dòng 17, 18: trả lời (4 model call, 4 tool call).

Câu trả lời trong ảnh chọn đúng "Chính sách hoàn tiền trước tháng 10". Nhưng nó viết "Bạn mua vào 28/09, yêu cầu hoàn trong thời gian 7 ngày (đến 05/10), nên bạn vẫn trong hạn yêu cầu hoàn tiền" và kết luận "Bạn có đủ điều kiện để yêu cầu hoàn tiền mà không bị phí". Kết luận này sai: yêu cầu ngày 06/10 đã qua hạn 05/10 mà chính agent vừa tính ra. Câu trả lời cũng không theo template: thiếu số ngày đã qua, thiếu đường dẫn tài liệu căn cứ, chỉ ghi tiêu đề chính sách.

Phân tích nguyên nhân:
- Bước tìm và đọc tài liệu chạy đúng. `list_files` tìm ra tên mới, agent đọc đúng file và chọn đúng chính sách theo ngày mua. Việc đổi tên file không làm hỏng bước này.
- Lỗi nằm ở bước suy luận: so sánh ngày yêu cầu với hạn cuối. Ở lần chạy này model bỏ qua bước 6 của skill (đọc template), nên không có khung bắt buộc ghi "số ngày đã qua" để tự đối chiếu.
- Cùng đầu vào và cùng nội dung chính sách, lần chạy trước khi đổi tên cho kết luận đúng. Model không cho kết quả giống nhau mỗi lần chạy (`gpt-4o-mini`, không cố định tham số sinh).

Hướng khắc phục, chưa thực hiện trong bài nộp này:
1. Sửa bước tính ngày trong `SKILL.md` cho tường minh: "hạn cuối = ngày mua + N ngày. Đủ điều kiện về thời gian khi và chỉ khi ngày yêu cầu ≤ hạn cuối. Ghi rõ số ngày trước khi kết luận."
2. Ghi bước đọc template là bắt buộc trước khi trả lời, kèm luật phí "Không áp dụng" khi không đủ điều kiện.
3. Chạy lại trường hợp A sau đổi tên trong cuộc trò chuyện mới để xác nhận.
4. Ở stage có Bash (stage 03, 04), có thể chuyển phép tính ngày sang script để kết quả luôn giống nhau mỗi lần chạy.

#### Trường hợp B sau khi đổi tên: đạt

![Stage 02: trường hợp B sau khi đổi tên](analysis-images/09-stage02-case-b-sau-doi-ten.png)

Bằng chứng: `stage-02-skills/traces/20261007-224003_043bb805_turn01_26e282ed.jsonl`
- Dòng 2: `message_count = 1`, cuộc trò chuyện mới.
- Dòng 3 đến 5: `read_file("skills/refund-policy/SKILL.md")`. **Nội dung skill vào history.**
- Dòng 7 đến 11: `list_files("data/policies/")` trả về `refund-a.md`, `refund-b.md`. Đồng thời `read_file("skills/refund-policy/references/answer-template.md")`. **Nội dung reference vào history.**
- Dòng 13 đến 17: đọc `refund-b.md` và `refund-a.md`.
- Dòng 19, 20: trả lời (4 model call, 5 tool call).

Kết quả: chính sách từ tháng 10, chênh lệch 02/10/2026 đến 12/10/2026 là 10 ngày, đủ điều kiện, không thu phí, căn cứ `data/policies/refund-b.md`. Kết luận giống lần chạy trước khi đổi tên. Câu trả lời có lặp nội dung hai lần (một danh sách đánh số và một khối theo template), nhưng không ảnh hưởng tính đúng.

### 5.6 Thiếu thông tin

Câu hỏi: "Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026." Câu này không nói sản phẩm đã kích hoạt hay chưa.

![Stage 02: thiếu thông tin](analysis-images/10-stage02-thieu-thong-tin.png)

Bằng chứng: `stage-02-skills/traces/20261007-224231_2f5d85d0_turn01_c0e60327.jsonl`
- Dòng 3 đến 5: đọc `SKILL.md`. Bước 1 của skill yêu cầu hỏi lại nếu thiếu trạng thái kích hoạt.
- Dòng 7 đến 9: `list_files("data/policies/")`.
- Dòng 11 đến 15: đọc `refund-a.md`, `refund-b.md`.
- Dòng 17, 18: trả lời (4 model call, 4 tool call).

Kết quả:
- Agent nêu chính sách từ tháng 10 áp dụng và hạn yêu cầu đến 16/10/2026, rồi viết: "Tuy nhiên, cần lưu ý rằng nếu sản phẩm của bạn đã được kích hoạt, sẽ không được hoàn tiền. Bạn có thể xác nhận trạng thái kích hoạt sản phẩm để tiếp tục quy trình hoàn tiền."
- Agent **không** kết luận đủ hay không đủ điều kiện, và **không** tự giả định "chưa kích hoạt". Yêu cầu của đề đạt.
- Ghi chú: agent vẫn đọc chính sách và phân tích một phần trước khi hỏi lại, trong khi skill đặt bước kiểm tra thông tin lên đầu. Câu hỏi lại cũng khá mềm ("Bạn có thể xác nhận...").

## 6. Câu hỏi cuối bài

**Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách? Nếu agent chưa có tool tìm file, việc sửa prompt có giải quyết được yêu cầu đổi tên file không?**

### Vì sao cần tool để tìm file

Model không tự nhìn thấy hệ thống file. Nó chỉ biết những gì nằm trong context: system prompt, tin nhắn, kết quả tool. `read_file` chỉ dùng được khi đã biết đúng đường dẫn. Thiếu `list_files`, agent không có cách nào biết thư mục đang có những file nào, nên chỉ có thể đoán tên file hoặc trả lời bằng kiến thức chung. Đó đúng là điều xảy ra ở stage 00: 0 tool call, câu trả lời "thường vài ngày đến vài tuần".

`list_files` biến "danh sách file hiện có" thành dữ liệu lấy **lúc chạy**, không phải dữ liệu viết sẵn trong prompt hay code. Vì thế khi đổi tên file, không cần sửa gì. Ở trace `a6431f35` và `043bb805`, agent gọi `list_files("data/policies/")`, nhận về `refund-a.md`, `refund-b.md` và đọc đúng hai file mới, dù không có dòng code hay prompt nào nhắc tới hai tên này.

### Vì sao cần skill để hướng dẫn chọn chính sách

Tool cho agent **khả năng** (đọc được gì, liệt kê được gì). Tool không cho **quy trình** (dùng khả năng đó thế nào, theo thứ tự nào, theo luật nghiệp vụ nào). Bài này có những luật mà model không tự biết:
- Tìm ở `data/policies/`.
- Chọn chính sách theo **ngày mua**, không theo ngày yêu cầu hay ngày hiện tại của máy.
- Số ngày là chênh lệch ngày lịch. Ngày bằng giới hạn vẫn hợp lệ.
- Thiếu thông tin thì hỏi lại, không giả định.
- Trả lời theo mẫu, có đường dẫn tài liệu làm căn cứ.

Skill gói các luật đó thành tài liệu chỉ nạp khi cần. System prompt chỉ chứa metadata (tên, mô tả, vị trí). Khi câu hỏi khớp mô tả, model tự đọc `SKILL.md` rồi đọc `answer-template.md` (dòng 3 đến 11 ở các trace stage 02). Nhờ vậy:
- System prompt gọn, tác vụ không liên quan (ví dụ báo cáo tuần) không phải mang theo luật hoàn tiền.
- Muốn đổi quy trình thì sửa skill, không phải sửa code.
- Trace cho thấy rõ skill nào đã được dùng và lúc nào.

Trường hợp thiếu thông tin là ví dụ trực tiếp: agent hỏi lại trạng thái kích hoạt thay vì tự giả định, đúng bước 1 của skill.

### Nếu chưa có tool tìm file, sửa prompt có giải quyết được việc đổi tên file không?

**Không.**

1. Prompt là văn bản tĩnh, viết trước khi chạy. Nó không biết thư mục hiện có file gì. Viết "hãy tìm file chính sách trong `data/policies/`" mà không có tool liệt kê thì đó là chỉ dẫn không có hành động tương ứng. Model chỉ có thể đoán tên rồi gọi `read_file`, đoán sai thì nhận `FILE_NOT_FOUND`.
2. Cách duy nhất để prompt "chạy được" là ghi cứng tên file, ví dụ `data/policies/policy-before-oct.md`. Việc này vi phạm ràng buộc của đề. Và mỗi lần đổi tên, prompt lại phải sửa theo: sau khi đổi thành `refund-a.md`, prompt cũ trỏ vào file không còn tồn tại. Vấn đề chỉ được chuyển từ "agent tự tìm" sang "con người cập nhật tay", không được giải quyết.
3. Dán thẳng nội dung chính sách vào prompt cũng không được: đề cấm, và khi chính sách thay đổi thì prompt lại lỗi thời.
4. Bằng chứng stage 00: system prompt đã dặn "không có tool phù hợp thì nói rõ giới hạn thay vì đoán", vậy mà model vẫn trả lời bằng kiến thức chung. Prompt điều chỉnh được hành vi phần nào, nhưng không tạo ra được khả năng truy cập dữ liệu mà agent không có.

Tóm lại: tool giải quyết việc "tìm và đọc được dữ liệu thật lúc chạy", skill giải quyết việc "dùng dữ liệu đó đúng quy trình nghiệp vụ". Prompt chỉ điều phối hai thứ này, không thay thế được chúng.

Kết quả trường hợp A sau khi đổi tên cho thấy thêm một điều: có đủ tool và skill vẫn chưa bảo đảm câu trả lời đúng. Model có thể bỏ qua một bước của skill hoặc tính sai. Vì vậy vẫn cần kiểm tra lại bằng trace, viết skill tường minh hơn, và với phép tính cần chính xác tuyệt đối thì giao cho script ở stage có Bash.

## 7. Ghi chú

- Trace không lưu nội dung câu trả lời cuối của một lượt, chỉ lưu `answer_chars`. Câu trả lời được lấy từ ảnh chụp, và với trường hợp A thì từ history của lượt kế tiếp.
- Dòng mô tả dưới tiêu đề app (`CAPABILITY_TEXT` trong `config.py`) vẫn ghi "Tools: read_file, write_file". Đây chỉ là chữ hiển thị. Danh sách tool thật gửi cho model có 3 tool (trace `user_submitted` và `model_request`, panel "Tools được cấp (3)").
- Thông báo lỗi `PATH_NOT_FOUND` ghi "Không tìm thấy file" dù đường dẫn có thể là thư mục. Mã lỗi vẫn đúng.
- Không nộp `.env` hay API key.
