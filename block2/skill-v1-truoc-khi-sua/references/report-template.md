# Báo cáo dữ liệu công việc: `{đường dẫn CSV}`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | Lệnh: `{lệnh đã chạy}` | exit code: {exit_code}

## Ngưỡng quá tải
- Ngưỡng: **{max_hours} giờ** (người dùng cung cấp, truyền vào `--max-hours`).
- Quy tắc: quá tải khi tổng giờ **lớn hơn** ngưỡng. Bằng ngưỡng không phải quá tải.

## Tổng giờ theo người
Chỉ cộng các dòng hợp lệ. Các dòng bị loại nằm ở mục "Dòng bị loại khỏi tổng giờ".

| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| {owner} | {hours_by_owner[owner]} | {Có nếu owner nằm trong overloaded_owners, ngược lại Không} |

## Người vượt ngưỡng
- {owner}: {total_hours} giờ (ngưỡng {max_hours} giờ)

Nếu `overloaded_owners` rỗng, ghi: "Không ai vượt ngưỡng {max_hours} giờ."

## Dòng bị loại khỏi tổng giờ
| Line | task_id | Mã lý do | Diễn giải |
|---|---|---|---|
| {line} | {task_id, ghi "(trống)" nếu null} | {reasons, giữ nguyên thứ tự} | {giải thích từng mã} |

Nếu `excluded_rows` rỗng, ghi: "Không có dòng nào bị loại."

Diễn giải mã lý do:
- `wrong_field_count`: số trường khác số cột của header.
- `missing_task_id`: thiếu task_id.
- `duplicate_id`: task_id đã xuất hiện ở dòng trước; chỉ giữ lần xuất hiện đầu tiên.
- `missing_owner`: thiếu owner.
- `invalid_hours`: hours không phải số hữu hạn không âm.

## Chất lượng dữ liệu (toàn bộ dòng)
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | {row_count} |
| Dòng thiếu owner | {missing_owner_count} |
| Dòng hours không hợp lệ | {invalid_hours_count} |
| Số task_id bị lặp (distinct) | {duplicate_id_count} ({duplicate_ids}) |

### Chi tiết lỗi
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| {line} | {column} | {type} | {task_id} | {message} |

## Đánh giá
- Tổng giờ ở trên chỉ tính các dòng hợp lệ. Nêu rằng các dòng bị loại cần được sửa thì tổng giờ mới đầy đủ; không tự cộng giờ của dòng bị loại.

## Khuyến nghị
- {Cách sửa đề xuất cho từng nhóm lỗi; không tự sửa file nguồn}
