
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar, DateEntry
from ttkwidgets.autocomplete import AutocompleteCombobox, AutocompleteEntry  # Import AutocompleteEntry
from tkinter import scrolledtext, filedialog, messagebox
import os
import shutil
# Lazy import Google API - chỉ import khi cần
# import google.generativeai as genai
import json
import threading
from collections import Counter
from PIL import Image
import subprocess
import sys
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


CONFIG_FILE = "folder_path_config.txt"
INPUT_FOLDER_CONFIG = "input_folder_config.txt"
OUTPUT_FOLDER_CONFIG = "output_folder_config.txt"

# --- Load AI config from file (nếu có, fallback default)
def load_ai_opt_config():
    d = {}
    try:
        with open("api_config.json", "r", encoding="utf-8") as f:
            d = json.load(f)
    except:
        pass
    
    GEMINI_RPM_LIMIT = d.get("GEMINI_RPM_LIMIT", 15)
    BATCH_DELAY = d.get("BATCH_DELAY", 1.5)
    CONCURRENT_REQUESTS = d.get("CONCURRENT_REQUESTS", 3)
    IMAGES_PER_REQUEST = d.get("IMAGES_PER_REQUEST", 5)
    ENABLE_DOWNSCALE = d.get("ENABLE_DOWNSCALE", True)
    MAX_IMAGE_SIZE = d.get("MAX_IMAGE_SIZE", 1600)
    MIN_DELAY = d.get("MIN_DELAY", 0.5)
    return {
        'GEMINI_RPM_LIMIT': GEMINI_RPM_LIMIT, 'BATCH_DELAY': BATCH_DELAY, 'CONCURRENT_REQUESTS': CONCURRENT_REQUESTS,
        'IMAGES_PER_REQUEST': IMAGES_PER_REQUEST, 'ENABLE_DOWNSCALE': ENABLE_DOWNSCALE, 'MAX_IMAGE_SIZE': MAX_IMAGE_SIZE,
        'MIN_DELAY': MIN_DELAY
    }

ai_opt = load_ai_opt_config()
GEMINI_RPM_LIMIT = ai_opt['GEMINI_RPM_LIMIT']
BATCH_DELAY      = ai_opt['BATCH_DELAY']
CONCURRENT_REQUESTS = ai_opt['CONCURRENT_REQUESTS']
IMAGES_PER_REQUEST  = ai_opt['IMAGES_PER_REQUEST']
ENABLE_DOWNSCALE    = ai_opt['ENABLE_DOWNSCALE']
MAX_IMAGE_SIZE      = ai_opt['MAX_IMAGE_SIZE']
MIN_DELAY           = ai_opt['MIN_DELAY']


def calculate_batch_config(total_images):
    """Tính toán cấu hình batch dựa trên tổng số ảnh với multi-image requests"""
    # Tính số request cần thiết với multi-image
    num_requests = math.ceil(total_images / IMAGES_PER_REQUEST)
    
    if num_requests <= GEMINI_RPM_LIMIT:
        # Nếu số request <= 15, xử lý tất cả trong 1 batch
        batch_size = num_requests
        num_batches = 1
        # Với multi-image: thời gian = số request / số concurrent * 1.5s (lâu hơn vì nhiều ảnh)
        estimated_time = (num_requests / CONCURRENT_REQUESTS) * 1.5
    else:
        # Nếu nhiều hơn 15 requests, chia thành nhiều batch
        batch_size = GEMINI_RPM_LIMIT
        num_batches = math.ceil(num_requests / batch_size)
        # Ước tính thời gian: (số batch - 1) * delay + (số request / concurrent) * 1.5s
        estimated_time = (num_batches - 1) * BATCH_DELAY + (num_requests / CONCURRENT_REQUESTS) * 1.5
    
    return {
        'batch_size': batch_size,
        'num_batches': num_batches,
        'estimated_time': estimated_time,
        'concurrent_requests': CONCURRENT_REQUESTS,
        'images_per_request': IMAGES_PER_REQUEST,
        'total_requests': num_requests
    }

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

# Lazy load Google API - chỉ khởi tạo khi cần
GOOGLE_API_KEY, MODEL_NAME = load_api_config()
genai = None
model = None
AI_AVAILABLE = None  # None = chưa kiểm tra, True/False = đã kiểm tra

def init_google_ai():
    """Khởi tạo Google AI (lazy loading)"""
    global genai, model, AI_AVAILABLE
    
    # Nếu đã khởi tạo rồi thì không cần làm gì
    if AI_AVAILABLE is not None:
        return AI_AVAILABLE
    
    # Import Google API chỉ khi cần
    try:
        import google.generativeai as genai_module
        genai = genai_module
        
        if GOOGLE_API_KEY and MODEL_NAME:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel(MODEL_NAME)
            AI_AVAILABLE = True
            print("✅ AI đã sẵn sàng!")
            # Cập nhật UI
            if 'label_ai_status' in globals():
                window.after(0, update_ai_status)
            return True
        else:
            AI_AVAILABLE = False
            print("❌ AI không khả dụng - Cần cấu hình API Key")
            # Cập nhật UI
            if 'label_ai_status' in globals():
                window.after(0, update_ai_status)
            return False
    except ImportError as e:
        print(f"❌ Lỗi import Google API: {e}")
        AI_AVAILABLE = False
        if 'label_ai_status' in globals():
            window.after(0, update_ai_status)
        return False
    except Exception as e:
        print(f"❌ Lỗi khởi tạo AI: {e}")
        AI_AVAILABLE = False
        if 'label_ai_status' in globals():
            window.after(0, update_ai_status)
        return False




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
Các key của JSON phải là: "ma_niem_phong", "ma_tau_full", "ngay_chup", "ma_thiet_bi_full".

