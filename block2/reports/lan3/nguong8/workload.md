# Báo cáo dữ liệu công việc: `data/workload.csv`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | Lệnh: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8` | exit code: 0

## Ngưỡng quá tải
- Ngưỡng: **8 giờ** (người dùng cung cấp, truyền vào `--max-hours`).
- Quy tắc: quá tải khi tổng giờ **lớn hơn** ngưỡng. Bằng ngưỡng không phải quá tải.

## Tổng giờ theo người
Chỉ cộng các dòng hợp lệ. Các dòng bị loại nằm ở mục "Dòng bị loại khỏi tổng giờ".

| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| Lan | 9 | Có |
| Minh | 3 | Không |

## Người vượt ngưỡng
- Lan: 9 giờ (ngưỡng 8 giờ)

Nếu `overloaded_owners` rỗng, ghi: "Không ai vượt ngưỡng 8 giờ."

## Dòng bị loại khỏi tổng giờ
| Line | task_id | Mã lý do | Diễn giải |
|---|---|---|---|
| 5 | T04 | invalid_hours | hours 'abc' không phải số hữu hạn không âm. |
| 6 | T02 | duplicate_id | task_id T02 đã xuất hiện ở line 3. |
| 7 | T05 | missing_owner | owner trống. |

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
| Số dòng dữ liệu (không tính header) | 6 |
| Dòng thiếu owner | 1 |
| Dòng hours không hợp lệ | 1 |
| Số task_id bị lặp (distinct) | 1 (T02) |

### Chi tiết lỗi
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| 5 | hours | invalid_hours | T04 | hours 'abc' không phải số hữu hạn không âm. |
| 6 | task_id | duplicate_id | T02 | task_id T02 đã xuất hiện ở dòng trước. |
| 7 | owner | missing_owner | T05 | owner trống. |

## Đánh giá
- Tổng giờ ở trên chỉ tính các dòng hợp lệ. Nêu rằng các dòng bị loại cần được sửa thì tổng giờ mới đầy đủ; không tự cộng giờ của dòng bị loại.

## Khuyến nghị
- Kiểm tra lại dữ liệu ở dòng 5 để đảm bảo hours hợp lệ.
- Thay đổi task_id T02 ở dòng 6 hoặc xóa dòng này để không bị lặp.
- Cung cấp owner cho task_id T05 ở dòng 7.