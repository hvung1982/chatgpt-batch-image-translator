# Release Checklist

## Tiếng Việt

Dùng checklist này trước khi tạo bản phát hành công khai.

- [ ] Pull code mới nhất từ branch cần release.
- [ ] Kiểm tra `git status` sạch trước khi build.
- [ ] Không có thư mục/file riêng tư trong bản release:
  - `chatgpt_auto_profile`
  - profile Playwright/macOS user data
  - `images`
  - `images_vn`
  - `app_settings.json`
  - `progress.csv`
  - ảnh sách/truyện riêng
- [ ] Build Windows bằng `build_portable.ps1` trên Windows.
- [ ] Build macOS bằng `build_macos.sh` trên macOS.
- [ ] Chạy thử app build sạch trên một profile mới.
- [ ] Đăng nhập ChatGPT lần đầu trong browser app mở ra.
- [ ] Test với vài ảnh mẫu được phép chia sẻ.
- [ ] Zip cả thư mục portable Windows, không zip riêng file `.exe`.
- [ ] Với macOS, cân nhắc sign/notarize nếu phát hành rộng.
- [ ] Ghi rõ trong release note đây là công cụ unofficial và người dùng chịu trách nhiệm về quyền sử dụng nội dung.

## English

Use this checklist before publishing a public release.

- [ ] Pull the latest code from the branch being released.
- [ ] Make sure `git status` is clean before building.
- [ ] Do not include private files/folders in the release:
  - `chatgpt_auto_profile`
  - Playwright/macOS user profile data
  - `images`
  - `images_vn`
  - `app_settings.json`
  - `progress.csv`
  - private book/comic images
- [ ] Build Windows with `build_portable.ps1` on Windows.
- [ ] Build macOS with `build_macos.sh` on macOS.
- [ ] Test the built app with a fresh profile.
- [ ] Sign in to ChatGPT through the browser opened by the app.
- [ ] Test with a few sample images you have permission to share.
- [ ] Zip the whole Windows portable folder, not only the `.exe` file.
- [ ] For macOS, consider signing/notarizing the app for broader distribution.
- [ ] Clearly state in the release notes that this is an unofficial tool and users are responsible for rights to the content they process.
