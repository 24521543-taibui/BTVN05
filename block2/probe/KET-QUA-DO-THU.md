# Kết quả đo hành vi agent theo phiên bản skill

Thí nghiệm bổ sung, **không phải** trace nộp bài. Mục đích: tìm cách viết `SKILL.md` và `report-template.md` để agent `gpt-4o-mini` dùng skill đúng.

## Cách đo

- `scripts/probe_agent.py` chạy agent của `stage-04-script-skill` (cùng `build_agent`, system prompt, tools và model với app) trong một bản sao workspace tạm, mỗi lượt là một cuộc trò chuyện mới. Không ghi vào `traces/` hay `workspace/` của project.
- Mỗi dòng của file kết quả trong `ket-qua/` là một lượt chạy: các tool call (tên, tham số, exit code), câu trả lời cuối và nội dung các file `write_file` đã ghi.
- `scripts/gen_variants.py` sinh các biến thể mô tả. Thân skill và template của các biến thể nằm ở `variants/`.
- Tiêu chí đạt, tự đánh giá bằng code (`classify` trong `probe_agent.py`):
  - `nguong8`: chạy script với `--max-hours 8`, JSON có người quá tải, có `write_file`, nội dung nhắc Lan và 9, câu trả lời không nói "không có ai vượt".
  - `nguong9`, `para1`: chạy script với đúng ngưỡng của câu hỏi, JSON không có người quá tải.
  - `para2`: chạy với `--max-hours 7.5`, Lan nằm trong người quá tải. `para3`: chạy với `--max-hours 4` trên `workload-edge.csv`.
  - `thieu`: không chạy script, không `write_file`, câu trả lời hỏi ngưỡng.
  - `khongco`: script chạy và trả exit 1, không `write_file`.
  - `weekly`: nạp skill `weekly-report`, không nạp `csv-quality`, không chạy script.
  - `carry`, `carry2`: xem bảng các ca.
- Mẫu nhỏ (8 đến 20 lượt mỗi ca), model không cố định tham số sinh, nên chênh lệch một vài lượt có thể là ngẫu nhiên. Vì đã thử nhiều biến thể nên bản được chọn đã được đo lại bằng lượt chạy mới trên chính file đã áp dụng (hai dòng `xacnhan-final-*`).

## Các ca

| Ca | Câu hỏi hoặc kịch bản |
|---|---|
| `nguong8` | Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md. |
| `nguong9` | Kiểm tra data/workload.csv, người nào vượt 9 giờ? Ghi báo cáo vào output/workload-9.md. |
| `thieu` | Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải. |
| `khongco` | Kiểm tra data/khong-co.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/khong-co.md. |
| `para1` | Ai làm quá 10 giờ trong data/workload.csv? |
| `para2` | Cho tôi tổng giờ của từng người trong data/workload.csv, ngưỡng cảnh báo là 7.5 giờ. |
| `para3` | Rà soát file data/workload-edge.csv, ai vượt 4 giờ thì báo cho tôi, ghi kết quả ra output/edge.md. |
| `weekly` | Tạo báo cáo tuần từ data/weekly_notes.md, lưu vào output/weekly-report.md. (skill weekly-report phải được nạp, csv-quality không được chiếm chỗ) |
| `carry` | Nhiều lượt trong một cuộc trò chuyện: lượt 1 là ca ngưỡng 8, lượt 2 là ca thiếu ngưỡng. Đạt khi lượt 2 hỏi ngưỡng thay vì chạy script |
| `carry2` | Nhiều lượt: lượt 1 là ca ngưỡng 8, lượt 2 là "Còn nếu ngưỡng là 10 giờ thì sao?". Đạt khi lượt 2 chạy lại script với --max-hours 10 |

## Kết quả (số lượt đạt / số lượt chạy)

