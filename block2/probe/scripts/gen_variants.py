"""Sinh các biến thể SKILL.md chỉ khác dòng description (phần model luôn nhìn thấy). argv: <SKILL.md gốc> <thư mục ra>."""

import re
import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
src = Path(sys.argv[1]).read_text(encoding="utf-8")
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

DESCRIPTIONS = {
    "A": (
        "BẮT BUỘC đọc skill này trước khi mở file CSV công việc (cột task_id, owner, hours) hoặc trả lời về giờ làm việc của từng người. "
        "Dùng khi người dùng muốn kiểm tra file CSV công việc, hỏi người nào vượt N giờ, ai quá tải, tổng giờ theo người, hoặc yêu cầu ghi báo cáo từ file đó. "
        "Tự đọc CSV rồi cộng sẽ sai vì file có dòng lỗi và task_id trùng, chỉ script trong skill mới cho kết quả đúng."
    ),
    "B": (
        "Kiểm tra file CSV công việc (cột task_id, owner, hours), người nào vượt N giờ, ai quá tải, tổng giờ theo người, rồi ghi báo cáo vào output/. "
        "Dùng cho mọi yêu cầu kiểm tra hoặc phân tích file CSV công việc, kể cả khi file có thể không tồn tại. "
        "Luôn gọi read_file đọc SKILL.md này trước khi gọi read_file hay bash với file CSV."
    ),
    "B2": (
        "Kiểm tra file CSV công việc (cột task_id, owner, hours), người nào vượt N giờ, ai quá tải, tổng giờ theo người, rồi ghi báo cáo vào output/. "
        "Dùng cho mọi yêu cầu kiểm tra hoặc phân tích file CSV công việc, kể cả khi file có thể không tồn tại. "
        "Luôn gọi read_file đọc SKILL.md này trước khi gọi read_file hay bash với file CSV. "
        "Ngưỡng giờ phải do người dùng nêu trong yêu cầu hiện tại, chưa có thì hỏi lại và không tự đặt ngưỡng."
    ),
    "B3": (
        "Kiểm tra file CSV công việc (cột task_id, owner, hours), người nào vượt N giờ, ai quá tải, tổng giờ theo người, rồi ghi báo cáo vào output/. "
        "Dùng cho mọi yêu cầu kiểm tra hoặc phân tích file CSV công việc, kể cả khi file có thể không tồn tại. "
        "Luôn gọi read_file đọc SKILL.md này trước khi gọi read_file hay bash với file CSV. "
        "Mỗi yêu cầu phải tự nêu ngưỡng giờ, không dùng ngưỡng của lượt trước hay cuộc trò chuyện cũ. Yêu cầu nào thiếu ngưỡng thì hỏi lại, không tự đặt ngưỡng như 0."
    ),
    "C": (
        "Dùng ngay khi yêu cầu nhắc đến file CSV công việc (task_id, owner, hours), giờ làm, vượt N giờ, quá tải hoặc báo cáo. "
        "Phải đọc SKILL.md này trước khi đọc file CSV."
    ),
    "D": (
        "BẮT BUỘC đọc skill này đầu tiên, trước mọi lệnh read_file hay bash trên file CSV công việc (task_id, owner, hours). "
        "Dùng cho mọi yêu cầu kiểm tra file CSV công việc, người nào vượt N giờ, ai quá tải, tổng giờ theo người, ghi báo cáo vào output/, kể cả khi file có thể không tồn tại. "
        "Tự đọc CSV rồi cộng sẽ sai vì file có dòng lỗi và task_id trùng."
    ),
}

for key, desc in DESCRIPTIONS.items():
    assert ": " not in desc and " #" not in desc, f"{key}: description có ': ' hoặc ' #', làm hỏng YAML"
    text = re.sub(r"^description: .*$", f"description: {desc}", src, count=1, flags=re.M)
    meta = yaml.safe_load(text.split("---", 2)[1])
    assert meta["description"] == desc and meta["name"] == "csv-quality", key
    assert not re.search(r"(^|[^-A-Za-z0-9.])8([^0-9]|$)", desc.replace("utf-8", "")), f"{key}: có số 8"
    (out / f"{key}.md").write_text(text, encoding="utf-8")
    print(f"{key}: {len(desc)} ký tự, YAML hợp lệ")
