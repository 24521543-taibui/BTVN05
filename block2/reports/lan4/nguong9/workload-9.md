# Báo cáo dữ liệu công việc: `data/workload.csv`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | Lệnh: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 9` | exit code: 0

## Ngưỡng quá tải
- Ngưỡng: **9 giờ** (người dùng cung cấp, truyền vào `--max-hours`).
- Quy tắc: quá tải khi tổng giờ lớn hơn ngưỡng. Bằng ngưỡng không phải quá tải.

## Tổng giờ theo người
Chỉ cộng các dòng hợp lệ. Dòng bị loại nằm ở mục "Dòng bị loại khỏi tổng giờ".

| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| Lan | 9 | Không |
| Minh | 3 | Không |

## Người vượt ngưỡng
- Không ai vượt ngưỡng 9 giờ.

## Dòng bị loại khỏi tổng giờ
| Line | task_id | Mã lý do | Diễn giải |
|---|---|---|---|
| 5 | T04 | invalid_hours | hours 'abc' không phải số hữu hạn không âm. |
| 6 | T02 | duplicate_id | task_id T02 đã xuất hiện ở line 3. |
| 7 | T05 | missing_owner | owner trống. |

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
| 6 | task_id | duplicate_id | T02 | task_id T02 đã xuất hiện ở line 3. |
| 7 | owner | missing_owner | T05 | owner trống. |

## Đánh giá
- Tổng giờ ở trên chỉ tính các dòng hợp lệ, các dòng bị loại cần được sửa thì tổng giờ mới đầy đủ; không cộng giờ của dòng bị loại.

## Khuyến nghị
- Sửa lại giờ cho task_id T04 để có giá trị hợp lệ.
- Xóa hoặc điều chỉnh task_id T02 để không bị lặp.
- Điền thông tin owner cho task_id T05.