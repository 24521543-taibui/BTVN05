# block2: Kiểm tra quá tải theo người

Bài luyện tập D05 / 02. Phân tích đầy đủ, kết quả từng trường hợp và vị trí bằng chứng trong trace: [analysis.md](analysis.md).

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `skill/csv-quality/` | Skill đã cập nhật: `SKILL.md`, `references/report-template.md`, `scripts/check_csv.py` |
| `data/` | CSV đầu vào: `workload.csv`, `workload-edge.csv` |
| `tests/` | `test_check_csv.py`, gồm kiểm thử cho ID đầu tiên có hours không hợp lệ. Test này chạy trong project `stage-04-script-skill` (dùng `paths` của project) |
| `outputs/` | JSON chạy script trực tiếp (ngưỡng 8, 9, trường hợp đặc biệt), kết quả test, câu trả lời của agent, phân tích lệnh Stage 03 |
| `traces/` | Trace của agent: `lan1/`, `lan2/` (chạy trên giao diện), `lan3/`, `lan4/` (bản chốt), `stage03-chay-khong-giao-dien/` |
| `reports/` | Báo cáo agent tạo, theo từng lần chạy |
| `skill-v1-truoc-khi-sua/` | Skill ở lần chạy 1, để đối chiếu |
| `probe/` | Thí nghiệm đo hành vi agent theo phiên bản skill: script, biến thể, dữ liệu từng lượt, [KET-QUA-DO-THU.md](probe/KET-QUA-DO-THU.md) |

## Chạy script trực tiếp

Từ thư mục `block2/`, cần Python 3.11 trở lên (script chỉ dùng thư viện chuẩn):

```bash
python skill/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8
python skill/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 9
python skill/csv-quality/scripts/check_csv.py --input data/workload-edge.csv --max-hours 0
```

Thiếu `--max-hours` hoặc giá trị không hợp lệ: lỗi ở stderr, exit 2. File không tồn tại: lỗi ở stderr, exit 1.
