import google.generativeai as genai
from PIL import Image
import os
import concurrent.futures
# import csv  # <-- ### ĐÃ BỎ ### Không cần dùng thư viện này nữa
import time
import json
from tqdm import tqdm
from collections import Counter

# --- PHẦN CẤU HÌNH ---
# Vui lòng thay đổi các giá trị dưới đây cho phù hợp

# 1. Dán API Key của bạn vào đây
try:
    # --- QUAN TRỌNG: Hãy thay thế bằng API Key của chính bạn ---
    GOOGLE_API_KEY = "AIzaSyAylYXbqPkbqBTGc7Spct9-EFQA0lguKaI"
    genai.configure(api_key=GOOGLE_API_KEY)
except AttributeError:
    print("Lỗi: Vui lòng cung cấp API Key của bạn trong biến GOOGLE_API_KEY.")
    exit()

# 2. Tên file CSV để lưu kết quả
# OUTPUT_CSV_FILE = "ket_qua_tong_hop.csv" # <-- ### ĐÃ BỎ ###

# 3. Số luồng xử lý song song. 10 là một con số tốt để bắt đầu.
MAX_WORKERS = 5
# Các định dạng file ảnh hợp lệ
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')

# --- HÀM XỬ LÝ CHO MỖI LUỒNG ---

# Khởi tạo model một lần duy nhất để tái sử dụng
model = genai.GenerativeModel('gemini-2.5-flash-lite')


# Đây là prompt "tổng" để hỏi tất cả thông tin cùng lúc
# và yêu cầu trả về dưới dạng JSON.
MASTER_PROMPT = """
Phân tích hình ảnh này và trích xuất các thông tin sau đây.
Trả lời bằng một đối tượng JSON hợp lệ duy nhất.
Các key của JSON phải là: "ma_niem_phong", "ma_tau", "ngay_chup", "ma_thiet_bi".

- "ma_niem_phong": Tìm mã niêm phong, ví dụ "SEAL A 123456", "K 678901", hoặc "Z012345". Chỉ lấy phần gồm 1 ký tự chữ và 6 số, ví dụ "A123456", "K678901", hoặc "Z012345". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_tau": Tìm mã tàu, ví dụ "BT 97793 TS". Chỉ lấy phần "BT" và 5 số tiếp theo, ví dụ "BT97793". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ngay_chup": Tìm ngày tháng trên ảnh, ví dụ "05/08/2025". Chuyển thành định dạng 6 số "DDMMYY", ví dụ "050825". Nếu không đúng định dạng, trả về "Không tìm thấy".
- "ma_thiet_bi": Tìm mã thiết bị, thường bắt đầu bằng BTK, ví dụ "BTK123456". Chỉ lấy 6 số cuối, ví dụ "123456". Nếu không đúng định dạng, trả về "Không tìm thấy".

Quan trọng: Chỉ trả về đối tượng JSON, không thêm bất kỳ văn bản giải thích nào khác.
"""


def process_image_for_all_data(image_path: str) -> dict:
    """
    Hàm này xử lý một ảnh duy nhất, gửi 1 prompt tổng hợp đến API
    và parse kết quả JSON trả về.
    """
    file_name = os.path.basename(image_path)
    try:
        img = Image.open(image_path)
        response = model.generate_content([MASTER_PROMPT, img])
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(cleaned_text)
        data['file_name'] = file_name
        return data
    except json.JSONDecodeError:
        return {"file_name": file_name, "error": "AI không trả về JSON hợp lệ", "raw_response": response.text}
    except FileNotFoundError:
        return {"file_name": file_name, "error": "Không tìm thấy file."}
    except Image.UnidentifiedImageError:
        return {"file_name": file_name, "error": "File ảnh bị lỗi hoặc không thể đọc."}
    except Exception as e:
        return {"file_name": file_name, "error": f"Lỗi không xác định: {e}"}


