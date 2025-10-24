
import tkinter as tk
from tkcalendar import Calendar, DateEntry
from ttkwidgets.autocomplete import AutocompleteCombobox, AutocompleteEntry  # Import AutocompleteEntry
from tkinter import scrolledtext, filedialog, messagebox
import os
import shutil
from PIL import Image, ImageTk
import webbrowser
import google.generativeai as genai
import json
import threading
from collections import Counter


selected_image_folder = ""
image_paths = []
image_labels = []
remove_buttons = []
CONFIG_FILE = "folder_path_config.txt"

# Cấu hình Google Gemini AI
GOOGLE_API_KEY = "AIzaSyAylYXbqPkbqBTGc7Spct9-EFQA0lguKaI"
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    AI_AVAILABLE = True
except Exception as e:
    print(f"Lỗi khởi tạo AI: {e}")
    AI_AVAILABLE = False

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

def extract_tinh_from_tau_code(tau_code):
    """Trích xuất mã tỉnh từ mã tàu và tìm tên tỉnh tương ứng"""
    if not tau_code:
        return "Không tìm thấy"
    
    tinh_mapping = create_tinh_mapping()
    
    # Thử các độ dài khác nhau của mã tỉnh (2-3 ký tự)
    for length in [3, 2]:
        if len(tau_code) >= length:
            code = tau_code[:length]
            if code in tinh_mapping:
                return tinh_mapping[code]
    
    return "Không tìm thấy"

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
Các key của JSON phải là: "ma_niem_phong", "ma_tau", "ngay_chup", "ma_thiet_bi", "tinh".

- "ma_niem_phong": Tìm mã niêm phong, ví dụ "SEAL A 12345", "K 67890", hoặc "Z01234". Chỉ lấy phần gồm 1 ký tự chữ và 5 số, ví dụ "A12345", "K67890", hoặc "Z01234". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_tau": Tìm số tàu, chỉ lấy phần số (không có chữ cái). Ví dụ từ "KG 95596" chỉ lấy "95596", từ "BT 97793" chỉ lấy "97793", từ "SG 12345" chỉ lấy "12345". Nếu không tìm thấy số, trả về "Không tìm thấy".
- "ngay_chup": Tìm ngày tháng trên ảnh, ví dụ "05/08/2025". Chuyển thành định dạng 6 số "DDMMYY", ví dụ "050825". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_thiet_bi": Tìm mã thiết bị, thường bắt đầu bằng BTK, ví dụ "BTK123456". Chỉ lấy 6 số cuối, ví dụ "123456". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "tinh": Tìm mã tàu đầy đủ (có cả chữ cái và số), sau đó dựa vào 2-3 ký tự đầu để xác định tên tỉnh thành. CHÚ Ý: Một số mã tỉnh có 3 ký tự như BĐ, BTh, ĐNa, ĐL, ĐNo, ĐB, ĐN, ĐT, HNa, HGi, LCa, QNa, QNg, TNg, TTH.

DANH SÁCH MÃ TỈNH:
{mapping_text}

Ví dụ: 
- Từ "KG 95596" → lấy "KG" → tìm "Kiên Giang"
- Từ "BĐ 12345" → lấy "BĐ" → tìm "Bình Định"  
- Từ "ĐNa 67890" → lấy "ĐNa" → tìm "Đà Nẵng"
- Từ "TTH 11111" → lấy "TTH" → tìm "Thừa Thiên Huế"

Nếu không xác định được, trả về "Không tìm thấy".

