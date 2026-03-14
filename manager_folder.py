import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, UnidentifiedImageError
import os
import webbrowser
import shutil


global image_files, image_labels, selected_images, folder_path, image_frame

image_files = []
image_labels = []
selected_images = []
folder_path = ""

def browse_folder():
    global image_labels, selected_images, folder_path_label, folder_path, image_files
    folder_path = filedialog.askdirectory()
    if folder_path:
        # Clear previous image widgets (now references the correct image_frame)
        for widget in image_frame.winfo_children():
            widget.destroy()

        image_labels = []
        selected_images = []
        folder_name = os.path.basename(folder_path)
        folder_path_label.config(text=folder_name)

        image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]

        for i, image_file in enumerate(image_files):
            image_path = os.path.join(folder_path, image_file)
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)

                image_label_frame = tk.Frame(image_frame)
                image_label_frame.pack(side=tk.LEFT, padx=5, pady=5)

                label = tk.Label(image_label_frame, image=photo)
                label.image = photo
                label.bind("<Button-1>", lambda event, path=image_path: open_image(path))
                label.pack()

                var = tk.IntVar()
                check_button = tk.Checkbutton(image_label_frame, variable=var, command=lambda i=i, var=var: toggle_selection(i, var))
                check_button.pack()

                image_labels.append((image_label_frame, var))
            except Exception as e:
                print(f"Error loading image {image_file}: {e}")

        image_frame.update_idletasks()   # Update the frame layout
        canvas.configure(scrollregion=canvas.bbox("all"))  # Update scroll region after adding images

def toggle_selection(index, var):
    global selected_images
    if var.get() == 1:
        selected_images.append(index)
    else:
        selected_images.remove(index)

def delete_selected_images():
    global image_labels, selected_images, image_files
    if selected_images:
        confirm = messagebox.askyesno("Xác nhận xóa", "Bạn có chắc chắn muốn xóa các ảnh đã chọn?")
        if confirm:
            for index in sorted(selected_images, reverse=True):
                image_labels[index][0].destroy()
                del image_labels[index]
                del image_files[index]
            selected_images = []

def open_image(image_path):
    webbrowser.open(image_path)


def create_new_folder():
    global new_folder_entry, image_files, image_labels, selected_images

    new_folder_name = new_folder_entry.get()
    if not new_folder_name:  # Kiểm tra nếu tên thư mục trống
        messagebox.showerror("Lỗi", "Vui lòng nhập tên thư mục mới.")
        return

    if not selected_images:  # Kiểm tra nếu không có ảnh được chọn
        messagebox.showerror("Lỗi", "Vui lòng chọn ảnh để di chuyển.")
        return

    new_folder_name = new_folder_entry.get()
    new_folder_path = filedialog.askdirectory(title="Chọn vị trí thư mục mới")

    # Kiểm tra nếu người dùng đã chọn đường dẫn
    if new_folder_path:
        new_folder_path = os.path.join(new_folder_path, new_folder_name)

    new_folder_path = os.path.join(new_folder_path, new_folder_name)

    try:
        os.makedirs(new_folder_path, exist_ok=True)  # Tạo thư mục, nếu đã tồn tại thì không báo lỗi
        for index in sorted(selected_images, reverse=True):
            image_file = image_files.pop(index)  # Lấy và xóa khỏi danh sách
            source_path = os.path.join(folder_path, image_file)
            destination_path = os.path.join(new_folder_path, image_file)
            shutil.move(source_path, destination_path)

            image_labels[index][0].destroy()
            del image_labels[index]

        selected_images = []
        messagebox.showinfo("Thành công", f"Đã tạo thư mục và di chuyển ảnh vào: {new_folder_name}")
        new_folder_entry.delete(0, tk.END)

        # Refresh lại giao diện sau khi di chuyển
        browse_folder()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể tạo thư mục hoặc di chuyển ảnh: {e}")


def update_canvas_scrollregion(event):  # Add event argument here
    canvas.configure(scrollregion=canvas.bbox("all"))

window = tk.Tk()
window.title("Trình xem ảnh")
window.iconbitmap("iconZ.ico")

# Frame chính (main_frame)
main_frame = tk.Frame(window)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Frame chứa chức năng duyệt và xóa ảnh
browse_delete_frame = tk.LabelFrame(main_frame, text="Duyệt & Xóa ảnh")
browse_delete_frame.grid(row=0, column=0, sticky="nsew")

browse_button = tk.Button(browse_delete_frame, text="Chọn thư mục", command=browse_folder)
browse_button.grid(row=0, column=0, padx=5, pady=5)

folder_path_label = tk.Label(browse_delete_frame, text="")
folder_path_label.grid(row=1, column=0, padx=5, pady=5)



# Frame chứa chức năng tạo thư mục
new_folder_frame = tk.LabelFrame(main_frame, text="Tạo thư mục mới")
new_folder_frame.grid(row=0, column=1, sticky="nsew")

new_folder_label = tk.Label(new_folder_frame, text="Tên thư mục:")
new_folder_label.pack(side=tk.LEFT, padx=5, pady=5)

new_folder_entry = tk.Entry(new_folder_frame)
new_folder_entry.pack(side=tk.LEFT, padx=5, pady=5)

create_folder_button = tk.Button(new_folder_frame, text="Tạo thư mục", command=create_new_folder)
create_folder_button.pack(side=tk.LEFT, padx=5, pady=5)

delete_button = tk.Button(new_folder_frame, text="Xóa ảnh đã chọn", command=delete_selected_images)
delete_button.pack(side=tk.BOTTOM, padx=5, pady=5)

# Canvas Setup (Modified)
canvas = tk.Canvas(main_frame)
canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")

# Scrollbars Setup (Modified)
v_scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
v_scrollbar.grid(row=1, column=2, sticky="ns")
h_scrollbar = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
h_scrollbar.grid(row=2, column=0, columnspan=2, sticky="ew")

canvas['yscrollcommand'] = v_scrollbar.set
canvas['xscrollcommand'] = h_scrollbar.set

# Frame for Images (Modified)
image_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=image_frame, anchor="nw")

image_frame.bind("<Configure>", update_canvas_scrollregion)

window.mainloop()