# --- CHẠY CHƯƠNG TRÌNH CHÍNH ---
if __name__ == "__main__":

    while True:
        image_folder_path = input("Vui lòng nhập đường dẫn đến thư mục chứa ảnh và nhấn Enter:\n"
                                  "(Ví dụ: C:\\Users\\TenBan\\Pictures\\Seals hoặc /home/TenBan/seals_test)\n> ")
        if os.path.isdir(image_folder_path):
            break
        else:
            print("\n❌ Lỗi: Đường dẫn không tồn tại hoặc không phải là một thư mục. Vui lòng thử lại.\n")

    total_start_time = time.perf_counter()

    # 1. Tìm tất cả các file ảnh
    print(f"\n🔍 Đang quét ảnh trong thư mục: '{image_folder_path}'...")
    image_paths = []
    for root, _, files in os.walk(image_folder_path):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                image_paths.append(os.path.join(root, file))

    if not image_paths:
        print(f"❌ Không tìm thấy ảnh nào trong thư mục '{image_folder_path}'.")
        exit()

    num_images = len(image_paths)
    print(f"✅ Tìm thấy {num_images} ảnh. Bắt đầu xử lý với {MAX_WORKERS} luồng...")

    # 2. Xử lý song song
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results_iterator = executor.map(process_image_for_all_data, image_paths)
        all_results = list(tqdm(results_iterator, total=num_images, desc="🤖 Đang xử lý ảnh"))


    # 4. Phân tích và tổng hợp kết quả cuối cùng
    print("\n📈 Đang tổng hợp kết quả...")

    # Khởi tạo các bộ đếm
    niem_phong_counts = Counter()
    tau_counts = Counter()
    ngay_chup_counts = Counter()
    ma_thiet_bi_counts = Counter()
    error_count = 0

    # Duyệt qua tất cả kết quả để đếm
    for result in all_results:
        if 'error' in result and result['error']:
            error_count += 1
            continue # Bỏ qua các kết quả lỗi và đi tiếp

        ma_niem_phong = result.get('ma_niem_phong', '').strip()
        ma_tau = result.get('ma_tau', '').strip()
        ngay_chup = result.get('ngay_chup', '').strip()
        ma_thiet_bi = result.get('ma_thiet_bi', '').strip()

        if ma_niem_phong and ma_niem_phong.lower() != 'không tìm thấy':
            niem_phong_counts[ma_niem_phong] += 1

        if ma_tau and ma_tau.lower() != 'không tìm thấy':
            tau_counts[ma_tau] += 1

        if ngay_chup and ngay_chup.lower() != 'không tìm thấy':
            ngay_chup_counts[ngay_chup] += 1

        if ma_thiet_bi and ma_thiet_bi.lower() != 'không tìm thấy':
            ma_thiet_bi_counts[ma_thiet_bi] += 1

    # Tìm giá trị xuất hiện nhiều nhất từ mỗi bộ đếm
    final_niem_phong = niem_phong_counts.most_common(1)[0][0] if niem_phong_counts else "Không có dữ liệu"
    final_tau = tau_counts.most_common(1)[0][0] if tau_counts else "Không có dữ liệu"
    final_ngay_chup = ngay_chup_counts.most_common(1)[0][0] if ngay_chup_counts else "Không có dữ liệu"
    final_thiet_bi = ma_thiet_bi_counts.most_common(1)[0][0] if ma_thiet_bi_counts else "Không có dữ liệu"

    total_end_time = time.perf_counter()
    total_duration = total_end_time - total_start_time

    # --- ### THAY ĐỔI ### In ra kết quả cuối cùng ---
    print("\n" + "="*50)
    print("✨ HOÀN TẤT! ✨")
    print("-" * 50)
    print("📋 KẾT QUẢ TỔNG HỢP (Dựa trên tần suất cao nhất)")
    print(f"  - Mã niêm phong phổ biến nhất: {final_niem_phong}")
    print(f"  - Mã tàu phổ biến nhất:        {final_tau}")
    print(f"  - Ngày chụp phổ biến nhất:     {final_ngay_chup}")
    print(f"  - Mã thiết bị phổ biến nhất:   {final_thiet_bi}")
    print("-" * 50)
    print(f"Tổng số ảnh đã xử lý: {num_images}")
    if error_count > 0:
        print(f"Số ảnh xử lý thành công: {num_images - error_count}")
        print(f"Số ảnh bị lỗi: {error_count}")
    print(f"Tổng thời gian thực thi: {total_duration:.2f} giây")
    print("=" * 50)