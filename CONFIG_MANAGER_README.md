# 🔧 Config Manager - Quản lý Cấu hình Tool Tạo Folder

## 📋 Tổng quan
Config Manager là chương trình quản lý cấu hình cho Tool Tạo Folder, cho phép bạn:
- Quản lý mã niêm phong
- Cấu hình API Gemini
- Quản lý danh sách đại lý
- Quản lý danh sách tỉnh thành

## 🚀 Cách sử dụng

### 1. Chạy chương trình
```bash
python config_manager.py
```

### 2. Build thành file exe
```bash
pyinstaller config_manager.spec
```

## 📁 Các tab chức năng

### 🏷️ Tab Mã Niêm Phong
- **Thêm**: Nhập mã niêm phong (format: 1 chữ + 6 số, ví dụ: A123456)
- **Sửa**: Double-click vào mã trong danh sách để sửa
- **Xóa**: Chọn mã và nhấn "🗑️ Xóa"
- **Import**: Import từ file .txt

**Validation:**
- Mã niêm phong phải có đúng 7 ký tự
- Ký tự đầu phải là chữ cái
- 6 ký tự sau phải là số

### 🤖 Tab API Gemini
- **API Key**: Nhập API key của Google Gemini
- **Model**: Chọn model AI (gemini-2.5-flash-lite, gemini-1.5-flash, gemini-1.5-pro)
- **Lưu**: Lưu cấu hình và cập nhật vào create_folder.py
- **Test**: Kiểm tra API có hoạt động không
- **Hiện/Ẩn**: Toggle hiển thị API key

### 🏢 Tab Đại Lý
- **Thêm**: Nhập tên đại lý và mã rút gọn
- **Sửa**: Double-click vào đại lý trong danh sách
- **Xóa**: Chọn đại lý và nhấn "🗑️ Xóa"

**Format file dai_ly_config.txt:**
```
Tên đại lý:Mã rút gọn
Ví dụ: Công ty ABC:ABC
```

### 🏛️ Tab Tỉnh Thành
- **Thêm**: Nhập tên tỉnh và mã tỉnh
- **Sửa**: Double-click vào tỉnh trong danh sách
- **Xóa**: Chọn tỉnh và nhấn "🗑️ Xóa"

**Format file ma_tinh_config.txt:**
```
Tên tỉnh:Mã tỉnh
Ví dụ: Kiên Giang:KG
```

## 📂 Các file cấu hình

### 1. niem_phong.txt
Chứa danh sách mã niêm phong hợp lệ:
```
A123456
B234567
C345678
```

### 2. api_config.json
Cấu hình API Gemini:
```json
{
  "api_key": "your_api_key_here",
  "model": "gemini-2.5-flash-lite",
  "updated_at": "2025-01-27T10:30:00"
}
```

### 3. dai_ly_config.txt
Danh sách đại lý:
```
Công ty ABC:ABC
Công ty XYZ:XYZ
```

### 4. ma_tinh_config.txt
Danh sách tỉnh thành:
```
Kiên Giang:KG
Bến Tre:BT
Đà Nẵng:ĐNa
```

## 🔄 Tích hợp với create_folder.py

Config Manager tự động cập nhật:
- **API Key**: Thay đổi trong create_folder.py
- **Model**: Cập nhật model AI được sử dụng
- **Mã niêm phong**: Đồng bộ với niem_phong.txt
- **Đại lý**: Đồng bộ với dai_ly_config.txt
- **Tỉnh thành**: Đồng bộ với ma_tinh_config.txt

## ⚠️ Lưu ý quan trọng

1. **Backup**: Luôn backup các file cấu hình trước khi thay đổi
2. **API Key**: Giữ bí mật API key, không chia sẻ
3. **Format**: Tuân thủ đúng format của từng loại dữ liệu
4. **Validation**: Chương trình sẽ kiểm tra tính hợp lệ của dữ liệu

## 🛠️ Troubleshooting

### Lỗi API không hoạt động
1. Kiểm tra API key có đúng không
2. Kiểm tra kết nối internet
3. Sử dụng chức năng "Test API"

### Lỗi import file
1. Kiểm tra format file có đúng không
2. Kiểm tra encoding (UTF-8)
3. Kiểm tra quyền đọc file

### Lỗi validation
1. Kiểm tra format dữ liệu
2. Kiểm tra độ dài ký tự
3. Kiểm tra ký tự đặc biệt

## 📞 Hỗ trợ
Nếu gặp vấn đề, hãy kiểm tra:
1. File log (nếu có)
2. Console output
3. Format dữ liệu
4. Quyền truy cập file