| Phiên bản | Khác biệt | Kết quả |
|---|---|---|
| `v2-hien-tai` | Skill v2: mô tả "Phân tích file CSV công việc ... Đọc skill này trước khi mở hay đọc file CSV", chưa đổi quy trình (mốc so sánh) | nguong8 1/8; nguong9 0/8; thieu 7/8; khongco 0/8 |
| `desc-A` | Mô tả bắt đầu bằng "BẮT BUỘC đọc skill này", nêu hậu quả nếu tự cộng | nguong8 6/8; nguong9 4/8; thieu 7/8; khongco 2/8 |
| `desc-B` | Mô tả B: mở đầu bằng đúng cách người dùng hỏi ("Kiểm tra file CSV công việc ..., người nào vượt N giờ, ai quá tải, tổng giờ theo người, rồi ghi báo cáo vào output/"), thêm "kể cả khi file có thể không tồn tại" và "Luôn gọi read_file đọc SKILL.md này trước khi gọi read_file hay bash với file CSV" | nguong8 8/8; nguong9 8/8; thieu 8/8; khongco 8/8 |
| `B-de` | Mô tả B, đo lại với 16 lượt mỗi ca | nguong8 16/16; nguong9 16/16; thieu 16/16; khongco 16/16 |
| `B-mo-rong` | Mô tả B, câu diễn đạt khác, weekly-report, nhiều lượt | para1 8/8; para2 8/8; para3 8/8; weekly 8/8; carry 0/8 |
| `B-carry2` | Mô tả B, ca ngưỡng nối tiếp | carry2 8/8 |
| `desc-C` | Mô tả ngắn, chỉ nêu từ khoá | nguong8 0/8; nguong9 0/8; thieu 4/8; khongco 0/8 |
| `desc-D` | Mô tả "BẮT BUỘC đọc skill này đầu tiên, trước mọi lệnh read_file hay bash" kết hợp danh sách tình huống | nguong8 8/8; nguong9 8/8; thieu 6/8; khongco 8/8 |
| `desc-B2` | B thêm câu "Ngưỡng giờ phải do người dùng nêu ..., chưa có thì hỏi lại" vào mô tả | nguong8 2/8; nguong9 5/8; thieu 8/8; khongco 0/8; carry 1/8; carry2 7/8 |
| `desc-B3` | B thêm câu dài về ngưỡng (không dùng ngưỡng lượt trước, không tự đặt 0) vào mô tả | nguong8 0/8; nguong9 7/8; thieu 8/8; khongco 2/8; carry 6/8; carry2 2/8 |
| `E1` | B + thân skill siết quy tắc ngưỡng ("tin nhắn mới nhất", "kể cả 0") | nguong8 8/8; nguong9 8/8; thieu 8/8; khongco 8/8; carry 0/8; carry2 8/8 |
| `E1-de` | E1, 16 lượt mỗi ca của đề | nguong8 16/16; nguong9 16/16; thieu 16/16; khongco 16/16 |
| `E1-mo-rong` | E1, câu diễn đạt khác và weekly | para1 4/8; para2 8/8; para3 8/8; weekly 8/8 |
| `E2` | E1 + "chỉ trả lời một câu hỏi xin ngưỡng và không gọi tool nào" | nguong8 8/8; nguong9 8/8; thieu 8/8; khongco 8/8; carry 2/8; carry2 6/8 |
| `E3` | E1 + câu "Không tự đặt giá trị ngưỡng" trong mô tả | nguong8 8/8; nguong9 8/8; thieu 6/8; khongco 7/8; carry 0/8; carry2 8/8 |
| `B-ap-dung-xac-nhan` | B áp dụng vào skill thật (quy trình cũ: skill, bash, write_file), đo lại | nguong8 12/12; nguong9 12/12; thieu 12/12; khongco 12/12; para1 12/12; weekly 12/12; carry2 12/12 |
| `F1` | B + quy trình đọc template trước khi chạy script | nguong8 10/10; nguong9 10/10; thieu 10/10; khongco 10/10; para1 6/10 |
| `F2` | B + quy trình gọi song song bash và read_file template | nguong8 10/10; nguong9 10/10; thieu 10/10; khongco 10/10; para1 10/10 |
| `F3` | F2 + "cả hai tool, thiếu một là sai" và "chỉ write_file sau khi đã nhận template" | nguong8 12/12; nguong9 12/12; thieu 12/12; khongco 12/12; para1 7/12 |
| `G1` | F2 + điều kiện tiên quyết cho write_file | nguong8 12/12; nguong9 12/12; thieu 12/12; khongco 12/12; para1 3/12; para2 12/12 |
| `G2` | F3 + bước 1 nói rõ "vượt N giờ", "quá N giờ" là đã có ngưỡng | nguong8 12/12; nguong9 12/12; thieu 12/12; khongco 12/12; para1 12/12; para2 12/12 |
| `T2-template` | G2 + report-template.md mới (hướng dẫn điều kiện chuyển sang dạng {...}) | nguong8 12/12; nguong9 12/12; thieu 11/12; khongco 12/12 |
| `xacnhan-G2-de` | G2 áp dụng vào skill thật, 20 lượt mỗi ca của đề | nguong8 20/20; nguong9 20/20; thieu 20/20; khongco 20/20 |
| `xacnhan-G2-mo-rong` | G2 áp dụng vào skill thật, câu diễn đạt khác, weekly, ngưỡng nối tiếp | para1 12/12; para2 12/12; para3 12/12; weekly 12/12; carry2 12/12 |
| `xacnhan-G2-carry` | G2 áp dụng vào skill thật, ca nhiều lượt thiếu ngưỡng | carry 0/12 |
| `xacnhan-final-de` | BẢN CHỐT (G2 + template mới) áp dụng vào skill thật, 20 lượt mỗi ca của đề | nguong8 20/20; nguong9 20/20; thieu 20/20; khongco 20/20 |
| `xacnhan-final-mo-rong` | BẢN CHỐT, câu diễn đạt khác, weekly, ngưỡng nối tiếp, 12 lượt mỗi ca | para1 12/12; para2 12/12; para3 12/12; weekly 12/12; carry2 12/12 |

