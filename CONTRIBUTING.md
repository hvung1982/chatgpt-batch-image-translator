# Contributing

## Tiếng Việt

Cảm ơn bạn đã quan tâm đến dự án. Đây là công cụ tự động hóa desktop cho workflow cá nhân, nên ưu tiên của repo là giữ app đơn giản, dễ build và tránh commit dữ liệu riêng tư.

Trước khi gửi issue hoặc pull request:

- Kiểm tra bạn đang dùng phiên bản mới nhất của branch phù hợp.
- Không đính kèm profile ChatGPT, cookie, ảnh riêng tư, hoặc file cấu hình cá nhân.
- Mô tả rõ hệ điều hành, Python version, cách chạy/build và lỗi gặp phải.
- Nếu báo lỗi UI ChatGPT, hãy nhớ rằng ChatGPT có thể thay đổi giao diện bất cứ lúc nào, làm automation cần cập nhật lại selector hoặc flow.

## Pull requests

- Giữ thay đổi nhỏ và tập trung.
- Không commit thư mục build, profile, ảnh input/output, hoặc `app_settings.json`.
- Nếu sửa luồng chính, hãy chạy kiểm tra cú pháp:

```powershell
python -m py_compile app.pyw run_chatgpt_batch.py
```

## English

Thanks for your interest in contributing. This is a desktop automation tool for a personal workflow, so the repository prioritizes keeping the app simple, buildable, and free of private data.

Before opening an issue or pull request:

- Make sure you are using the latest version of the relevant branch.
- Do not attach ChatGPT profiles, cookies, private images, or personal settings files.
- Clearly describe your operating system, Python version, run/build steps, and the error you saw.
- If the bug is related to the ChatGPT web UI, remember that ChatGPT can change its interface at any time, so automation selectors or flow may need updates.

## Pull Requests

- Keep changes small and focused.
- Do not commit build folders, profiles, input/output images, or `app_settings.json`.
- If you change the main flow, run a syntax check:

```powershell
python -m py_compile app.pyw run_chatgpt_batch.py
```
