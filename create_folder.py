
import tkinter as tk
from tkcalendar import Calendar, DateEntry
from ttkwidgets.autocomplete import AutocompleteCombobox, AutocompleteEntry  # Import AutocompleteEntry
from tkinter import scrolledtext, filedialog, messagebox
import os
import shutil
import google.generativeai as genai
import json
import threading
from collections import Counter
from PIL import Image
import subprocess
import sys


CONFIG_FILE = "folder_path_config.txt"
INPUT_FOLDER_CONFIG = "input_folder_config.txt"
OUTPUT_FOLDER_CONFIG = "output_folder_config.txt"

# Cấu hình Google Gemini AI
def load_api_config():
    """Load cấu hình API từ file JSON hoặc báo lỗi"""
    try:
        with open("api_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            api_key = config.get("api_key", "")
            model = config.get("model", "gemini-2.5-flash-lite")
            
            if not api_key:
                print("❌ Lỗi: Chưa cấu hình API Key!")
                print("💡 Hướng dẫn: Chạy config_manager.py để cấu hình API Key")
                return None, None
            
            return api_key, model
    except FileNotFoundError:
        print("❌ Lỗi: Không tìm thấy file api_config.json!")
        print("💡 Hướng dẫn: Chạy config_manager.py để tạo file cấu hình API")
        return None, None

GOOGLE_API_KEY, MODEL_NAME = load_api_config()
if GOOGLE_API_KEY and MODEL_NAME:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
        AI_AVAILABLE = True
        print("✅ AI đã sẵn sàng!")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo AI: {e}")
        AI_AVAILABLE = False
else:
    AI_AVAILABLE = False
    print("❌ AI không khả dụng - Cần cấu hình API Key")




def save_input_folder_path(path):
    with open(INPUT_FOLDER_CONFIG, "w") as f:
        f.write(path)

def save_output_folder_path(path):
    with open(OUTPUT_FOLDER_CONFIG, "w") as f:
        f.write(path)

def load_input_folder_path():
    try:
        with open(INPUT_FOLDER_CONFIG, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def load_output_folder_path():
    try:
        with open(OUTPUT_FOLDER_CONFIG, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def browse_input_folder():
    folder_path = filedialog.askdirectory(title="Chọn folder input")
    if folder_path:
        input_folder_entry.delete(0, tk.END)
        input_folder_entry.insert(0, folder_path)
        save_input_folder_path(folder_path)

def browse_output_folder():
    folder_path = filedialog.askdirectory(title="Chọn folder output")
    if folder_path:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, folder_path)
        save_output_folder_path(folder_path)

# Tạo mapping từ mã tỉnh sang tên tỉnh
def create_tinh_mapping():
    """Tạo mapping từ mã tỉnh sang tên tỉnh từ file config"""
    mapping = {}
    try:
        with open("ma_tinh_config.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    tinh_name, tinh_code = line.strip().split(":")
                    mapping[tinh_code.strip()] = tinh_name.strip()
    except FileNotFoundError:
        print("Không tìm thấy file ma_tinh_config.txt")
    return mapping

# Tạo prompt với thông tin mapping tỉnh
def create_master_prompt():
    """Tạo prompt với thông tin mapping tỉnh"""
    tinh_mapping = create_tinh_mapping()
    
    # Tạo danh sách mapping rõ ràng hơn
    mapping_list = []
    for code, name in tinh_mapping.items():
        mapping_list.append(f"{code} = {name}")
    
    mapping_text = "\n".join(mapping_list)
    
    return f"""
Phân tích hình ảnh này và trích xuất các thông tin sau đây.
Trả lời bằng một đối tượng JSON hợp lệ duy nhất.
Các key của JSON phải là: "ma_niem_phong", "ma_tau", "ngay_chup", "ma_thiet_bi".

- "ma_niem_phong": Tìm mã niêm phong, ví dụ "SEAL A 123456", "K 678901", hoặc "Z012345". Chỉ lấy phần gồm 1 ký tự chữ và 6 số, ví dụ "A123456", "K678901", hoặc "Z012345". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_tau": Tìm mã tàu đầy đủ (có cả chữ cái và số), ví dụ "KG 95596", "BT 97793", "SG 12345", "BĐ 12345", "ĐNa 67890", "TTH 11111". Giữ nguyên format đầy đủ với khoảng trắng. Nếu không tìm thấy, trả về "Không tìm thấy".
- "ngay_chup": Tìm ngày tháng trên ảnh, ví dụ "05/08/2025". Chuyển thành định dạng 6 số "DDMMYY", ví dụ "050825". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_thiet_bi": Tìm mã thiết bị, thường bắt đầu bằng BTK, ví dụ "BTK123456". Chỉ lấy 6 số cuối, ví dụ "123456". QUAN TRỌNG: Mã thiết bị phải là đúng 6 chữ số. Nếu không đúng định dạng hoặc không đủ 6 số, trả về "Không tìm thấy".

Ví dụ: 
- Mã thiết bị: "BTK123456" → lấy "123456" (6 số)
- Mã thiết bị: "BTK12345" → "Không tìm thấy" (chỉ có 5 số)
- Mã thiết bị: "BTK1234567" → lấy "123456" (6 số đầu)
- Mã tàu: "KG 95596" → trả về "KG 95596"
- Mã tàu: "BĐ 12345" → trả về "BĐ 12345"
- Mã tàu: "ĐNa 67890" → trả về "ĐNa 67890"

Nếu không xác định được, trả về "Không tìm thấy".

Quan trọng: Chỉ trả về đối tượng JSON, không thêm bất kỳ văn bản giải thích nào khác.
"""

def process_image_with_ai(image_path):
    """Phân tích một ảnh bằng AI và trả về thông tin"""
    try:
        img = Image.open(image_path)
        # Tạo prompt mới mỗi lần để đảm bảo có thông tin mapping mới nhất
        current_prompt = create_master_prompt()
        response = model.generate_content([current_prompt, img])
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_text)
        # Lưu raw response để debug
        data['raw_response'] = response.text
        return data
    except json.JSONDecodeError:
        return {"error": "AI không trả về JSON hợp lệ", "raw_response": response.text}
    except Exception as e:
        return {"error": f"Lỗi: {e}"}

def analyze_images_with_ai():
    """Phân tích tất cả ảnh trong folder input bằng AI"""
    if not AI_AVAILABLE:
        messagebox.showerror("Lỗi", "❌ AI không khả dụng!\n\n💡 Cần cấu hình API Key:\n1. Chạy config_manager.py\n2. Vào tab 'API Gemini'\n3. Nhập API Key và nhấn 'Lưu'")
        return
    
    input_path = input_folder_entry.get().strip()
    if not input_path or not os.path.isdir(input_path):
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn folder input chứa ảnh để phân tích.")
        return
    
    # Tìm tất cả ảnh trong folder input
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    image_paths = []
    
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.lower().endswith(image_extensions):
                image_paths.append(os.path.join(root, file))
    
    if not image_paths:
        messagebox.showwarning("Cảnh báo", "Không tìm thấy ảnh nào trong folder input.")
        return
    
    # Hiển thị loading
    label_result.config(text=f"Đang phân tích {len(image_paths)} ảnh bằng AI...")
    button_analyze.config(state="disabled")
    window.update()
    
    # Thông báo bắt đầu phân tích
    print(f"\n🚀 BẮT ĐẦU PHÂN TÍCH {len(image_paths)} ẢNH BẰNG AI...")
    print(f"📁 Folder: {input_path}")
    print("-" * 60)
    
    def analyze_thread():
        try:
            all_results = []
            for i, image_path in enumerate(image_paths, 1):
                print(f"🔄 Đang xử lý ảnh {i}/{len(image_paths)}: {os.path.basename(image_path)}")
                result = process_image_with_ai(image_path)
                result['file_name'] = os.path.basename(image_path)
                all_results.append(result)
                print(f"✅ Hoàn thành ảnh {i}/{len(image_paths)}")
            
            print(f"\n🎉 HOÀN TẤT PHÂN TÍCH {len(image_paths)} ẢNH!")
            print("-" * 60)
            
            # Phân tích kết quả
            niem_phong_counts = Counter()
            tau_counts = Counter()
            ngay_chup_counts = Counter()
            ma_thiet_bi_counts = Counter()
            tinh_counts = Counter()
            error_count = 0
            
            for result in all_results:
                if 'error' in result and result['error']:
                    error_count += 1
                    continue
                
                ma_niem_phong = result.get('ma_niem_phong', '').strip()
                ma_tau_full = result.get('ma_tau', '').strip()  # Mã tàu đầy đủ
                ngay_chup = result.get('ngay_chup', '').strip()
                ma_thiet_bi = result.get('ma_thiet_bi', '').strip()
                
                # Tự động suy ra tỉnh từ mã tàu đầy đủ
                tinh = "Không tìm thấy"
                ma_tau_so = "Không tìm thấy"
                
                if ma_tau_full and ma_tau_full.lower() != 'không tìm thấy':
                    # Tách mã tàu đầy đủ thành chữ cái và số
                    import re
                    ma_tau_pattern = r'([A-Z]{2,3})[-\s]*(\d{5})'
                    ma_tau_match = re.search(ma_tau_pattern, ma_tau_full)
                    
                    if ma_tau_match:
                        tinh_code = ma_tau_match.group(1)  # Chữ cái tỉnh
                        ma_tau_so = ma_tau_match.group(2)  # Số tàu
                        
                        # Tìm tỉnh từ mapping
                        tinh_mapping = create_tinh_mapping()
                        for code, name in tinh_mapping.items():
                            if code == tinh_code:
                                tinh = name
                                break
                        
                        # Lưu thông tin vào result để debug
                        result['tinh_code'] = tinh_code
                        result['ma_tau_so'] = ma_tau_so
                        result['tinh'] = tinh
                    else:
                        # Nếu không match pattern, giữ nguyên
                        ma_tau_so = ma_tau_full
                        result['ma_tau_so'] = ma_tau_so
                        result['tinh'] = tinh
                
                if ma_niem_phong and ma_niem_phong.lower() != 'không tìm thấy':
                    niem_phong_counts[ma_niem_phong] += 1
                if ma_tau_so and ma_tau_so.lower() != 'không tìm thấy':
                    tau_counts[ma_tau_so] += 1
                if ngay_chup and ngay_chup.lower() != 'không tìm thấy':
                    ngay_chup_counts[ngay_chup] += 1
                if ma_thiet_bi and ma_thiet_bi.lower() != 'không tìm thấy':
                    ma_thiet_bi_counts[ma_thiet_bi] += 1
                if tinh and tinh.lower() != 'không tìm thấy':
                    tinh_counts[tinh] += 1
            
            # Tìm giá trị phổ biến nhất
            final_niem_phong = niem_phong_counts.most_common(1)[0][0] if niem_phong_counts else ""
            final_tau = tau_counts.most_common(1)[0][0] if tau_counts else ""
            final_ngay_chup = ngay_chup_counts.most_common(1)[0][0] if ngay_chup_counts else ""
            final_thiet_bi = ma_thiet_bi_counts.most_common(1)[0][0] if ma_thiet_bi_counts else ""
            final_tinh = tinh_counts.most_common(1)[0][0] if tinh_counts else ""
            
            # Export chi tiết kết quả từng ảnh ra console
            export_detailed_results_to_console(all_results)
            
            # Cập nhật giao diện
            window.after(0, lambda: update_ui_with_ai_results(
                final_niem_phong, final_tau, final_ngay_chup, final_thiet_bi, final_tinh,
                len(all_results), error_count
            ))
            
        except Exception as e:
            window.after(0, lambda: show_ai_error(str(e)))
    
    # Chạy phân tích trong thread riêng
    threading.Thread(target=analyze_thread, daemon=True).start()

def update_ui_with_ai_results(ma_niem_phong, ma_tau, ngay_chup, ma_thiet_bi, tinh, total_images, error_count):
    """Cập nhật giao diện với kết quả AI"""
    # Tự động điền thông tin
    if ma_niem_phong:
        seal_code_num.delete(0, tk.END)
        seal_code_num.insert(0, ma_niem_phong)
    
    if ma_tau:
        tau_num.delete(0, tk.END)
        tau_num.insert(0, ma_tau)
    
    if ma_thiet_bi:
        device_code_num.delete(0, tk.END)
        device_code_num.insert(0, ma_thiet_bi)
    
    if tinh:
        # Tìm tỉnh trong danh sách và tự động chọn
        found = False
        for key, value in tinh_thanh_vt.items():
            if value == tinh or key == tinh:
                combobox_tinh.set(key)
                found = True
                break
        
        # Nếu không tìm thấy, thử tìm kiếm gần đúng
        if not found:
            for key, value in tinh_thanh_vt.items():
                if tinh.lower() in key.lower() or tinh.lower() in value.lower():
                    combobox_tinh.set(key)
                    found = True
                    break
    
    if ngay_chup and len(ngay_chup) == 6:
        try:
            # Chuyển đổi DDMMYY thành datetime object
            day = int(ngay_chup[:2])
            month = int(ngay_chup[2:4])
            year = 2000 + int(ngay_chup[4:6])
            from datetime import datetime
            cal.set_date(datetime(year, month, day))
        except:
            pass
    
    # Hiển thị kết quả
    success_count = total_images - error_count
    result_text = f"✅ Phân tích hoàn tất! {success_count}/{total_images} ảnh thành công"
    if error_count > 0:
        result_text += f" ({error_count} lỗi)"
    
    # Thêm thông tin tỉnh được nhận diện
    if tinh:
        result_text += f"\n📍 Tỉnh: {tinh}"
        # Debug info cho console
        print(f"🔍 Debug - Tỉnh được nhận diện: '{tinh}'")
        if tinh != "Không tìm thấy":
            print(f"✅ Tỉnh đã được tự động chọn trong combobox")
        else:
            print(f"⚠️  Không thể tìm thấy tỉnh tương ứng")
    
    label_result.config(text=result_text)
    
    # Export kết quả ra console
    export_results_to_console(ma_niem_phong, ma_tau, ngay_chup, ma_thiet_bi, tinh, total_images, error_count)
    
    # Bật lại nút
    button_analyze.config(state="normal")

def export_detailed_results_to_console(all_results):
    """Export chi tiết kết quả từng ảnh ra console"""
    print("\n" + "="*80)
    print("📸 CHI TIẾT KẾT QUẢ TỪNG ẢNH")
    print("="*80)
    
    for i, result in enumerate(all_results, 1):
        print(f"\n🖼️  Ảnh {i}: {result.get('file_name', 'Unknown')}")
        print("-" * 50)
        
        if 'error' in result and result['error']:
            print(f"❌ Lỗi: {result['error']}")
            if 'raw_response' in result:
                print(f"📝 Response gốc: {result['raw_response'][:100]}...")
        else:
            print(f"  🔒 Mã niêm phong: {result.get('ma_niem_phong', 'Không tìm thấy')}")
            print(f"  🚢 Số tàu: {result.get('ma_tau_so', 'Không tìm thấy')}")
            print(f"  📅 Ngày chụp: {result.get('ngay_chup', 'Không tìm thấy')}")
            print(f"  🔧 Mã thiết bị: {result.get('ma_thiet_bi', 'Không tìm thấy')}")
            
            # Chi tiết về việc suy ra tỉnh
            tinh = result.get('tinh', 'Không tìm thấy')
            print(f"  📍 Tỉnh: {tinh}")
            
            # Hiển thị thông tin chi tiết về mã tàu và tỉnh
            if 'raw_response' in result:
                raw_response = result['raw_response']
                print(f"     📝 Raw response từ AI:")
                print(f"        {raw_response[:200]}...")
                
                # Lấy thông tin đã được xử lý
                ma_tau_full = result.get('ma_tau', '')
                tinh_code = result.get('tinh_code', '')
                ma_tau_so = result.get('ma_tau_so', '')
                
                print(f"     🚢 Mã tàu đầy đủ từ AI: '{ma_tau_full}'")
                
                if tinh_code and ma_tau_so:
                    print(f"     🔍 Phân tích mã tàu '{ma_tau_full}':")
                    print(f"        📍 Chữ cái tỉnh: '{tinh_code}'")
                    print(f"        🔢 Số tàu: '{ma_tau_so}'")
                    print(f"        🗺️  Suy ra tỉnh: '{tinh}'")
                    
                    # Kiểm tra mapping
                    if tinh != "Không tìm thấy":
                        print(f"        ✅ Mapping thành công: {tinh_code} → {tinh}")
                        print(f"        🎯 Chương trình đã dùng chữ cái '{tinh_code}' để suy ra tỉnh '{tinh}'")
                    else:
                        print(f"        ❌ Không tìm thấy mapping cho mã: {tinh_code}")
                else:
                    print(f"     ⚠️  Mã tàu '{ma_tau_full}' không đúng format (cần: XX 12345)")
                    print(f"     🤔 Không thể suy ra tỉnh từ mã tàu này")
            else:
                print(f"     ⚠️  Không có raw_response để phân tích")
    
    print("\n" + "="*80)

def export_results_to_console(ma_niem_phong, ma_tau, ngay_chup, ma_thiet_bi, tinh, total_images, error_count):
    """Export kết quả tổng hợp ra console"""
    print("\n" + "="*60)
    print("🤖 KẾT QUẢ TỔNG HỢP AI")
    print("="*60)
    print(f"📊 Tổng số ảnh: {total_images}")
    print(f"✅ Thành công: {total_images - error_count}")
    if error_count > 0:
        print(f"❌ Lỗi: {error_count}")
    print("-"*60)
    print("📋 THÔNG TIN ĐƯỢC TRÍCH XUẤT (Tần suất cao nhất):")
    print(f"  🔒 Mã niêm phong: {ma_niem_phong if ma_niem_phong else 'Không tìm thấy'}")
    print(f"  🚢 Số tàu: {ma_tau if ma_tau else 'Không tìm thấy'}")
    print(f"  📅 Ngày chụp: {ngay_chup if ngay_chup else 'Không tìm thấy'}")
    print(f"  🔧 Mã thiết bị: {ma_thiet_bi if ma_thiet_bi else 'Không tìm thấy'}")
    print(f"  📍 Tỉnh: {tinh if tinh else 'Không tìm thấy'}")
    
    # Thêm thông tin về mapping tỉnh
    if tinh and tinh != "Không tìm thấy":
        print("-"*60)
        print("🗺️  THÔNG TIN MAPPING TỈNH:")
        # Tìm mã tỉnh tương ứng
        found_mapping = False
        tinh_mapping = create_tinh_mapping()
        for code, name in tinh_mapping.items():
            if name == tinh:
                print(f"  🏷️  Mã tỉnh: {code}")
                print(f"  📍 Tên tỉnh: {name}")
                print(f"  ✅ Mapping: {code} → {name}")
                found_mapping = True
                break
        
        if not found_mapping:
            print(f"  ⚠️  Không tìm thấy mã tỉnh cho: {tinh}")
            print(f"  🔍 Có thể AI đã nhận diện trực tiếp tên tỉnh từ ảnh")
            print(f"  📋 Danh sách mã tỉnh có sẵn:")
            for code, name in list(tinh_mapping.items())[:10]:  # Hiển thị 10 mã đầu
                print(f"     {code} → {name}")
            if len(tinh_mapping) > 10:
                print(f"     ... và {len(tinh_mapping) - 10} mã khác")
    else:
        print("-"*60)
        print("🗺️  THÔNG TIN MAPPING TỈNH:")
        print(f"  ❌ AI không nhận diện được tỉnh từ ảnh")
        print(f"  💡 Có thể do:")
        print(f"     - Không có mã tàu rõ ràng trong ảnh")
        print(f"     - Mã tàu không khớp với danh sách mapping")
        print(f"     - Chất lượng ảnh không đủ để nhận diện")
    
    print("="*60)
    print("💡 Thông tin đã được tự động điền vào form!")
    print("="*60 + "\n")

def show_ai_error(error_msg):
    """Hiển thị lỗi AI"""
    label_result.config(text=f"❌ Lỗi AI: {error_msg}")
    button_analyze.config(state="normal")

def open_config_manager():
    """Mở chương trình config manager"""
    try:
        # Kiểm tra xem file config_manager.py có tồn tại không
        if os.path.exists("config_manager.py"):
            # Mở config_manager.py bằng Python
            subprocess.Popen([sys.executable, "config_manager.py"])
            print("🔧 Đã mở Config Manager")
        else:
            messagebox.showerror("Lỗi", "Không tìm thấy file config_manager.py!")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở Config Manager: {e}")



def create_folder():
    tinh = combobox_tinh.get()
    daily = combobox_daily.get()
    so_tau = tau_num.get()
    ma_thiet_bi = device_code_num.get()
    ma_niem_phong = seal_code_num.get()
    ngay = cal.get_date().strftime("%d%m%y")

    # Kiểm tra mã niêm phong trong file niêm_phong.txt
    with open("niem_phong.txt", "r", encoding="utf-8") as f:
        valid_seal_codes = {line.strip() for line in f}
    if ma_niem_phong not in valid_seal_codes:
        messagebox.showerror("Lỗi", "Mã niêm phong không hợp lệ!")
        return

    # Lấy đường dẫn output
    output_path = output_folder_entry.get()

    # Kiểm tra đường dẫn output
    if not output_path:
        messagebox.showerror("Lỗi", "Vui lòng chọn folder output!")
        return

    # Kiểm tra mã thiết bị
    if not ma_thiet_bi.isdigit() or len(ma_thiet_bi) != 6:
        messagebox.showerror("Lỗi", "Mã thiết bị phải là đúng 6 chữ số!")
        return

    # Rút gọn tên tỉnh và đại lý
    tinh_rut_gon = tinh_thanh_vt.get(tinh, tinh)
    dai_ly_rut_gon = dai_ly_vt.get(daily, daily)
    if(cong_no_var.get()=="Yes"):
        cong_no_suffix = "1"
    elif(cong_no_var.get()=="No"):
        cong_no_suffix = "0"
    else:
        cong_no_suffix = "3"

    # Tạo tên thư mục
    folder_name = f"{tinh_rut_gon}.{dai_ly_rut_gon}.{so_tau}.{ma_thiet_bi}.{ma_niem_phong}.{ngay}.{cong_no_suffix}"
    full_path = os.path.join(output_path, folder_name)

    try:
        os.makedirs(full_path)
        
        # Move ảnh từ folder input sang folder output
        input_path = input_folder_entry.get()
        if input_path and os.path.exists(input_path):
            moved_count = 0
            for filename in os.listdir(input_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    source_path = os.path.join(input_path, filename)
                    destination_path = os.path.join(full_path, filename)
                    shutil.move(source_path, destination_path)
                    moved_count += 1
            
            if moved_count > 0:
                label_result.config(text=f"✅ Tạo folder thành công và đã di chuyển {moved_count} ảnh!")
            else:
                label_result.config(text="✅ Tạo folder thành công! (Không có ảnh để di chuyển)")
        else:
            label_result.config(text="✅ Tạo folder thành công! (Không có folder input)")
        
        # Xóa mã niêm phong đã dùng trong file niêm_phong.txt
        valid_seal_codes.remove(ma_niem_phong)
        with open("niem_phong.txt", "w", encoding="utf-8") as f:
            for code in valid_seal_codes:
                f.write(code + "\n")

        # Cập nhật hiển thị số mã niêm phong còn lại
        update_remaining_seal_codes()
        
    except Exception as e:
        label_result.config(text=f"❌ Lỗi: {e}")

    # Clear input fields after creating the folder
    combobox_tinh.set("")
    combobox_daily.set("")
    tau_num.delete(0, tk.END)
    device_code_num.delete(0, tk.END)
    seal_code_num.delete(0, tk.END)

def update_remaining_seal_codes():
    try:
        with open("niem_phong.txt", "r", encoding="utf-8") as f:
            remaining_codes = len(f.readlines())
        label_remaining_seal_codes.config(text=f"Mã niêm phong còn lại: {remaining_codes}")
    except FileNotFoundError:
        label_remaining_seal_codes.config(text="Không tìm thấy file niêm phong.")


def update_image_display():
    global image_labels
    for label in image_labels:
        label.destroy()
    image_labels = []

def load_mappings(tinh_config_file, dai_ly_config_file):
    tinh_mapping = {}
    dai_ly_mapping = {}

    with open(tinh_config_file, "r", encoding="utf-8") as f:
        for line in f:
            value, key = line.strip().split(":")
            tinh_mapping[key.strip()] = value.strip()

    with open(dai_ly_config_file, "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.strip().split(":")
            dai_ly_mapping[key.strip()] = value.strip()

    return tinh_mapping, dai_ly_mapping

def load_data(config_file):
    data = {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 2:
                    data[parts[0].strip()] = parts[1].strip()
    except FileNotFoundError:
        messagebox.showwarning("Cảnh báo", f"Không tìm thấy tệp tin cấu hình: {config_file}")

    return data

# --- Giao diện người dùng ---
window = tk.Tk()
window.title("Tạo folder")
window.iconbitmap("iconZ.ico")
cong_no_var = tk.StringVar(value="Unknow")

tinh_thanh_vt, dai_ly_vt = load_mappings("ma_tinh_config.txt", "dai_ly_config.txt")

# Load danh sách tỉnh thành từ file ma_tinh_config.txt
tinh_thanh_vt = load_data("ma_tinh_config.txt")
tinh_thanh_vn = list(tinh_thanh_vt.keys())

# Load danh sách đại lý từ file danh_sach_dai_ly.txt
dai_ly_vt = load_data("dai_ly_config.txt")
danh_sach_dai_ly = list(dai_ly_vt.keys())


# Frame chứa các thành phần nhập liệu
input_frame = tk.LabelFrame(window, text="Thông tin")
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Frame chứa đường dẫn
path_frame = tk.LabelFrame(window, text="Đường dẫn")
path_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Các Label và Entry trong Frame
label_tinh = tk.Label(input_frame, text="Tỉnh:")
label_tinh.grid(row=0, column=0, padx=5, pady=5, sticky="w")
combobox_tinh = AutocompleteCombobox(input_frame, completevalues=tinh_thanh_vn)
combobox_tinh.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

label_daily = tk.Label(input_frame, text="Đại lý:")
label_daily.grid(row=1, column=0, padx=5, pady=5, sticky="w")
combobox_daily = AutocompleteCombobox(input_frame, completevalues=danh_sach_dai_ly, width=35)
combobox_daily.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

label_sotau = tk.Label(input_frame, text="Số tàu:")
label_sotau.grid(row=2, column=0, padx=5, pady=5, sticky="w")
tau_num = tk.Entry(input_frame, width=10)
tau_num.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

# Validation cho số tàu - chỉ cho phép số
def validate_tau_number(event):
    value = tau_num.get()
    # Chỉ giữ lại các ký tự số
    filtered_value = ''.join(filter(str.isdigit, value))
    
    if filtered_value != value:
        tau_num.delete(0, tk.END)
        tau_num.insert(0, filtered_value)

tau_num.bind('<KeyRelease>', validate_tau_number)

label_device_code = tk.Label(input_frame, text="Mã thiết bị:")
label_device_code.grid(row=3, column=0, padx=5, pady=5, sticky="w")
device_code_num = tk.Entry(input_frame, width=10)
device_code_num.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

# Validation cho mã thiết bị - chỉ cho phép số và tối đa 6 ký tự
def validate_device_code(event):
    value = device_code_num.get()
    # Chỉ giữ lại các ký tự số
    filtered_value = ''.join(filter(str.isdigit, value))
    # Giới hạn tối đa 6 ký tự
    if len(filtered_value) > 6:
        filtered_value = filtered_value[:6]
    
    if filtered_value != value:
        device_code_num.delete(0, tk.END)
        device_code_num.insert(0, filtered_value)

device_code_num.bind('<KeyRelease>', validate_device_code)

label_seal_code = tk.Label(input_frame, text="Mã niêm phong:")
label_seal_code.grid(row=4, column=0, padx=5, pady=5, sticky="w")
seal_code_num = tk.Entry(input_frame, width=10)
seal_code_num.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

# Validation cho mã niêm phong - format: 1 chữ cái + 6 số
def validate_seal_code(event):
    value = seal_code_num.get().upper()
    # Chỉ giữ lại chữ cái và số
    filtered_value = ''.join(c for c in value if c.isalnum())
    # Giới hạn tối đa 7 ký tự
    if len(filtered_value) > 7:
        filtered_value = filtered_value[:7]
    
    if filtered_value != value:
        seal_code_num.delete(0, tk.END)
        seal_code_num.insert(0, filtered_value)

seal_code_num.bind('<KeyRelease>', validate_seal_code)

label_days = tk.Label(input_frame, text="Ngày:")
label_days.grid(row=5, column=0, padx=5, pady=5, sticky="w")
cal = DateEntry(input_frame, width=12, bg="darkblue", fg="white")
cal.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

# Thêm phần Công nợ
label_cong_no = tk.Label(input_frame, text="Công nợ:")
label_cong_no.grid(row=6, column=0, padx=5, pady=5, sticky="w")
cong_no_options = ["Unknow", "Yes", "No"]
for i, option in enumerate(cong_no_options):
    tk.Radiobutton(input_frame, text=option, variable=cong_no_var, value=option).grid(row=6, column=i+1, sticky="w")



# Folder Input
label_input_folder = tk.Label(path_frame, text="Folder Input:")
label_input_folder.grid(row=0, column=0, padx=5, pady=5, sticky="w")

input_folder_frame = tk.Frame(path_frame)
input_folder_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

input_folder_entry = tk.Entry(input_folder_frame, width=40)
input_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Tự động lưu khi thay đổi đường dẫn input
def on_input_folder_change(event):
    path = input_folder_entry.get().strip()
    if path and os.path.isdir(path):
        save_input_folder_path(path)

input_folder_entry.bind('<FocusOut>', on_input_folder_change)

button_browse_input = tk.Button(input_folder_frame, text="Chọn", command=browse_input_folder)
button_browse_input.pack(side=tk.RIGHT, padx=(5, 0))

# Folder Output
label_output_folder = tk.Label(path_frame, text="Folder Output:")
label_output_folder.grid(row=1, column=0, padx=5, pady=5, sticky="w")

output_folder_frame = tk.Frame(path_frame)
output_folder_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

output_folder_entry = tk.Entry(output_folder_frame, width=40)
output_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Tự động lưu khi thay đổi đường dẫn output
def on_output_folder_change(event):
    path = output_folder_entry.get().strip()
    if path and os.path.isdir(path):
        save_output_folder_path(path)

output_folder_entry.bind('<FocusOut>', on_output_folder_change)

button_browse_output = tk.Button(output_folder_frame, text="Chọn", command=browse_output_folder)
button_browse_output.pack(side=tk.RIGHT, padx=(5, 0))

# Cấu hình grid weights
path_frame.columnconfigure(1, weight=1)

# Frame chứa các nút điều khiển
button_frame = tk.Frame(path_frame)
button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

# Nút "Xử lý AI"
button_analyze = tk.Button(button_frame, text="🤖 Xử lý AI", command=analyze_images_with_ai, 
                          bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                          state="normal" if AI_AVAILABLE else "disabled")
button_analyze.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

# Nút "Tạo folder"
button_convert = tk.Button(button_frame, text="Tạo folder", command=create_folder)
button_convert.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

# Label hiển thị trạng thái AI
ai_status_text = "✅ AI: Sẵn sàng" if AI_AVAILABLE else "❌ AI: Cần cấu hình API Key"
label_ai_status = tk.Label(path_frame, text=ai_status_text, 
                          fg="green" if AI_AVAILABLE else "red", font=("Arial", 9))
label_ai_status.grid(row=3, column=0, columnspan=2, padx=5, pady=2)

# Nút "Cấu hình" ở góc trong frame "Thông tin"
button_config = tk.Button(input_frame, text="⚙️", command=open_config_manager,
                         bg="#FF9800", fg="white", font=("Arial", 8),
                         width=2, height=1, relief="flat", bd=0)
button_config.place(in_=input_frame, relx=0.98, rely=0.02, anchor="ne")

# Thêm label hiển thị số mã niêm phong còn lại
label_remaining_seal_codes = tk.Label(input_frame, text="")
label_remaining_seal_codes.grid(row=7, column=0, columnspan=2, padx=5, pady=5)  # Đặt vị trí phù hợp



# Cập nhật ban đầu khi chương trình chạy
update_remaining_seal_codes()

# Load đường dẫn đã lưu
input_folder_path = load_input_folder_path()
if input_folder_path:
    input_folder_entry.insert(0, input_folder_path)

output_folder_path = load_output_folder_path()
if output_folder_path:
    output_folder_entry.insert(0, output_folder_path)

# Label kết quả
label_result = tk.Label(window, text="")
label_result.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

# Cấu hình grid weights
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.rowconfigure(0, weight=1)

window.mainloop()