## Nhận xét

- Cách viết **mô tả** quyết định agent có nạp skill hay không, vì mô tả là phần duy nhất agent luôn nhìn thấy. Mô tả bám sát cách người dùng hỏi (B) và có lệnh "đọc SKILL.md trước khi đọc file CSV" cho kết quả tốt nhất. Mô tả ngắn chỉ nêu từ khoá (C) hầu như không có tác dụng.
- Thêm quy tắc về ngưỡng vào mô tả (B2, B3, E3) làm các ca của đề kém đi, vì agent hỏi lại ngưỡng khi đã có hoặc bỏ qua script. Quy tắc ngưỡng nên nằm ở thân skill.
- Agent gần như không bao giờ đọc `report-template.md` khi chỉ được dặn ở bước cuối. Dặn đọc template **cùng lượt** với lệnh chạy script, kèm điều kiện "chỉ `write_file` sau khi đã nhận template" (F3, G2) làm tỉ lệ đọc template lên 100%.
- Một số thay đổi nhỏ trong quy trình (E1, F1, F3, G1) làm agent hỏi lại ngưỡng sai ở câu "Ai làm quá 10 giờ ..." (`para1`). G2 thêm câu "vượt N giờ", "quá N giờ" là đã có ngưỡng và giữ được `para1` 12/12.
- Hướng dẫn điều kiện trong template ("Nếu ... rỗng, ghi: ...") bị agent chép nguyên vào báo cáo ở 33/40 báo cáo (câu hướng dẫn mục Đánh giá ở 40/40). Chuyển sang dạng `{...}` giải quyết hoàn toàn (0/40 ở bản chốt).
- **Giới hạn còn lại**: kịch bản nhiều lượt trong cùng một cuộc trò chuyện, lượt sau không nêu ngưỡng (`carry`) chưa được giải quyết bằng cách chỉnh skill (0/8 đến 0/12). Agent dùng lại ngưỡng của lượt trước hoặc tự đặt `--max-hours 0`. Ca "thiếu ngưỡng" của đề mở cuộc trò chuyện mới nên không bị ảnh hưởng.
