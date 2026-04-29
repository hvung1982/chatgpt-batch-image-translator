import os
import csv
from pathlib import Path

DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", r"D:\images_vn")
PROGRESS_FILE = os.path.join(DOWNLOAD_FOLDER, "progress.csv")
FAILED_LIST_FILE = os.path.join(DOWNLOAD_FOLDER, "failed_list.csv")


def main():
    if not os.path.exists(PROGRESS_FILE):
        print(f"Không thấy progress.csv: {PROGRESS_FILE}")
        return

    failed_rows = []

    with open(PROGRESS_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            status = (row.get("status") or "").strip().lower()

            if status in ["fail", "failed", "manual", "error"]:
                failed_rows.append(row)

    if not failed_rows:
        print("Không có ảnh lỗi.")
        return

    fieldnames = ["index", "file", "status", "note"]

    with open(FAILED_LIST_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in failed_rows:
            writer.writerow({
                "index": row.get("index", ""),
                "file": row.get("file", ""),
                "status": row.get("status", ""),
                "note": row.get("note", "")
            })

    print(f"Đã xuất danh sách lỗi: {FAILED_LIST_FILE}")
    print(f"Số ảnh lỗi: {len(failed_rows)}")


if __name__ == "__main__":
    main()