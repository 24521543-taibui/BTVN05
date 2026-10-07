---
name: csv-quality
description: Kiểm tra chất lượng file CSV danh sách công việc (cột task_id, owner, hours), tính tổng giờ theo người và xác định người quá tải theo ngưỡng giờ người dùng đưa ra, bằng script có sẵn, rồi ghi báo cáo Markdown dưới output/. Dùng khi người dùng yêu cầu kiểm tra, rà soát chất lượng dữ liệu CSV công việc, tính tổng giờ theo owner hoặc hỏi ai vượt ngưỡng, ai quá tải.
---

# CSV quality

Kiểm tra chất lượng CSV công việc và tính tổng giờ theo người bằng script, không tự đếm hay tự cộng bằng mắt.

## Ngưỡng giờ (`--max-hours`)

Script bắt buộc có `--max-hours`. Ngưỡng phải do người dùng nêu rõ trong yêu cầu đang xử lý.

- Người dùng có nêu ngưỡng (ví dụ "ai vượt X giờ", "ngưỡng X giờ"): truyền **đúng giá trị đó** vào `--max-hours`, không làm tròn, không đổi đơn vị.
- Người dùng chưa nêu ngưỡng: **hỏi lại ngưỡng trước**, chưa chạy script, chưa nêu tổng giờ hay ai quá tải. Không tự chọn ngưỡng, không lấy ngưỡng từ ví dụ, từ lần chạy trước hay từ cuộc trò chuyện cũ. Kể cả khi người dùng chỉ yêu cầu kiểm tra chất lượng, script vẫn cần ngưỡng, nên vẫn hỏi.
- Ngưỡng phải là số hữu hạn không âm. Nếu người dùng đưa giá trị khác (số âm, chữ), báo lại và hỏi ngưỡng hợp lệ.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh đầy đủ:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng người dùng nêu>
```

Ví dụ: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours <ngưỡng>`

Không cần đọc source script để chạy. Chỉ đọc `scripts/check_csv.py` khi cần hiểu một hành vi mà phần dưới không mô tả.

## Kiểm tra kết quả

- `exit_code` 0: phân tích thành công. `stdout` là JSON. Dữ liệu có lỗi, có dòng bị loại hoặc có người quá tải vẫn là exit 0.
- `exit_code` 1: **lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi parse). Đọc `stderr`, báo người dùng là không phân tích được. Không đưa ra tổng giờ, người quá tải hay thống kê nào, không ghi báo cáo như thể đã phân tích.
- `exit_code` 2: **lệnh sai** (thiếu `--input`/`--max-hours` hoặc ngưỡng không hợp lệ). Đọc `stderr`. Nếu lỗi do ngưỡng thì hỏi lại người dùng, không tự thay ngưỡng khác.
- `timed_out` true hoặc `ok` false: lệnh không chạy xong; báo lỗi, không suy đoán kết quả.
- Phân biệt rõ **lỗi dữ liệu** (nằm trong `issues` và `excluded_rows`, script vẫn chạy thành công) với **lỗi thực thi** (exit khác 0).

## Ý nghĩa JSON

Thống kê chất lượng, tính trên mọi dòng dữ liệu: `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.

Tổng giờ và quá tải:
- `max_hours`: ngưỡng script đã nhận. Phải trùng với ngưỡng người dùng nêu.
- `hours_by_owner`: tổng giờ theo owner, chỉ gồm các dòng được cộng. Owner phân biệt hoa/thường, không gộp tên.
- `overloaded_owners`: người có tổng giờ **lớn hơn** ngưỡng, sắp xếp theo tên. Bằng ngưỡng không phải quá tải. Danh sách rỗng nghĩa là không ai quá tải.
- `excluded_rows`: các dòng **không** được cộng, mỗi dòng xuất hiện một lần. `line` tính theo file (header là line 1), `task_id` là null khi trống, `reasons` gồm các mã:
  - `wrong_field_count`: số trường khác số cột của header.
  - `missing_task_id`: task_id trống.
  - `duplicate_id`: task_id đã xuất hiện ở dòng trước. Chỉ lần xuất hiện đầu tiên được giữ, kể cả khi lần đầu không hợp lệ.
  - `missing_owner`: owner trống.
  - `invalid_hours`: hours không phải số hữu hạn không âm (0 hợp lệ).

## Viết báo cáo

1. Đọc template `references/report-template.md` trong thư mục skill này, tức `skills/csv-quality/references/report-template.md`.
2. Lấy mọi con số từ JSON của script: ngưỡng, tổng giờ, người quá tải, dòng bị loại, thống kê chất lượng. Không tự cộng lại, không tự so sánh với ngưỡng, không cộng giờ của dòng bị loại.
3. Liệt kê mọi dòng trong `excluded_rows` kèm toàn bộ lý do. Mỗi issue ghi line number (header là line 1), cột và mô tả.
4. Không sửa file CSV khi người dùng chỉ yêu cầu kiểm tra. Có thể đề xuất cách sửa trong mục khuyến nghị.
5. Ghi báo cáo bằng `write_file` vào đường dẫn người dùng yêu cầu (mặc định `output/csv-quality.md`), rồi trả lời đường dẫn, ngưỡng đã dùng, ai quá tải và tóm tắt ngắn.