Quan trọng: Chỉ trả về đối tượng JSON, không thêm bất kỳ văn bản giải thích nào khác.
"""

MASTER_PROMPT = create_master_prompt()


def process_image_with_ai(image_path):
    """Phân tích một ảnh bằng AI và trả về thông tin"""
    try:
        img = Image.open(image_path)
        # Tạo prompt mới mỗi lần để đảm bảo có thông tin mapping mới nhất
        current_prompt = create_master_prompt()
        response = model.generate_content([current_prompt, img])
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_text)
        return data
    except json.JSONDecodeError:
        return {"error": "AI không trả về JSON hợp lệ", "raw_response": response.text}
    except Exception as e:
        return {"error": f"Lỗi: {e}"}

def analyze_images_with_ai():
    """Phân tích tất cả ảnh trong folder đã chọn bằng AI"""
    if not AI_AVAILABLE:
        messagebox.showerror("Lỗi", "AI không khả dụng. Vui lòng kiểm tra API key.")
        return
    
    if not selected_image_folder or not image_paths:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn folder chứa ảnh để phân tích.")
        return
    
    # Hiển thị loading
    label_result.config(text=f"Đang phân tích {len(image_paths)} ảnh bằng AI...")
    button_analyze.config(state="disabled")
    window.update()
    
    # Thông báo bắt đầu phân tích
    print(f"\n🚀 BẮT ĐẦU PHÂN TÍCH {len(image_paths)} ẢNH BẰNG AI...")
    print(f"📁 Folder: {selected_image_folder}")
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
                ma_tau = result.get('ma_tau', '').strip()
                ngay_chup = result.get('ngay_chup', '').strip()
                ma_thiet_bi = result.get('ma_thiet_bi', '').strip()
                tinh = result.get('tinh', '').strip()
                
                if ma_niem_phong and ma_niem_phong.lower() != 'không tìm thấy':
                    niem_phong_counts[ma_niem_phong] += 1
                if ma_tau and ma_tau.lower() != 'không tìm thấy':
                    tau_counts[ma_tau] += 1
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
            print(f"  🚢 Số tàu: {result.get('ma_tau', 'Không tìm thấy')}")
            print(f"  📅 Ngày chụp: {result.get('ngay_chup', 'Không tìm thấy')}")
            print(f"  🔧 Mã thiết bị: {result.get('ma_thiet_bi', 'Không tìm thấy')}")
            print(f"  📍 Tỉnh: {result.get('tinh', 'Không tìm thấy')}")
    
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
    print("="*60)
    print("💡 Thông tin đã được tự động điền vào form!")
    print("="*60 + "\n")

def show_ai_error(error_msg):
    """Hiển thị lỗi AI"""
    label_result.config(text=f"❌ Lỗi AI: {error_msg}")
    button_analyze.config(state="normal")

def show_image(index):
    # Hàm này không còn cần thiết vì đã chuyển sang chọn folder
    pass

def remove_image_and_close(index, window_to_close):
    # Hàm này không còn cần thiết vì đã chuyển sang chọn folder
    window_to_close.destroy()

def select_image_folder():
    global selected_image_folder, image_paths, image_labels, remove_buttons
    folder_path = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
    if not folder_path:
        return
    
    selected_image_folder = folder_path
    
    # Tìm tất cả ảnh trong folder
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    image_paths = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(image_extensions):
                image_paths.append(os.path.join(root, file))
    
    # Cập nhật hiển thị
    update_folder_display()
    
    # Hiển thị preview một số ảnh đầu tiên
    show_image_previews()

def update_folder_display():
    """Cập nhật hiển thị thông tin folder đã chọn"""
    if selected_image_folder:
        folder_name = os.path.basename(selected_image_folder)
        label_folder_info.config(text=f"📁 Folder: {folder_name} ({len(image_paths)} ảnh)")
    else:
        label_folder_info.config(text="📁 Chưa chọn folder")

def show_image_previews():
    """Hiển thị preview của một số ảnh đầu tiên"""
    # Xóa các preview cũ
    for widget in image_display_frame.winfo_children():
        widget.destroy()
    image_labels = []
    remove_buttons = []
    
    # Hiển thị tối đa 6 ảnh preview
    preview_count = min(6, len(image_paths))
    for i in range(preview_count):
        image_path = image_paths[i]
        
        # Tạo frame để chứa ảnh
        image_container = tk.Frame(image_display_frame)
        image_container.pack(side=tk.LEFT, padx=5, pady=5)

        # Hiển thị ảnh (giảm kích thước ảnh)
        try:
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(image_container, image=photo)
            label.image = photo
            label.pack()

            # Thêm sự kiện click vào ảnh để xem chi tiết
            label.bind("<Button-1>", lambda event, path=image_path: webbrowser.open(path))
            image_labels.append(label)
        except Exception as e:
            # Nếu không thể load ảnh, hiển thị tên file
            label = tk.Label(image_container, text=os.path.basename(image_path)[:10] + "...", 
                           width=12, height=3, relief="solid")
            label.pack()
            image_labels.append(label)
    
    if len(image_paths) > 6:
        more_label = tk.Label(image_display_frame, text=f"... và {len(image_paths) - 6} ảnh khác", 
                             font=("Arial", 9), fg="gray")
        more_label.pack(side=tk.LEFT, padx=5, pady=5)

def clear_folder_selection():
    """Xóa lựa chọn folder hiện tại"""
    global selected_image_folder, image_paths, image_labels, remove_buttons
    selected_image_folder = ""
    image_paths = []
    
    # Xóa hiển thị preview
    for widget in image_display_frame.winfo_children():
        widget.destroy()
    image_labels = []
    remove_buttons = []
    
    # Cập nhật hiển thị
    update_folder_display()


def browse_folder():
    global folder_path
    folder_path = filedialog.askdirectory(title="Chọn thư mục lưu")
    if folder_path:
        folder_path_entry.delete(0, tk.END)
        folder_path_entry.insert(0, folder_path)
        save_folder_path(folder_path)

def save_folder_path(path):
    with open(CONFIG_FILE, "w") as f:
        f.write(path)

def load_folder_path():
    try:
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def create_folder():
    global folder_path, image_paths, image_labels, remove_buttons
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

    # Lấy đường dẫn từ ô nhập liệu nếu nó đã được thay đổi
    folder_path = folder_path_entry.get()

    # Kiểm tra đường dẫn thư mục
    if not folder_path:
        messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu!")
        return

    # Kiểm tra mã thiết bị
    if not ma_thiet_bi.isdigit() or len(ma_thiet_bi) != 6:
        messagebox.showerror("Lỗi", "Mã thiết bị phải là 6 chữ số!")
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
    full_path = os.path.join(folder_path, folder_name)

    try:
        os.makedirs(full_path)
        
        # Copy ảnh từ folder đã chọn vào folder mới
        if image_paths:
            for image_path in image_paths:
                image_name = os.path.basename(image_path)
                destination_path = os.path.join(full_path, image_name)
                shutil.copy2(image_path, destination_path)  # Sử dụng copy2 để giữ metadata

        label_result.config(text="✅ Tạo folder thành công!")
        
        # Xóa mã niêm phong đã dùng trong file niêm_phong.txt
        valid_seal_codes.remove(ma_niem_phong)
        with open("niem_phong.txt", "w", encoding="utf-8") as f:
            for code in valid_seal_codes:
                f.write(code + "\n")

        # Cập nhật hiển thị số mã niêm phong còn lại
        update_remaining_seal_codes()
        
        # Xóa lựa chọn folder sau khi tạo thành công
        clear_folder_selection()
        
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
input_frame = tk.LabelFrame(window, text="Thông tin")  # Khởi tạo input_frame
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Frame chứa chức năng AI
ai_frame = tk.LabelFrame(window, text="Phân tích AI")
ai_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

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
tau_num = tk.Entry(input_frame)
tau_num.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

label_device_code = tk.Label(input_frame, text="Mã thiết bị:")
label_device_code.grid(row=3, column=0, padx=5, pady=5, sticky="w")
device_code_num = tk.Entry(input_frame)
device_code_num.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

label_seal_code = tk.Label(input_frame, text="Mã niêm phong:")
label_seal_code.grid(row=4, column=0, padx=5, pady=5, sticky="w")
seal_code_num = tk.Entry(input_frame)
seal_code_num.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

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



# Frame chứa thông tin folder đã chọn
folder_info_frame = tk.Frame(ai_frame)
folder_info_frame.pack(fill=tk.X, padx=10, pady=5)

# Nút "Chọn folder ảnh"
button_chon_folder = tk.Button(image_frame, text="📁 Chọn folder ảnh", command=select_image_folder,
                              bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
button_chon_folder.pack(pady=5)

# Nút "Xóa folder"
button_xoa_folder = tk.Button(image_frame, text="🗑️ Xóa folder", command=clear_folder_selection,
                             bg="#f44336", fg="white", font=("Arial", 9))
button_xoa_folder.pack(pady=2)

# Label hiển thị thông tin folder
label_folder_info = tk.Label(image_frame, text="📁 Chưa chọn folder", 
                            font=("Arial", 9), fg="gray")
label_folder_info.pack(pady=2)

# Nút "Phân tích AI"
button_analyze = tk.Button(image_frame, text="🤖 Phân tích AI", command=analyze_images_with_ai, 
                          bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                          state="normal" if AI_AVAILABLE else "disabled")
button_analyze.pack(pady=5)

# Frame chứa các nút điều khiển
button_frame = tk.Frame(window)
button_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")  # Thay đổi columnspan

# Nút "Lưu tại..." và ô nhập đường dẫn
button_convert = tk.Button(button_frame, text="Lưu tại...", command=browse_folder)
button_convert.pack(side="left", padx=5)
folder_path_entry = tk.Entry(button_frame)
folder_path_entry.pack(side="left", fill="x", expand=True, padx=5)

# Nút "Tạo folder"
button_convert = tk.Button(button_frame, text="Tạo folder", command=create_folder)
button_convert.pack(side="right", padx=5)

# Thêm label hiển thị số mã niêm phong còn lại
label_remaining_seal_codes = tk.Label(input_frame, text="")
label_remaining_seal_codes.grid(row=7, column=0, columnspan=2, padx=5, pady=5)  # Đặt vị trí phù hợp

# Label hiển thị trạng thái AI
ai_status_text = "🤖 AI: Sẵn sàng" if AI_AVAILABLE else "❌ AI: Không khả dụng"
label_ai_status = tk.Label(input_frame, text=ai_status_text, 
                          fg="green" if AI_AVAILABLE else "red", font=("Arial", 9))
label_ai_status.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

# Thêm hướng dẫn sử dụng AI
if AI_AVAILABLE:
    help_text = "💡 Mẹo: Chọn folder ảnh và nhấn 'Phân tích AI' để tự động điền thông tin"
    label_ai_help = tk.Label(input_frame, text=help_text, 
                            fg="blue", font=("Arial", 8), wraplength=300)
    label_ai_help.grid(row=9, column=0, columnspan=2, padx=5, pady=2)

# Cập nhật ban đầu khi chương trình chạy
update_remaining_seal_codes()

# Label kết quả
label_result = tk.Label(window, text="")
label_result.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

folder_path = load_folder_path()  # Tải đường dẫn đã lưu
folder_path_entry.insert(0, folder_path)

window.iconbitmap("iconZ.ico")

window.mainloop()