- "ma_niem_phong": Tìm mã niêm phong, ví dụ "SEAL A 123456", "K 678901", hoặc "Z012345". Chỉ lấy phần gồm 1 ký tự chữ và 6 số, ví dụ "A123456", "K678901", hoặc "Z012345". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_tau_full": Tìm mã tàu đầy đủ (có cả chữ cái và số), ví dụ "KG 95596", "BT 97793", "SG 12345", "BĐ 12345", "ĐNa 67890", "TTH 11111". Giữ nguyên format đầy đủ với khoảng trắng. QUAN TRỌNG: Tổng hợp toàn bộ mã tàu bao gồm cả mã tỉnh và số tàu thành một chuỗi duy nhất. Nếu không tìm thấy, trả về "Không tìm thấy".
- "ngay_chup": Tìm ngày tháng trên ảnh, ví dụ "05/08/2025". Chuyển thành định dạng 6 số "DDMMYY", ví dụ "050825". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_thiet_bi_full": Tìm mã thiết bị đầy đủ, BẮT BUỘC bắt đầu bằng BTK, ví dụ "BTK123456", "BTK009533", "BTK000123". Giữ nguyên format đầy đủ bao gồm cả chữ cái và số. QUAN TRỌNG: Tổng hợp toàn bộ mã thiết bị bao gồm cả phần chữ cái (BTK) và phần số thành một chuỗi duy nhất. CHỈ CHẤP NHẬN mã bắt đầu bằng BTK, không chấp nhận BOX, DEV, hoặc các mã khác. Nếu không tìm thấy mã BTK, trả về "Không tìm thấy".

Ví dụ: 
- Mã thiết bị: "BTK123456" → trả về "BTK123456" (tổng hợp đầy đủ)
- Mã thiết bị: "BTK009533" → trả về "BTK009533" (tổng hợp đầy đủ)
- Mã thiết bị: "BTK000123" → trả về "BTK000123" (tổng hợp đầy đủ)
- Mã thiết bị: "BOX001907" → trả về "Không tìm thấy" (không phải BTK)
- Mã tàu: "KG 95596" → trả về "KG 95596" (tổng hợp đầy đủ)
- Mã tàu: "BĐ 12345" → trả về "BĐ 12345" (tổng hợp đầy đủ)
- Mã tàu: "ĐNa 67890" → trả về "ĐNa 67890" (tổng hợp đầy đủ)

QUAN TRỌNG: 
1. Tổng hợp mã tàu đầy đủ trước (bao gồm cả mã tỉnh và số tàu)
2. Tổng hợp mã thiết bị đầy đủ trước (bao gồm cả BTK và số)
3. Giữ nguyên format gốc của mã tàu và mã thiết bị
4. Không tách riêng các phần trong JSON response
5. Việc tách các phần sẽ được xử lý sau

Nếu không xác định được, trả về "Không tìm thấy".

Quan trọng: Chỉ trả về đối tượng JSON, không thêm bất kỳ văn bản giải thích nào khác.
"""

def create_multi_image_prompt():
    """Tạo prompt cho xử lý nhiều ảnh trong một request"""
    tinh_mapping = create_tinh_mapping()
    
    # Tạo danh sách mapping rõ ràng hơn
    mapping_list = []
    for code, name in tinh_mapping.items():
        mapping_list.append(f"{code} = {name}")
    
    mapping_text = "\n".join(mapping_list)
    
    return f"""
Phân tích các hình ảnh này và trích xuất thông tin từ mỗi ảnh.
Trả lời bằng một mảng JSON hợp lệ, mỗi phần tử là kết quả của một ảnh.

Mỗi phần tử trong mảng phải có các key: "ma_niem_phong", "ma_tau_full", "ngay_chup", "ma_thiet_bi_full".

- "ma_niem_phong": Tìm mã niêm phong, ví dụ "SEAL A 123456", "K 678901", hoặc "Z012345". Chỉ lấy phần gồm 1 ký tự chữ và 6 số, ví dụ "A123456", "K678901", hoặc "Z012345". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_tau_full": Tìm mã tàu đầy đủ (có cả chữ cái và số), ví dụ "KG 95596", "BT 97793", "SG 12345", "BĐ 12345", "ĐNa 67890", "TTH 11111". Giữ nguyên format đầy đủ với khoảng trắng. QUAN TRỌNG: Tổng hợp toàn bộ mã tàu bao gồm cả mã tỉnh và số tàu thành một chuỗi duy nhất. Nếu không tìm thấy, trả về "Không tìm thấy".
- "ngay_chup": Tìm ngày tháng trên ảnh, ví dụ "05/08/2025". Chuyển thành định dạng 6 số "DDMMYY", ví dụ "050825". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_thiet_bi_full": Tìm mã thiết bị đầy đủ, BẮT BUỘC bắt đầu bằng BTK, ví dụ "BTK123456", "BTK009533", "BTK000123". Giữ nguyên format đầy đủ bao gồm cả chữ cái và số. QUAN TRỌNG: Tổng hợp toàn bộ mã thiết bị bao gồm cả phần chữ cái (BTK) và phần số thành một chuỗi duy nhất. CHỈ CHẤP NHẬN mã bắt đầu bằng BTK, không chấp nhận BOX, DEV, hoặc các mã khác. Nếu không tìm thấy mã BTK, trả về "Không tìm thấy".

