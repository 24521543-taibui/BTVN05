# Báo cáo dữ liệu công việc: `{đường dẫn CSV}`

Công cụ: `skills/csv-quality/scripts/check_csv.py` | Lệnh: `{lệnh đã chạy}` | exit code: {exit_code}

## Ngưỡng quá tải
- Ngưỡng: **{max_hours} giờ** (người dùng cung cấp, truyền vào `--max-hours`).
- Quy tắc: quá tải khi tổng giờ lớn hơn ngưỡng. Bằng ngưỡng không phải quá tải.

## Tổng giờ theo người
Chỉ cộng các dòng hợp lệ. Dòng bị loại nằm ở mục "Dòng bị loại khỏi tổng giờ".

| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| {owner} | {total_hours} | {Có hoặc Không} |

## Người vượt ngưỡng
{mỗi người trong overloaded_owners một dòng dạng "- Tên: N giờ (ngưỡng M giờ)"; nếu danh sách rỗng thì chỉ ghi một dòng "- Không ai vượt ngưỡng M giờ."}

## Dòng bị loại khỏi tổng giờ
| Line | task_id | Mã lý do | Diễn giải |
|---|---|---|---|
| {line} | {task_id, ghi (trống) nếu null} | {các mã trong reasons, giữ nguyên thứ tự} | {giải thích từng mã, lấy từ message tương ứng trong issues} |

{nếu excluded_rows rỗng thì thay bảng trên bằng một dòng "Không có dòng nào bị loại."}

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
- {nhận xét ngắn: tổng giờ ở trên chỉ tính các dòng hợp lệ, các dòng bị loại cần được sửa thì tổng giờ mới đầy đủ; không cộng giờ của dòng bị loại}

## Khuyến nghị
- {cách sửa đề xuất cho từng nhóm lỗi; không tự sửa file nguồn}
