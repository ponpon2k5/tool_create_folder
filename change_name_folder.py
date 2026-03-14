import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog
import os
from PIL import Image, ImageTk
import webbrowser


def parse_folder_name(folder_name):
    parts = folder_name.split(".")
    if len(parts) == 7 and parts[0] in TINH_MAPPING and parts[1] in DAI_LY_MAPPING:
        return {
            "tinh": TINH_MAPPING[parts[0]],
            "dai_ly": DAI_LY_MAPPING[parts[1]],
            "so_tau": parts[2],
            "ma_thiet_bi": parts[3],
            "ma_niem_phong": parts[4],
            "ngay": parts[5],
            "cong_no": parts[6],
        }
    else:
        return None

def browse_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        global current_folder_path
        current_folder_path = folder_path
        folder_name = os.path.basename(folder_path)
        entry.delete(0, tk.END)
        entry.insert(0, folder_name)
        update_fields()
        show_images()

def update_fields():
    folder_name = entry.get()
    data = parse_folder_name(folder_name)
    if data:
        tinh_var.set(data["tinh"])
        dai_ly_var.set(data["dai_ly"])
        so_tau_var.set(data["so_tau"])
        ma_thiet_bi_var.set(data["ma_thiet_bi"])
        ma_niem_phong_var.set(data["ma_niem_phong"])
        ngay_var.set(data["ngay"])
        cong_no_str = data["cong_no"]
        if cong_no_str == "1":
            cong_no_var.set("Yes")
        elif cong_no_str == "0":
            cong_no_var.set("No")
        else:
            cong_no_var.set("Unknow")
    else:
        # Xóa các trường nếu tên thư mục không hợp lệ
        for var in [tinh_var, dai_ly_var, so_tau_var, ma_thiet_bi_var, ma_niem_phong_var, ngay_var, cong_no_var]:
            var.set("")

    ma_niem_phong_entry.config(state="readonly")

def rename_folder():
    global current_folder_path
    if current_folder_path:
        old_name = os.path.basename(current_folder_path)
        new_name = entry.get()
        if new_name != old_name:
            new_path = os.path.join(os.path.dirname(current_folder_path), new_name)
            try:
                os.rename(current_folder_path, new_path)
                current_folder_path = new_path  # Cập nhật đường dẫn thư mục hiện tại
                tk.messagebox.showinfo("Thành công", "Đổi tên thư mục thành công!")
            except OSError as e:
                tk.messagebox.showerror("Lỗi", f"Không thể đổi tên thư mục: {e}")


def update_folder_name(*args):
    tinh = tinh_var.get()
    dai_ly = dai_ly_var.get()
    so_tau = so_tau_var.get()
    ma_thiet_bi = ma_thiet_bi_var.get()
    ma_niem_phong = ma_niem_phong_var.get()
    ngay = ngay_var.get()
    cong_no = cong_no_var.get()
    if cong_no == "Yes":
        cong_no = "1"
    elif cong_no == "No":
        cong_no = "0"
    elif cong_no == "Unknow":
        cong_no = "3"

    # Tìm mã tỉnh và mã đại lý từ ánh xạ ngược
    ma_tinh = next((k for k, v in TINH_MAPPING.items() if v == tinh), "")
    ma_dai_ly = next((k for k, v in DAI_LY_MAPPING.items() if v == dai_ly), "")

    # Cập nhật tên thư mục trong ô nhập liệu
    new_folder_name = f"{ma_tinh}.{ma_dai_ly}.{so_tau}.{ma_thiet_bi}.{ma_niem_phong}.{ngay}.{cong_no}"
    entry.delete(0, tk.END)
    entry.insert(0, new_folder_name)

