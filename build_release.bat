@echo off
chcp 65001 >nul
echo ========================================
echo    BUILD TOOL TẠO FOLDER v1.3
echo ========================================
echo.

echo [1/5] Đang dọn dẹp thư mục build cũ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ Đã dọn dẹp xong
echo.

echo [2/5] Đang build create_folder.exe...
pyinstaller create_folder.spec --clean --noconfirm
if errorlevel 1 (
    echo ❌ Lỗi khi build create_folder.exe
    pause
    exit /b 1
)
echo ✓ Đã build create_folder.exe thành công
echo.

echo [3/5] Đang build config_manager.exe...
pyinstaller config_manager.spec --clean --noconfirm
if errorlevel 1 (
    echo ❌ Lỗi khi build config_manager.exe
    pause
    exit /b 1
)
echo ✓ Đã build config_manager.exe thành công
echo.

echo [4/5] Đang tạo thư mục release...
if exist Tool_Tao_Folder_v1.3 rmdir /s /q Tool_Tao_Folder_v1.3
mkdir Tool_Tao_Folder_v1.3
echo ✓ Đã tạo thư mục
echo.

echo [5/5] Đang copy files vào thư mục release...
copy dist\create_folder.exe Tool_Tao_Folder_v1.3\ >nul
copy dist\config_manager.exe Tool_Tao_Folder_v1.3\ >nul
copy iconZ.ico Tool_Tao_Folder_v1.3\ >nul
copy HƯỚNG_DẪN_SỬ_DỤNG.txt Tool_Tao_Folder_v1.3\ >nul
copy api_config.json Tool_Tao_Folder_v1.3\ >nul
copy dai_ly_config.txt Tool_Tao_Folder_v1.3\ >nul
copy ma_tinh_config.txt Tool_Tao_Folder_v1.3\ >nul
copy niem_phong.txt Tool_Tao_Folder_v1.3\ >nul
copy input_folder_config.txt Tool_Tao_Folder_v1.3\ >nul
copy output_folder_config.txt Tool_Tao_Folder_v1.3\ >nul
echo ✓ Đã copy files xong
echo.

echo ========================================
echo    BUILD HOÀN TẤT!
echo ========================================
echo.
echo Thư mục release: Tool_Tao_Folder_v1.3\
echo.
echo Các file đã được tạo:
echo   - create_folder.exe
echo   - config_manager.exe
echo   - iconZ.ico
echo   - HƯỚNG_DẪN_SỬ_DỤNG.txt
echo   - api_config.json
echo   - Các file config khác
echo.
pause