Ví dụ: 
- Mã thiết bị: "BTK123456" → trả về "BTK123456" (tổng hợp đầy đủ)
- Mã thiết bị: "BTK009533" → trả về "BTK009533" (tổng hợp đầy đủ)
- Mã thiết bị: "BTK000123" → trả về "BTK000123" (tổng hợp đầy đủ)
- Mã thiết bị: "BOX001907" → trả về "Không tìm thấy" (không phải BTK)
- Mã tàu: "KG 95596" → trả về "KG 95596" (tổng hợp đầy đủ)
- Mã tàu: "BĐ 12345" → trả về "BĐ 12345" (tổng hợp đầy đủ)
- Mã tàu: "ĐNa 67890" → trả về "ĐNa 67890" (tổng hợp đầy đủ)

QUAN TRỌNG: 
1. Phân tích từng ảnh riêng biệt
2. Trả về mảng JSON với số phần tử bằng số ảnh
3. Tổng hợp mã tàu đầy đủ trước (bao gồm cả mã tỉnh và số tàu)
4. Tổng hợp mã thiết bị đầy đủ trước (bao gồm cả BTK và số)
5. Giữ nguyên format gốc của mã tàu và mã thiết bị
6. Không tách riêng các phần trong JSON response
7. Việc tách các phần sẽ được xử lý sau

Nếu không xác định được, trả về "Không tìm thấy".

