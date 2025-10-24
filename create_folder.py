
import tkinter as tk
from tkcalendar import Calendar, DateEntry
from ttkwidgets.autocomplete import AutocompleteCombobox, AutocompleteEntry  # Import AutocompleteEntry
from tkinter import scrolledtext, filedialog, messagebox
import os
import shutil
from PIL import Image, ImageTk
import webbrowser


selected_image_paths = []
image_labels = []
remove_buttons = []
CONFIG_FILE = "folder_path_config.txt"


def show_image(index):
    webbrowser.open(selected_image_paths[index])

def remove_image_and_close(index, window_to_close):
    remove_image(index)
    window_to_close.destroy()

def add_images():
    global selected_image_paths, image_labels, remove_buttons
    new_image_paths = filedialog.askopenfilenames(
        title="Chọn ảnh", filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")]
    )
    if not new_image_paths:
        return

    for path in new_image_paths:
        if path not in selected_image_paths:
            selected_image_paths.append(path)
            index = len(selected_image_paths) - 1

            # Tạo frame để chứa ảnh và nút xóa (thay đổi cách bố trí)
            image_container = tk.Frame(image_display_frame)
            image_container.pack(side=tk.LEFT, padx=5, pady=5)

            # Hiển thị ảnh (giảm kích thước ảnh)
            img = Image.open(path)
            img.thumbnail((100, 100))  # Giảm kích thước ảnh hiển thị
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(image_container, image=photo)
            label.image = photo  # Giữ tham chiếu đến ảnh
            label.pack()

            # Thêm sự kiện click vào ảnh để xem chi tiết
            label.bind("<Button-1>", lambda event, index=index: show_image(index))

            # Thêm nút xóa
            remove_button = tk.Button(image_container, text="Xóa", command=lambda index=index: remove_image(index))
            remove_button.pack()

            image_labels.append(label)
            remove_buttons.append(remove_button)

def remove_image(index):
    global selected_image_paths, image_labels, remove_buttons, current_image_column
    del selected_image_paths[index]
    image_labels[index].destroy()
    del image_labels[index]
    remove_buttons[index].destroy()
    del remove_buttons[index]
    rearrange_images()

def rearrange_images():
    global current_image_column
    current_image_column = 0
    for widget in image_display_frame.winfo_children():
        widget.destroy()
    for i in range(len(selected_image_paths)):
        # Tạo lại các label và nút xóa cho các ảnh còn lại
        image_path = selected_image_paths[i]
        pair_frame = tk.Frame(image_display_frame)
        pair_frame.grid(row=0, column=current_image_column, padx=5, pady=5)
        current_image_column += 1

        img = Image.open(image_path)
        img.thumbnail((100, 100))
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(pair_frame, image=photo)
        label.image = photo
        label.pack()

        label.bind("<Button-1>", lambda event, index=i: show_image(index))

        remove_button = tk.Button(
            pair_frame, text="Xóa", command=lambda index=i: remove_image(index)
        )
        remove_button.pack()

        image_labels.append(label)
        remove_buttons.append(remove_button)


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
    global folder_path, selected_image_paths, image_labels, remove_buttons
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
        for image_path in selected_image_paths:
            image_name = os.path.basename(image_path)
            destination_path = os.path.join(full_path, image_name)
            shutil.move(image_path, destination_path)
        selected_image_paths = []

        # Xóa các label và nút xóa ảnh
        for label in image_labels:
            label.destroy()
        for button in remove_buttons:
            button.destroy()
        image_labels = []
        remove_buttons = []

        label_result.config(text="Cục ta cục táccccccc!")
        # Xóa mã niêm phong đã dùng trong file niêm_phong.txt
        valid_seal_codes.remove(ma_niem_phong)
        with open("niem_phong.txt", "w", encoding="utf-8") as f:
            for code in valid_seal_codes:
                f.write(code + "\n")

        # Cập nhật hiển thị số mã niêm phong còn lại
        update_remaining_seal_codes()
    except Exception as e:
        label_result.config(text=f"Lỗi: {e}")

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

# Frame chứa ảnh (sử dụng Canvas và Scrollbar để cuộn)
image_frame = tk.LabelFrame(window, text="Ảnh đính kèm")
image_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

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



# Frame chứa ảnh (di chuyển sang bên phải, cùng hàng với input_frame)
image_frame = tk.LabelFrame(window, text="Ảnh đính kèm")
image_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Canvas để cuộn ảnh nếu cần thiết
canvas = tk.Canvas(image_frame)
canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # Đặt canvas ở trên cùng và cho phép mở rộng

# Scrollbar cho Canvas (đặt fill=tk.X)
scrollbar = tk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=canvas.xview)
scrollbar.pack(side=tk.BOTTOM, fill=tk.X)  # Đặt scrollbar ở dưới cùng và cho phép mở rộng theo chiều ngang

# Frame chứa các ảnh
image_display_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=image_display_frame, anchor='nw')

# Cấu hình Canvas để cuộn
image_display_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.configure(xscrollcommand=scrollbar.set)

# Nút "Thêm ảnh" (đặt sau khi đã tạo scrollbar)
button_them_anh = tk.Button(image_frame, text="Thêm ảnh", command=add_images)
button_them_anh.pack(pady=5)  # Đặt nút dưới cùng

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

# Cập nhật ban đầu khi chương trình chạy
update_remaining_seal_codes()

# Label kết quả
label_result = tk.Label(window, text="")
label_result.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

folder_path = load_folder_path()  # Tải đường dẫn đã lưu
folder_path_entry.insert(0, folder_path)

window.iconbitmap("iconZ.ico")

window.mainloop()
