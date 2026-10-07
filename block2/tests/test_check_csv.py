"""csv-quality script: thống kê fixture, tổng giờ theo owner, dòng bị loại, ngưỡng --max-hours,
lỗi input/schema/parse exit 1, lỗi tham số exit khác 0, lỗi dữ liệu exit 0."""

import json
import subprocess
import sys

import pytest

import paths

SCRIPT = paths.FIXTURES_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"
WORKLOAD = paths.FIXTURES_DIR / "data" / "workload.csv"
WORKLOAD_EDGE = paths.FIXTURES_DIR / "data" / "workload-edge.csv"


def run(path, max_hours="10"):
    command = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        command += ["--max-hours", max_hours]
    return subprocess.run(command, capture_output=True, text=True, timeout=10)


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def excluded(data):
    return [(row["line"], row["task_id"], row["reasons"]) for row in data["excluded_rows"]]


def test_fixture_statistics():
    result = run(paths.FIXTURES_DIR / "data" / "tasks.csv", max_hours="4")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert data["max_hours"] == 4
    assert data["hours_by_owner"] == {"An": 5, "Lan": 4, "Minh": 3}
    assert data["overloaded_owners"] == [{"owner": "An", "total_hours": 5}]  # Lan bằng ngưỡng 4: không quá tải
    assert excluded(data) == [(4, "T03", ["missing_owner"]), (5, "T04", ["invalid_hours"]), (6, "T02", ["duplicate_id"])]


@pytest.mark.parametrize(("max_hours", "overloaded"), [("8", [{"owner": "Lan", "total_hours": 9}]), ("9", [])])
def test_workload_totals_and_overloaded_owners(max_hours, overloaded):
    result = run(WORKLOAD, max_hours=max_hours)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Lan": 9, "Minh": 3}  # T02 ở dòng 6 không bị cộng lần hai
    assert data["overloaded_owners"] == overloaded
    assert excluded(data) == [(5, "T04", ["invalid_hours"]), (6, "T02", ["duplicate_id"]), (7, "T05", ["missing_owner"])]
    # thống kê chất lượng vẫn tính trên mọi dòng dữ liệu
    assert (data["row_count"], data["missing_owner_count"], data["invalid_hours_count"], data["duplicate_ids"]) == (6, 1, 1, ["T02"])


def test_first_occurrence_with_invalid_hours_still_blocks_later_duplicate():
    """E01 lần đầu có hours lỗi: lần sau vẫn bị loại vì trùng ID, không thay bằng lần hợp lệ đầu tiên."""
    result = run(WORKLOAD_EDGE, max_hours="0")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Minh": 0}  # không cộng 5 giờ cho Lan
    assert data["overloaded_owners"] == []  # 0 bằng ngưỡng 0: không quá tải
    assert excluded(data) == [(2, "E01", ["invalid_hours"]), (3, "E01", ["duplicate_id"])]


def test_each_excluded_row_listed_once_with_all_reasons_in_order(tmp_path):
    data = json.loads(run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\n,,-1\nT01,Lan,x,extra\n")).stdout)
    assert excluded(data) == [
        (3, None, ["missing_task_id", "missing_owner", "invalid_hours"]),
        (4, "T01", ["wrong_field_count", "duplicate_id", "invalid_hours"]),
    ]
    assert data["hours_by_owner"] == {"Lan": 4}


def test_values_are_trimmed_and_owner_case_is_kept(tmp_path):
    text = "task_id,owner,hours\n T01 , Lan , 2 \nT02,lan,3\nT01,Lan,4\n\nT03,Lan,0\n"
    data = json.loads(run(write_csv(tmp_path, text)).stdout)
    assert data["row_count"] == 4  # dòng trống bị bỏ qua
    assert data["hours_by_owner"] == {"Lan": 2, "lan": 3}
    assert excluded(data) == [(4, "T01", ["duplicate_id"])]


def test_total_equal_to_decimal_threshold_is_not_overloaded(tmp_path):
    """0.1 + 0.2 bằng đúng ngưỡng 0.3; sai số float không được đẩy thành quá tải."""
    data = json.loads(run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,0.1\nT02,Lan,0.2\n"), max_hours="0.3").stdout)
    assert data["hours_by_owner"] == {"Lan": 0.3}
    assert data["overloaded_owners"] == []


def test_missing_max_hours_exit_non_zero():
    result = run(WORKLOAD, max_hours=None)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "--max-hours" in result.stderr


@pytest.mark.parametrize("max_hours", ["-1", "abc", "nan", "inf", ""])
def test_invalid_max_hours_exit_non_zero(max_hours):
    result = run(WORKLOAD, max_hours=max_hours)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "--max-hours" in result.stderr


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n")).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2
    assert excluded(data) == [(2, "T01", ["invalid_hours"])]


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["issues"] == [] and data["excluded_rows"] == []
    assert data["hours_by_owner"] == {"Lan": 4, "Minh": 2.5}


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"))
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'))
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


@pytest.mark.parametrize("name", ["tasks.csv", "workload.csv", "workload-edge.csv"])
def test_script_does_not_modify_input(name):
    source = paths.FIXTURES_DIR / "data" / name
    before = source.read_bytes()
    run(source)
    assert source.read_bytes() == before