def show_images():
    global current_folder_path, image_references
    if current_folder_path:
        for widget in image_frame.winfo_children():
            widget.destroy()

        image_files = [f for f in os.listdir(current_folder_path) if f.endswith((".jpg", ".jpeg", ".png"))]
        image_references = []

        # Frame chứa scrollbar
        scrollbar_frame = ttk.Frame(image_frame, padding=10)  # Padding để tăng kích thước thanh cuộn
        scrollbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Tạo canvas để chứa các ảnh
        canvas = tk.Canvas(image_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tạo scrollbar bên trong frame
        scrollbar = ttk.Scrollbar(scrollbar_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollbar.pack(fill=tk.X, expand=True)  # Scrollbar chiếm toàn bộ chiều rộng của frame

        canvas.configure(xscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Tạo frame bên trong canvas để chứa các ảnh
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        for i, image_file in enumerate(image_files):
            image_path = os.path.join(current_folder_path, image_file)
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                image_references.append(photo)
                label = tk.Label(inner_frame, image=photo)
                label.image_path = image_path
                label.bind("<Button-1>", open_image)
                label.grid(row=0, column=i, padx=5, pady=5)

                delete_button = ttk.Button(inner_frame, text="Xóa", command=lambda path=image_path: delete_image(path))
                delete_button.grid(row=1, column=i, padx=5, pady=5)

            except Exception as e:
                print(f"Không thể mở ảnh {image_file}: {e}")
def open_image(event):
    webbrowser.open(event.widget.image_path)  # Mở ảnh bằng trình duyệt mặc định

def delete_image(image_path):
    if tk.messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa ảnh này?"):
        try:
            os.remove(image_path)
            show_images()  # Cập nhật lại danh sách ảnh sau khi xóa
        except Exception as e:
            tk.messagebox.showerror("Lỗi", f"Không thể xóa ảnh: {e}")

def load_mappings(tinh_config_file, dai_ly_config_file):
    tinh_mapping = {}
    dai_ly_mapping = {}

    with open(tinh_config_file, "r", encoding="utf-8") as f:
        for line in f:
            value, key = line.strip().split(":")
            tinh_mapping[key.strip()] = value.strip()

    with open(dai_ly_config_file, "r", encoding="utf-8") as f:
        for line in f:
            value, key = line.strip().split(":")
            dai_ly_mapping[key.strip()] = value.strip()

    return tinh_mapping, dai_ly_mapping

def show_context_menu(event):
    context_menu = tk.Menu(radio_frame, tearoff=0)
    context_menu.add_command(label="Unknow", command=lambda: set_cong_no("Unknow"))
    context_menu.add_command(label="Yes", command=lambda: set_cong_no("Yes"))
    context_menu.add_command(label="No", command=lambda: set_cong_no("No"))
    context_menu.post(event.x_root, event.y_root)

def set_cong_no(value):
    cong_no_var.set(value)
    update_folder_name()


TINH_MAPPING, DAI_LY_MAPPING = load_mappings("ma_tinh_config.txt", "dai_ly_config.txt")



# Tạo cửa sổ chính
window = tk.Tk()
window.title("Change Folder Name")
window.iconbitmap("iconZ.ico")

# Frame chứa thông tin thư mục
info_frame = ttk.Frame(window, padding=10)
info_frame.grid(row=0, column=0, sticky="nsew")

# Tạo và đặt nhãn và ô nhập liệu (mở rộng ô nhập liệu)
ttk.Label(info_frame, text="Folder name:").grid(row=0, column=0, sticky="w")
entry = ttk.Entry(info_frame, width=40)  # Mở rộng ô nhập liệu
entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)  # Cho ô nhập liệu chiếm 2 cột

# Các biến Tkinter để lưu trữ giá trị của các trường
tinh_var = tk.StringVar()
dai_ly_var = tk.StringVar()
so_tau_var = tk.StringVar()
ma_thiet_bi_var = tk.StringVar()
ma_niem_phong_var = tk.StringVar()
ngay_var = tk.StringVar()
cong_no_var = tk.StringVar(value="")

# Tạo và đặt các nhãn và combobox/entry cho các trường
for i, (label, var) in enumerate([
    ("Tỉnh:", tinh_var),
    ("Đại lý:", dai_ly_var),
    ("Số tàu:", so_tau_var),
    ("Mã thiết bị:", ma_thiet_bi_var),
    ("Mã niêm phong:", ma_niem_phong_var),
    ("Ngày:", ngay_var),
]):
    ttk.Label(info_frame, text=label).grid(row=i + 1, column=0, sticky="w")
    if i < 2:  # Tỉnh và đại lý là combobox
        combobox = ttk.Combobox(info_frame, textvariable=var,
                                values=list(TINH_MAPPING.values() if i == 0 else DAI_LY_MAPPING.values()), width=34)
        combobox.grid(row=i + 1, column=1, padx=5, pady=5)
    else:  # Các trường khác là entry
        entry_field = ttk.Entry(info_frame, textvariable=var, width=37)
        entry_field.grid(row=i + 1, column=1, padx=5, pady=5)

# Frame chứa các nút
button_frame = ttk.Frame(window, padding=10)
button_frame.grid(row=1, column=0, sticky="ew")

# Frame chứa Radiobutton cho công nợ
radio_frame = ttk.Frame(info_frame)
radio_frame.grid(row=7, column=1, sticky="w")

# Biến Tkinter để lưu trữ giá trị công nợ
cong_no_var = tk.StringVar(value="")

# Tạo và đặt các Radiobutton cho trường công nợ
ttk.Label(info_frame, text="Công nợ:").grid(row=7, column=0, sticky="w")
unknow_radio = ttk.Radiobutton(radio_frame, text="Unknow", variable=cong_no_var, value="Unknow", command=update_folder_name)
unknow_radio.pack(side="left")
yes_radio = ttk.Radiobutton(radio_frame, text="Yes", variable=cong_no_var, value="Yes", command=update_folder_name)
yes_radio.pack(side="left")
no_radio = ttk.Radiobutton(radio_frame, text="No", variable=cong_no_var, value="No", command=update_folder_name)
no_radio.pack(side="left")
# Liên kết sự kiện click chuột phải vào radio_frame để hiển thị menu ngữ cảnh
radio_frame.bind("<Button-3>", show_context_menu)
# Biến global để lưu trữ đường dẫn thư mục hiện tại
current_folder_path = None

# Thêm trace cho các biến để theo dõi sự thay đổi
for var in [tinh_var, dai_ly_var, so_tau_var, ma_thiet_bi_var, ma_niem_phong_var, ngay_var]:
    var.trace_add("write", update_folder_name)

# Thêm nút "Import thư mục"
ttk.Button(button_frame, text="Import thư mục", command=browse_folder).grid(row=0, column=0, padx=5, pady=5)

# Thêm nút "Đổi tên thư mục"
ttk.Button(button_frame, text="Đổi tên thư mục", command=rename_folder).grid(row=0, column=1, padx=5, pady=5)

# Create entry for mã niêm phong (make it read-only initially)
ma_niem_phong_entry = ttk.Entry(info_frame, textvariable=ma_niem_phong_var, state="readonly", width=37)
ma_niem_phong_entry.grid(row=5, column=1, padx=5, pady=5)

# Frame chứa ảnh
image_frame = ttk.Frame(window, padding=10,)
image_frame.grid(row=2, column=0, sticky="nsew")

# Biến global để lưu trữ tham chiếu đến ảnh
image_references = []



window.mainloop()
