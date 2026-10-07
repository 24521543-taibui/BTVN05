---
name: csv-quality
description: BẮT BUỘC đọc skill này trước khi mở file CSV công việc (cột task_id, owner, hours) hoặc trả lời về giờ làm việc của từng người. Dùng khi người dùng muốn kiểm tra file CSV công việc, hỏi người nào vượt N giờ, ai quá tải, tổng giờ theo người, hoặc yêu cầu ghi báo cáo từ file đó. Tự đọc CSV rồi cộng sẽ sai vì file có dòng lỗi và task_id trùng, chỉ script trong skill mới cho kết quả đúng.
---

# CSV quality

Kiểm tra chất lượng CSV công việc và tính tổng giờ theo người bằng script. Không đọc CSV rồi tự cộng, không tự suy ra kết quả: mọi con số trong câu trả lời và báo cáo lấy từ JSON của script.

## Quy trình bắt buộc

1. Xác định ngưỡng giờ từ yêu cầu hiện tại (mục "Ngưỡng giờ"). Chưa có ngưỡng thì hỏi người dùng rồi dừng.
2. Chạy script bằng tool `bash` (mục "Chạy script"). Không dùng `read_file` để đọc CSV rồi tự tính.
3. Kiểm tra `exit_code` (mục "Kiểm tra kết quả").
4. Đọc `references/report-template.md`, viết báo cáo bằng `write_file` (mục "Viết báo cáo").
5. Trả lời: ngưỡng đã dùng, tổng giờ theo người, ai quá tải, dòng bị loại và đường dẫn báo cáo.

## Ngưỡng giờ (`--max-hours`)

Script bắt buộc có `--max-hours`. Lấy ngưỡng từ yêu cầu hiện tại của người dùng, thường viết dạng "vượt N giờ", "quá N giờ", "ngưỡng N", "tối đa N giờ".

- Yêu cầu có số giờ N: **N chính là ngưỡng**. Truyền đúng N vào `--max-hours`, không làm tròn, không đổi đơn vị và không hỏi lại.
- Yêu cầu không có số giờ nào: hỏi người dùng ngưỡng giờ rồi dừng. Chưa chạy script, chưa nêu tổng giờ, chưa nêu ai quá tải. Không tự chọn ngưỡng. Không dùng ngưỡng từ ví dụ, từ lần chạy trước hay từ cuộc trò chuyện cũ.
- Ngưỡng phải là số hữu hạn không âm. Người dùng đưa giá trị khác (số âm, chữ) thì báo lại và hỏi ngưỡng hợp lệ.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <N>
```

Thay `<đường dẫn CSV>` bằng đường dẫn người dùng nêu (ví dụ `data/ten-file.csv`) và `<N>` bằng ngưỡng giờ ở bước 1. Chạy cả khi chưa chắc file có tồn tại: script tự báo lỗi nếu không có file.

Không cần đọc source script để chạy.

## Kiểm tra kết quả

- `exit_code` 0: phân tích thành công, `stdout` là JSON. Dữ liệu có lỗi, có dòng bị loại hoặc có người quá tải vẫn là exit 0.
- `exit_code` 1: **lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi parse). Đọc `stderr` và báo người dùng là không phân tích được, kèm nội dung lỗi. Không đưa ra tổng giờ, người quá tải hay thống kê nào. Không ghi báo cáo như thể đã phân tích.
- `exit_code` 2: **lệnh sai** (thiếu `--input`/`--max-hours` hoặc ngưỡng không hợp lệ). Đọc `stderr`. Lỗi do ngưỡng thì hỏi lại người dùng, không tự thay ngưỡng khác.
- `timed_out` true hoặc `ok` false: lệnh không chạy xong, báo lỗi và không suy đoán kết quả.
- Phân biệt **lỗi dữ liệu** (nằm trong `issues` và `excluded_rows`, script vẫn chạy thành công) với **lỗi thực thi** (exit khác 0).

## Ý nghĩa JSON

Thống kê chất lượng, tính trên mọi dòng dữ liệu: `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.

Tổng giờ và quá tải:
- `max_hours`: ngưỡng script đã nhận, phải trùng ngưỡng người dùng nêu.
- `hours_by_owner`: tổng giờ theo owner, chỉ gồm các dòng được cộng. Owner phân biệt hoa/thường, không gộp tên.
- `overloaded_owners`: người có tổng giờ **lớn hơn** ngưỡng, sắp xếp theo tên. Bằng ngưỡng không phải quá tải. Danh sách rỗng nghĩa là không ai quá tải.
- `excluded_rows`: các dòng **không** được cộng, mỗi dòng một lần. `line` tính theo file (header là line 1), `task_id` là null khi trống, `reasons` gồm các mã:
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
