# ChatGPT Batch Translator PRO - macOS

Ban macOS giu workflow nhu ban Windows:

- Upload anh len ChatGPT.
- Gui prompt `Dich`.
- Cho ban dich.
- Gui prompt `Tao anh voi ban dich`.
- Cho anh moi.
- Tai anh ve thu muc output.
- Giu `progress.csv`, retry, batch size, start from, va ten output dang `00073VN.png`.

## Diem rieng tren macOS

- Settings va profile ChatGPT mac dinh nam tai:

```text
~/Library/Application Support/ChatGPT Batch Translator/
```

- App khong dong goi profile ChatGPT ca nhan.
- Moi may Mac se co profile ChatGPT rieng va dang nhap lan dau rieng.
- Nut mo thu muc output dung lenh macOS `open`.
- Nut dung batch kill ca process group tren macOS de dong worker/Playwright gon hon.
- Chuc nang thu nho browser bang `pygetwindow/pywin32` chi chay tren Windows va duoc bo qua tren Mac.
- Giao dien co 3 che do theme: `Sang`, `Toi`, va `He thong`. Che do `He thong` tu doc Light/Dark Mode cua macOS va tu cap nhat khi he dieu hanh doi giao dien.
- Theme macOS dung bang mau va cac lop surface theo huong Liquid Glass/Tahoe: nen, sidebar va card co do tuong phan mem hon de tuong thich voi he giao dien moi. Tkinter khong ho tro NSVisualEffectView nen day la lop giao dien tuong thich, khong phai material blur goc cua macOS.

## Build file .app bang PyInstaller

Chay tren may Mac:

```bash
cd /path/to/chatgpt-batch-image-translator
python3 -m venv .venv
source .venv/bin/activate
chmod +x build_macos.sh
./build_macos.sh
```

Hoac double-click file:

```text
build_macos.command
```

Sau khi build xong, app nam o:

```text
dist/ChatGPT Batch Translator.app
```

Gui nguyen file `.app` nay cho nguoi dung.

## Playwright Chromium

Script build se cai Chromium vao trong app:

```text
ChatGPT Batch Translator.app/Contents/MacOS/ms-playwright
```

Khi chay app da dong goi, GUI tu set `PLAYWRIGHT_BROWSERS_PATH` den thu muc nay. Nguoi dung binh thuong khong can chay `playwright install chromium`.

Neu chay tu source de test:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 app.pyw
```

## Gatekeeper va quarantine

Neu app chua sign/notarize, macOS co the chan lan dau.

Cach mo cho nguoi dung:

1. Right click `ChatGPT Batch Translator.app`.
2. Chon `Open`.
3. Bam `Open` lan nua neu macOS hoi.
4. Dang nhap ChatGPT trong browser Playwright lan dau.

Neu app bi gan quarantine:

```bash
xattr -dr com.apple.quarantine "ChatGPT Batch Translator.app"
```

De phan phoi chuyen nghiep, nen sign va notarize bang Apple Developer account.

## Quyen thu muc tren macOS

Mac co the hoi quyen khi chon input/output trong:

- Downloads
- Desktop
- Documents

Neu bi loi doc/ghi file, vao:

```text
System Settings > Privacy & Security > Files and Folders
```

roi cap quyen cho app, hoac chon thu muc khac it bi macOS bao ve hon.

## py2app

Repo nay uu tien PyInstaller. Co the lam bang py2app, nhung van phai copy/cai Playwright Chromium va set `PLAYWRIGHT_BROWSERS_PATH`. De don gian, dung `build_macos.sh`.