Quan trọng: Chỉ trả về mảng JSON, không thêm bất kỳ văn bản giải thích nào khác.
"""

def process_image_with_ai(image_path, current_prompt=None):
    """Phân tích một ảnh bằng AI và trả về thông tin"""
    try:
        img = open_image_optimized(image_path)
        # Tạo prompt nếu chưa truyền vào
        if current_prompt is None:
            current_prompt = create_master_prompt()
        response = generate_with_retry([current_prompt, img])
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_text)
        # Lưu raw response để debug
        data['raw_response'] = response.text
        return data
    except json.JSONDecodeError:
        return {"error": "AI không trả về JSON hợp lệ", "raw_response": response.text if 'response' in locals() else ''}
    except Exception as e:
        return {"error": f"Lỗi: {e}"}


def process_multiple_images_with_ai(image_paths, current_prompt=None):
    """Phân tích nhiều ảnh trong một request và trả về danh sách kết quả"""
    try:
        # Mở tất cả ảnh (tối ưu kích thước)
        images = []
        for image_path in image_paths:
            img = open_image_optimized(image_path)
            images.append(img)
        
        # Tạo prompt cho multi-image nếu chưa truyền
        if current_prompt is None:
            current_prompt = create_multi_image_prompt()
        
        # Gửi tất cả ảnh trong một request
        response = generate_with_retry([current_prompt] + images)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_text)
        
        if not isinstance(data, list):
            data = [data]
        
        results = []
        for i, result in enumerate(data):
            if i < len(image_paths):
                result['file_name'] = os.path.basename(image_paths[i])
                result['raw_response'] = response.text
                results.append(result)
        
        return results
    except json.JSONDecodeError:
        error_results = []
        for image_path in image_paths:
            error_results.append({
                "error": "AI không trả về JSON hợp lệ", 
                "raw_response": response.text if 'response' in locals() else '',
                "file_name": os.path.basename(image_path)
            })
        return error_results
    except Exception as e:
        error_results = []
        for image_path in image_paths:
            error_results.append({
                "error": f"Lỗi: {e}",
                "file_name": os.path.basename(image_path)
            })
        return error_results

def process_batch_multi_image(batch_images, batch_num, total_batches, total_images, multi_prompt_cache=None):
    """Xử lý một batch ảnh với multi-image requests"""
    batch_results = []
    request_times = []  # Lưu thời gian xử lý các request
    
    def process_image_group(image_group_info):
        image_paths, start_idx = image_group_info
        start_time = time.time()
        
        print(f"🔄 Đang xử lý nhóm ảnh {start_idx + 1}-{start_idx + len(image_paths)}/{total_images} ({len(image_paths)} ảnh)")
        
        # Cập nhật UI progress
        def update_progress():
            label_result.config(text=f"Đang phân tích nhóm ảnh {start_idx + 1}-{start_idx + len(image_paths)}/{total_images}...\nBatch {batch_num + 1}/{total_batches}")
        window.after(0, update_progress)
        
        # Xử lý nhiều ảnh trong một request
        results = process_multiple_images_with_ai(image_paths, multi_prompt_cache)
        
        end_time = time.time()
        request_time = end_time - start_time
        request_times.append(request_time)
        
        print(f"✅ Hoàn thành nhóm ảnh {start_idx + 1}-{start_idx + len(image_paths)}/{total_images} (took {request_time:.2f}s)")
        return results
    
    # Chia ảnh thành các nhóm
    image_groups = []
    # Tính start_idx dựa trên batch_num và số ảnh thực tế
    start_idx = batch_num * GEMINI_RPM_LIMIT * IMAGES_PER_REQUEST
    for i in range(0, len(batch_images), IMAGES_PER_REQUEST):
        group_images = batch_images[i:i + IMAGES_PER_REQUEST]
        group_start_idx = start_idx + i
        image_groups.append((group_images, group_start_idx))
    
    print(f"📦 Chia batch thành {len(image_groups)} nhóm, mỗi nhóm tối đa {IMAGES_PER_REQUEST} ảnh")
    
    # Xử lý concurrent với ThreadPoolExecutor
    processed_count = 0
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        # Submit tất cả tasks
        future_to_group = {executor.submit(process_image_group, group_info): group_info 
                          for group_info in image_groups}
        
        # Thu thập kết quả khi hoàn thành
        for future in as_completed(future_to_group):
            try:
                results = future.result()
                batch_results.extend(results)  # Extend vì results là một list
                processed_count += len(results)
                
                # Cập nhật progress bar
                current_count = processed_count
                def update_progress_bar(count=current_count, total=total_images):
                    progress_bar['value'] = count
                    progress_label.config(text=f"Đang xử lý: {count}/{total} ảnh")
                window.after(0, update_progress_bar)
                
            except Exception as e:
                group_info = future_to_group[future]
                # Tạo kết quả lỗi cho tất cả ảnh trong nhóm
                error_count_in_group = len(group_info[0])
                for image_path in group_info[0]:
                    error_result = {"error": f"Lỗi xử lý nhóm ảnh: {e}", "file_name": os.path.basename(image_path)}
                    batch_results.append(error_result)
                processed_count += error_count_in_group
                
                # Cập nhật progress bar cho lỗi
                current_count = processed_count
                def update_progress_bar_error(count=current_count, total=total_images):
                    progress_bar['value'] = count
                    progress_label.config(text=f"Đang xử lý: {count}/{total} ảnh")
                window.after(0, update_progress_bar_error)
    
    # Tính toán thống kê thời gian
    if request_times:
        avg_time = sum(request_times) / len(request_times)
        total_images_processed = len(batch_results)
        print(f"📊 Thống kê batch {batch_num + 1}: {len(request_times)} requests, trung bình {avg_time:.2f}s/request, {total_images_processed} ảnh")
    
    return batch_results

def create_pdf_from_images(image_paths, output_pdf_path):
    """Gộp tất cả ảnh thành một file PDF"""
    try:
        images = []
        for image_path in image_paths:
            try:
                # Mở ảnh và chuyển sang RGB nếu cần
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
            except Exception as e:
                print(f"⚠️  Không thể mở ảnh {os.path.basename(image_path)}: {e}")
                continue
        
        if not images:
            print("❌ Không có ảnh nào để tạo PDF")
            return False
        
        # Lưu tất cả ảnh vào PDF
        if images:
            images[0].save(
                output_pdf_path,
                "PDF",
                resolution=100.0,
                save_all=True,
                append_images=images[1:] if len(images) > 1 else []
            )
            print(f"✅ Đã tạo PDF: {output_pdf_path} ({len(images)} ảnh)")
            return True
        return False
    except Exception as e:
        print(f"❌ Lỗi khi tạo PDF: {e}")
        return False

def open_pdf(pdf_path):
    """Tự động mở file PDF"""
    try:
        if sys.platform == "win32":
            # Windows: sử dụng os.startfile
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            # macOS: sử dụng open
            subprocess.run(["open", pdf_path])
        else:
            # Linux: sử dụng xdg-open
            subprocess.run(["xdg-open", pdf_path])
        print(f"📄 Đã mở PDF: {pdf_path}")
    except Exception as e:
        print(f"⚠️  Không thể mở PDF tự động: {e}")
        messagebox.showwarning("Cảnh báo", f"Đã tạo PDF nhưng không thể mở tự động:\n{pdf_path}")

def analyze_images_with_ai():
    """Phân tích tất cả ảnh trong folder input bằng AI"""
    # Lazy load Google AI khi cần
    if not init_google_ai():
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
    
    # Debug: Hiển thị danh sách ảnh tìm thấy
    print(f"🔍 Tìm thấy {len(image_paths)} ảnh:")
    for i, path in enumerate(image_paths, 1):
        print(f"  {i}. {os.path.basename(path)}")
    print("-" * 60)
    
    # Tính toán cấu hình batch
    batch_config = calculate_batch_config(len(image_paths))
    
    # Hiển thị loading với thông tin batch
    if batch_config['num_batches'] > 1:
        label_result.config(text=f"Đang phân tích {len(image_paths)} ảnh bằng AI...\nChia thành {batch_config['num_batches']} batch, {batch_config['concurrent_requests']} concurrent\n{batch_config['images_per_request']} ảnh/request (ước tính {batch_config['estimated_time']:.1f}s)")
    else:
        label_result.config(text=f"Đang phân tích {len(image_paths)} ảnh bằng AI...\n{batch_config['concurrent_requests']} concurrent, {batch_config['images_per_request']} ảnh/request")
    button_analyze.config(state="disabled")
    
    # Hiển thị và khởi tạo progress bar
    progress_frame.grid()
    progress_bar['maximum'] = len(image_paths)
    progress_bar['value'] = 0
    progress_label.config(text=f"Đang xử lý: 0/{len(image_paths)} ảnh")
    window.update()
    
    # Thông báo bắt đầu phân tích
    print(f"\n🚀 BẮT ĐẦU PHÂN TÍCH {len(image_paths)} ẢNH BẰNG AI...")
    print(f"📁 Folder: {input_path}")
    print(f"📊 Cấu hình batch: {batch_config['num_batches']} batch, mỗi batch tối đa {batch_config['batch_size']} requests")
    print(f"🖼️  Multi-image processing: {batch_config['images_per_request']} ảnh/request")
    print(f"⚡ Concurrent processing: {batch_config['concurrent_requests']} requests đồng thời")
    print(f"📈 Tổng số requests: {batch_config['total_requests']} (giảm {len(image_paths) - batch_config['total_requests']} requests)")
    print(f"⏱️  Thời gian ước tính: {batch_config['estimated_time']:.1f} giây")
    print("-" * 60)
    
    # Cache prompt cho cả phiên chạy
    master_prompt_cache = create_master_prompt()
    multi_prompt_cache = create_multi_image_prompt()
    
    def analyze_thread():
        try:
            # Lưu thời gian bắt đầu
            start_time = time.time()
            all_results = []
            batch_size = batch_config['batch_size']
            num_batches = batch_config['num_batches']
            
            for batch_num in range(num_batches):
                # batch_size là số requests, cần tính số ảnh thực tế
                requests_per_batch = batch_size
                start_idx = batch_num * requests_per_batch * IMAGES_PER_REQUEST
                end_idx = min(start_idx + requests_per_batch * IMAGES_PER_REQUEST, len(image_paths))
                batch_images = image_paths[start_idx:end_idx]
                
                print(f"\n📦 BATCH {batch_num + 1}/{num_batches}: Xử lý ảnh {start_idx + 1}-{end_idx}")
                print(f"🖼️  Số ảnh trong batch: {len(batch_images)}")
                print(f"⚡ Multi-image processing: {IMAGES_PER_REQUEST} ảnh/request")
                print(f"🔄 Concurrent processing: {CONCURRENT_REQUESTS} requests đồng thời")
                
                # Xử lý batch với multi-image processing (dùng prompt cache)
                batch_results = process_batch_multi_image(batch_images, batch_num, num_batches, len(image_paths), multi_prompt_cache)
                all_results.extend(batch_results)
                
                print(f"✅ Hoàn thành batch {batch_num + 1}/{num_batches}")
                
                # Delay giữa các batch (trừ batch cuối)
                if batch_num < num_batches - 1:
                    print(f"⏳ Chờ {BATCH_DELAY}s trước khi xử lý batch tiếp theo...")
                    def update_delay():
                        label_result.config(text=f"Hoàn thành batch {batch_num + 1}/{num_batches}\nChờ {BATCH_DELAY}s trước batch tiếp theo...")
                    window.after(0, update_delay)
                    time.sleep(BATCH_DELAY)
            
            print(f"\n🎉 HOÀN TẤT PHÂN TÍCH {len(image_paths)} ẢNH!")
            print(f"📊 Tổng kết quả: {len(all_results)} kết quả từ {len(image_paths)} ảnh")
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
                ma_tau_full = result.get('ma_tau_full', '').strip()  # Mã tàu đầy đủ từ AI
                ngay_chup = result.get('ngay_chup', '').strip()
                ma_thiet_bi_full = result.get('ma_thiet_bi_full', '').strip()  # Mã thiết bị đầy đủ từ AI
                
                # Tự động suy ra tỉnh từ mã tàu đầy đủ
                tinh = "Không tìm thấy"
                ma_tau_so = "Không tìm thấy"
                
                if ma_tau_full and ma_tau_full.lower() != 'không tìm thấy':
                    import re
                    ma_tau_pattern = r'([A-Za-z]{2,3})[-\s]*(\d{5})'
                    ma_tau_match = re.search(ma_tau_pattern, ma_tau_full)
                    
                    if ma_tau_match:
                        tinh_code = ma_tau_match.group(1).upper()
                        ma_tau_so = ma_tau_match.group(2)
                        
                        tinh_mapping = create_tinh_mapping()
                        for code, name in tinh_mapping.items():
                            if code.upper() == tinh_code:
                                tinh = name
                                break
                        
                        result['tinh_code'] = tinh_code
                        result['tinh_code_original'] = ma_tau_match.group(1)
                        result['ma_tau_so'] = ma_tau_so
                        result['tinh'] = tinh
                        result['ma_tau'] = ma_tau_full
                    else:
                        ma_tau_so = ma_tau_full
                        result['ma_tau_so'] = ma_tau_so
                        result['tinh'] = tinh
                
                result['ma_thiet_bi_full'] = ma_thiet_bi_full
                
                if ma_niem_phong and ma_niem_phong.lower() != 'không tìm thấy':
                    niem_phong_counts[ma_niem_phong] += 1
                if ma_tau_so and ma_tau_so.lower() != 'không tìm thấy':
                    tau_counts[ma_tau_so] += 1
                if ngay_chup and ngay_chup.lower() != 'không tìm thấy':
                    ngay_chup_counts[ngay_chup] += 1
                if ma_thiet_bi_full and ma_thiet_bi_full.lower() != 'không tìm thấy':
                    ma_thiet_bi_counts[ma_thiet_bi_full] += 1
                if tinh and tinh.lower() != 'không tìm thấy':
                    tinh_counts[tinh] += 1
            
            # Tìm giá trị phổ biến nhất
            final_niem_phong = niem_phong_counts.most_common(1)[0][0] if niem_phong_counts else ""
            final_tau = tau_counts.most_common(1)[0][0] if tau_counts else ""
            final_ngay_chup = ngay_chup_counts.most_common(1)[0][0] if ngay_chup_counts else ""
            final_thiet_bi_full = ma_thiet_bi_counts.most_common(1)[0][0] if ma_thiet_bi_counts else ""
            final_tinh = tinh_counts.most_common(1)[0][0] if tinh_counts else ""
            
            # Xử lý mã thiết bị đầy đủ để lấy số cuối cùng
            final_thiet_bi = "Không tìm thấy"
            if final_thiet_bi_full and final_thiet_bi_full.lower() != 'không tìm thấy':
                import re
                thiet_bi_pattern = r'BTK(\d{6})'
                thiet_bi_match = re.search(thiet_bi_pattern, final_thiet_bi_full.upper())
                
                if thiet_bi_match:
                    final_thiet_bi = thiet_bi_match.group(1)
                else:
                    if not final_thiet_bi_full.upper().startswith('BTK'):
                        print(f"⚠️  Mã thiết bị '{final_thiet_bi_full}' không bắt đầu bằng BTK - bỏ qua")
                        final_thiet_bi = "Không tìm thấy"
                    else:
                        numbers = re.findall(r'\d+', final_thiet_bi_full)
                        if numbers:
                            last_number = numbers[-1]
                            if len(last_number) >= 6:
                                final_thiet_bi = last_number[-6:]
                            else:
                                final_thiet_bi = last_number.zfill(6)
            
            export_detailed_results_to_console(all_results)
            
            # Tính thời gian xử lý
            end_time = time.time()
            processing_time = end_time - start_time
            minutes = int(processing_time // 60)
            seconds = int(processing_time % 60)
            milliseconds = int((processing_time % 1) * 1000)
            
            # Format thời gian
            if minutes > 0:
                time_str = f"{minutes} phút {seconds} giây"
            else:
                time_str = f"{seconds}.{milliseconds//100} giây"
            
            print(f"⏱️  Thời gian xử lý: {time_str} ({processing_time:.2f}s)")
            
            # Tạo PDF từ tất cả ảnh trước khi cập nhật UI
            pdf_filename = None
            if image_paths:
                try:
                    # Tạo tên file PDF với timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pdf_filename = f"IMG_Combine_{timestamp}.pdf"
                    pdf_path = os.path.join(input_path, pdf_filename)
                    
                    # Tạo PDF
                    print(f"\n📄 Đang tạo PDF từ {len(image_paths)} ảnh...")
                    if create_pdf_from_images(image_paths, pdf_path):
                        # Tự động mở PDF
                        print(f"🔍 Đang mở PDF để kiểm tra...")
                        window.after(0, lambda p=pdf_path: open_pdf(p))
                    else:
                        pdf_filename = None  # Không có PDF nếu tạo thất bại
                except Exception as e:
                    print(f"⚠️  Lỗi khi tạo PDF: {e}")
                    pdf_filename = None
            
            window.after(0, lambda: update_ui_with_ai_results(
                final_niem_phong, final_tau, final_ngay_chup, final_thiet_bi, final_tinh,
                len(all_results), error_count, final_thiet_bi_full, pdf_filename, time_str
            ))
        
        except Exception as e:
            window.after(0, lambda: show_ai_error(str(e)))
    
    threading.Thread(target=analyze_thread, daemon=True).start()

def update_ui_with_ai_results(ma_niem_phong, ma_tau_so, ngay_chup, ma_thiet_bi, tinh, total_images, error_count, ma_thiet_bi_full="", pdf_filename=None, processing_time=None):
    """Cập nhật giao diện với kết quả AI"""
    # Tự động điền thông tin
    if ma_niem_phong:
        seal_code_num.delete(0, tk.END)
        seal_code_num.insert(0, ma_niem_phong)
    
    if ma_tau_so:
        tau_num.delete(0, tk.END)
        tau_num.insert(0, ma_tau_so)
    
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
    
    # Cập nhật progress bar lên 100% và ẩn đi
    progress_bar['value'] = total_images
    progress_label.config(text=f"Hoàn thành: {total_images}/{total_images} ảnh")
    window.update()
    # Ẩn progress bar sau một chút
    window.after(500, lambda: progress_frame.grid_remove())
    
    # Hiển thị kết quả - chỉ hiển thị thời gian xử lý
    success_count = total_images - error_count
    result_text = f"✅ Phân tích hoàn tất! {success_count}/{total_images} ảnh thành công"
    if error_count > 0:
        result_text += f" ({error_count} lỗi)"
    
    # Chỉ hiển thị thời gian xử lý
    if processing_time:
        result_text += f"\n⏱️  Thời gian xử lý: {processing_time}"
    
    # Debug info cho console (không hiển thị trong UI)
    if tinh:
        print(f"🔍 Debug - Tỉnh được nhận diện: '{tinh}'")
        if tinh != "Không tìm thấy":
            print(f"✅ Tỉnh đã được tự động chọn trong combobox")
        else:
            print(f"⚠️  Không thể tìm thấy tỉnh tương ứng")
    
    if pdf_filename:
        print(f"📄 Đã tạo PDF: {pdf_filename}")
    
    label_result.config(text=result_text)
    
    # Export kết quả ra console
    export_results_to_console(ma_niem_phong, ma_tau_so, ngay_chup, ma_thiet_bi, tinh, total_images, error_count, ma_thiet_bi_full)
    
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
            
            # Hiển thị thông tin chi tiết về mã thiết bị
            ma_thiet_bi_full = result.get('ma_thiet_bi_full', '')
            if ma_thiet_bi_full and ma_thiet_bi_full != 'Không tìm thấy':
                print(f"     🔧 Mã thiết bị đầy đủ từ AI: '{ma_thiet_bi_full}'")
                if ma_thiet_bi_full.upper().startswith('BTK'):
                    print(f"     ✅ Mã thiết bị hợp lệ (bắt đầu bằng BTK)")
                else:
                    print(f"     ❌ Mã thiết bị không hợp lệ (không bắt đầu bằng BTK)")
                print(f"     📝 Mã thiết bị sẽ được xử lý tách số ở cuối cùng")
            
            # Chi tiết về việc suy ra tỉnh
            tinh = result.get('tinh', 'Không tìm thấy')
            print(f"  📍 Tỉnh: {tinh}")
            
            # Hiển thị thông tin chi tiết về mã tàu và tỉnh
            if 'raw_response' in result:
                raw_response = result['raw_response']
                print(f"     📝 Raw response từ AI:")
                print(f"        {raw_response[:200]}...")
                
                # Lấy thông tin đã được xử lý
                ma_tau_full = result.get('ma_tau_full', '')
                tinh_code = result.get('tinh_code', '')
                tinh_code_original = result.get('tinh_code_original', '')
                ma_tau_so = result.get('ma_tau_so', '')
                
                print(f"     🚢 Mã tàu đầy đủ từ AI: '{ma_tau_full}'")
                
                if tinh_code and ma_tau_so:
                    print(f"     🔍 Phân tích mã tàu '{ma_tau_full}':")
                    print(f"        📍 Chữ cái tỉnh (gốc): '{tinh_code_original}'")
                    print(f"        📍 Chữ cái tỉnh (uppercase): '{tinh_code}'")
                    print(f"        🔢 Số tàu: '{ma_tau_so}'")
                    print(f"        🗺️  Suy ra tỉnh: '{tinh}'")
                    
                    # Kiểm tra mapping
                    if tinh != "Không tìm thấy":
                        print(f"        ✅ Mapping thành công: {tinh_code} → {tinh}")
                        print(f"        🎯 Chương trình đã dùng chữ cái '{tinh_code}' để suy ra tỉnh '{tinh}'")
                    else:
                        print(f"        ❌ Không tìm thấy mapping cho mã: {tinh_code}")
                        print(f"        🔍 Danh sách mã tỉnh có sẵn:")
                        tinh_mapping = create_tinh_mapping()
                        for code, name in list(tinh_mapping.items())[:5]:  # Hiển thị 5 mã đầu
                            print(f"           {code} → {name}")
                        if len(tinh_mapping) > 5:
                            print(f"           ... và {len(tinh_mapping) - 5} mã khác")
                else:
                    print(f"     ⚠️  Mã tàu '{ma_tau_full}' không đúng format (cần: XX 12345)")
                    print(f"     🤔 Không thể suy ra tỉnh từ mã tàu này")
            else:
                print(f"     ⚠️  Không có raw_response để phân tích")
    
    print("\n" + "="*80)

def export_results_to_console(ma_niem_phong, ma_tau_so, ngay_chup, ma_thiet_bi, tinh, total_images, error_count, ma_thiet_bi_full=""):
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
    print(f"  🚢 Số tàu: {ma_tau_so if ma_tau_so else 'Không tìm thấy'}")
    print(f"  📅 Ngày chụp: {ngay_chup if ngay_chup else 'Không tìm thấy'}")
    print(f"  🔧 Mã thiết bị: {ma_thiet_bi if ma_thiet_bi else 'Không tìm thấy'}")
    print(f"  📍 Tỉnh: {tinh if tinh else 'Không tìm thấy'}")
    
    # Hiển thị thông tin chi tiết về mã thiết bị
    if ma_thiet_bi_full and ma_thiet_bi_full != 'Không tìm thấy':
        print("-"*60)
        print("🔧 THÔNG TIN MÃ THIẾT BỊ:")
        print(f"  📱 Mã thiết bị đầy đủ: {ma_thiet_bi_full}")
        print(f"  🔢 Số thiết bị (đã tách): {ma_thiet_bi}")
        print(f"  ✅ Xử lý: {ma_thiet_bi_full} → {ma_thiet_bi}")
    
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
    # Ẩn progress bar khi có lỗi
    progress_frame.grid_remove()

def open_config_manager():
    """Mở chương trình config manager"""
    try:
        # Kiểm tra xem file config_manager.exe có tồn tại không
        if os.path.exists("config_manager.exe"):
            # Mở config_manager.exe
            subprocess.Popen(["config_manager.exe"])
            print("🔧 Đã mở Config Manager")
        elif os.path.exists("config_manager.py"):
            # Fallback: mở config_manager.py bằng Python
            subprocess.Popen([sys.executable, "config_manager.py"])
            print("🔧 Đã mở Config Manager (Python)")
        else:
            messagebox.showerror("Lỗi", "Không tìm thấy file config_manager.exe hoặc config_manager.py!")
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
        
        # Move ảnh và PDF từ folder input sang folder output
        input_path = input_folder_entry.get()
        if input_path and os.path.exists(input_path):
            moved_count = 0
            pdf_count = 0
            for filename in os.listdir(input_path):
                file_path = os.path.join(input_path, filename)
                # Di chuyển ảnh
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    destination_path = os.path.join(full_path, filename)
                    shutil.move(file_path, destination_path)
                    moved_count += 1
                # Di chuyển file PDF (tên bắt đầu bằng IMG_Combine_)
                elif filename.lower().endswith('.pdf') and filename.startswith('IMG_Combine_'):
                    destination_path = os.path.join(full_path, filename)
                    shutil.move(file_path, destination_path)
                    pdf_count += 1
            
            # Tạo thông báo kết quả
            result_msg = "✅ Tạo folder thành công"
            if moved_count > 0:
                result_msg += f" và đã di chuyển {moved_count} ảnh"
            if pdf_count > 0:
                result_msg += f" và {pdf_count} file PDF"
            if moved_count == 0 and pdf_count == 0:
                result_msg += "! (Không có ảnh hoặc PDF để di chuyển)"
            else:
                result_msg += "!"
            label_result.config(text=result_msg)
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

def open_image_optimized(image_path: str):
    img = Image.open(image_path)
    if ENABLE_DOWNSCALE:
        try:
            img = img.convert("RGB")
        except Exception:
            pass
        img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    return img

def generate_with_retry(contents, max_retries: int = 3):
    # Đảm bảo model đã được khởi tạo
    if model is None:
        if not init_google_ai():
            raise RuntimeError("Không thể khởi tạo Google AI")
    
    last_err = None
    for attempt in range(max_retries):
        try:
            return model.generate_content(contents)
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            # Backoff nếu nghi là rate limit hoặc lỗi tạm thời
            if "429" in msg or "rate" in msg or "quota" in msg or "tempor" in msg:
                sleep_s = min(8, 2 ** attempt)
                print(f"⚠️  Lỗi gọi AI (thử {attempt+1}/{max_retries}): {e}. Chờ {sleep_s}s rồi thử lại...")
                time.sleep(sleep_s)
                continue
            else:
                break
    raise last_err if last_err else RuntimeError("generate_with_retry failed")

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

# Nút "Xử lý AI" - luôn enable vì sẽ lazy load khi nhấn
button_analyze = tk.Button(button_frame, text="🤖 Xử lý AI", command=analyze_images_with_ai, 
                          bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                          state="normal")
button_analyze.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

# Nút "Tạo folder"
button_convert = tk.Button(button_frame, text="Tạo folder", command=create_folder)
button_convert.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

# Label hiển thị trạng thái AI - lazy check, không kiểm tra ngay
ai_status_text = "⏳ AI: Chưa kiểm tra (sẽ kiểm tra khi sử dụng)"
label_ai_status = tk.Label(path_frame, text=ai_status_text, 
                          fg="gray", font=("Arial", 9))
label_ai_status.grid(row=3, column=0, columnspan=2, padx=5, pady=2)

def update_ai_status():
    """Cập nhật trạng thái AI trên UI"""
    if AI_AVAILABLE is None:
        label_ai_status.config(text="⏳ AI: Chưa kiểm tra (sẽ kiểm tra khi sử dụng)", fg="gray")
    elif AI_AVAILABLE:
        label_ai_status.config(text="✅ AI: Sẵn sàng", fg="green")
    else:
        label_ai_status.config(text="❌ AI: Cần cấu hình API Key", fg="red")

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
label_result.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="ew")

# Progress bar và label tiến trình
progress_frame = tk.Frame(window)
progress_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

progress_label = tk.Label(progress_frame, text="", font=("Arial", 9))
progress_label.pack(side=tk.TOP, pady=(0, 5))

progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
progress_bar.pack(side=tk.TOP, fill=tk.X, expand=True)

# Ẩn progress bar ban đầu
progress_frame.grid_remove()

# Cấu hình grid weights
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.rowconfigure(0, weight=1)

window.mainloop()
