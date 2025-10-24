import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import re
from datetime import datetime

class ConfigManager:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Quản lý Cấu hình")
        self.window.geometry("900x700")
        self.window.iconbitmap("iconZ.ico")
        
        # Tạo notebook (tabs)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tạo các tab
        self.create_seal_code_tab()
        self.create_api_tab()
        self.create_daily_tab()
        self.create_tinh_tab()
        
        # Load dữ liệu
        self.load_seal_codes()
        self.load_api_config()
        self.load_daily_config()
        self.load_tinh_config()
        
    def create_seal_code_tab(self):
        """Tab quản lý mã niêm phong"""
        self.seal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.seal_frame, text="Mã Niêm Phong")
        
        # Frame chính
        main_frame = tk.Frame(self.seal_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame nhập liệu
        input_frame = tk.LabelFrame(main_frame, text="Thêm/Sửa Mã Niêm Phong")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mã niêm phong
        tk.Label(input_frame, text="Mã niêm phong (1 chữ + 6 số):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.seal_entry = tk.Entry(input_frame, width=15)
        self.seal_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Validation cho mã niêm phong
        def validate_seal_input(event):
            value = self.seal_entry.get().upper()
            filtered_value = ''.join(c for c in value if c.isalnum())
            if len(filtered_value) > 7:
                filtered_value = filtered_value[:7]
            if filtered_value != value:
                self.seal_entry.delete(0, tk.END)
                self.seal_entry.insert(0, filtered_value)
        
        self.seal_entry.bind('<KeyRelease>', validate_seal_input)
        
        # Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        tk.Button(button_frame, text="Thêm", command=self.add_seal_code).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Sửa", command=self.edit_seal_code).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Xóa", command=self.delete_seal_code).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Import", command=self.import_seal_codes).pack(side=tk.LEFT, padx=2)
        
        # Listbox hiển thị mã niêm phong
        list_frame = tk.LabelFrame(main_frame, text="Danh sách Mã Niêm Phong")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.seal_listbox = tk.Listbox(list_frame, font=("Arial", 10), 
                                      yscrollcommand=scrollbar.set, selectmode=tk.SINGLE)
        self.seal_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.seal_listbox.yview)
        
        # Bind double click để sửa
        self.seal_listbox.bind('<Double-1>', self.on_seal_double_click)
        
    def create_api_tab(self):
        """Tab quản lý API Gemini"""
        self.api_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.api_frame, text="API Gemini")
        
        main_frame = tk.Frame(self.api_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame cấu hình
        config_frame = tk.LabelFrame(main_frame, text="Cấu hình API")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # API Key
        tk.Label(config_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.api_key_entry = tk.Entry(config_frame, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Model
        tk.Label(config_frame, text="Model:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.model_var = tk.StringVar(value="gemini-2.5-flash-lite")
        model_combo = ttk.Combobox(config_frame, textvariable=self.model_var, 
                                  values=["gemini-2.5-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"],
                                  width=47)
        model_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Buttons
        button_frame = tk.Frame(config_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        tk.Button(button_frame, text="Lưu", command=self.save_api_config).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Hiện/Ẩn", command=self.toggle_api_key_visibility).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Test API", command=self.test_api).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.api_status_label = tk.Label(main_frame, text="")
        self.api_status_label.pack(pady=5)
        
    def create_daily_tab(self):
        """Tab quản lý đại lý"""
        self.daily_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.daily_frame, text="Đại Lý")
        
        main_frame = tk.Frame(self.daily_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame nhập liệu
        input_frame = tk.LabelFrame(main_frame, text="Thêm/Sửa Đại Lý")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tên đại lý
        tk.Label(input_frame, text="Tên đại lý:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.daily_name_entry = tk.Entry(input_frame, width=30)
        self.daily_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Mã rút gọn
        tk.Label(input_frame, text="Mã rút gọn:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.daily_code_entry = tk.Entry(input_frame, width=15)
        self.daily_code_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        tk.Button(button_frame, text="Thêm", command=self.add_daily).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Sửa", command=self.edit_daily).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Xóa", command=self.delete_daily).pack(side=tk.LEFT, padx=2)
        
        # Treeview hiển thị đại lý
        tree_frame = tk.LabelFrame(main_frame, text="Danh sách Đại Lý")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Tên đại lý", "Mã rút gọn")
        self.daily_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.daily_tree.heading(col, text=col)
            self.daily_tree.column(col, width=200)
        
        scrollbar_daily = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.daily_tree.yview)
        self.daily_tree.configure(yscrollcommand=scrollbar_daily.set)
        
        self.daily_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_daily.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double click để sửa
        self.daily_tree.bind('<Double-1>', self.on_daily_double_click)
        
    def create_tinh_tab(self):
        """Tab quản lý tỉnh thành"""
        self.tinh_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tinh_frame, text="Tỉnh Thành")
        
        main_frame = tk.Frame(self.tinh_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame nhập liệu
        input_frame = tk.LabelFrame(main_frame, text="Thêm/Sửa Tỉnh Thành")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tên tỉnh
        tk.Label(input_frame, text="Tên tỉnh:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tinh_name_entry = tk.Entry(input_frame, width=30)
        self.tinh_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Mã tỉnh
        tk.Label(input_frame, text="Mã tỉnh:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tinh_code_entry = tk.Entry(input_frame, width=15)
        self.tinh_code_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Buttons
        button_frame = tk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        tk.Button(button_frame, text="Thêm", command=self.add_tinh).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Sửa", command=self.edit_tinh).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Xóa", command=self.delete_tinh).pack(side=tk.LEFT, padx=2)
        
        # Treeview hiển thị tỉnh thành
        tree_frame = tk.LabelFrame(main_frame, text="Danh sách Tỉnh Thành")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Tên tỉnh", "Mã tỉnh")
        self.tinh_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tinh_tree.heading(col, text=col)
            self.tinh_tree.column(col, width=200)
        
        scrollbar_tinh = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tinh_tree.yview)
        self.tinh_tree.configure(yscrollcommand=scrollbar_tinh.set)
        
        self.tinh_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tinh.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double click để sửa
        self.tinh_tree.bind('<Double-1>', self.on_tinh_double_click)
    
    # === SEAL CODE METHODS ===
    def load_seal_codes(self):
        """Load mã niêm phong từ file"""
        try:
            with open("niem_phong.txt", "r", encoding="utf-8") as f:
                self.seal_codes = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.seal_codes = []
        
        self.refresh_seal_list()
    
    def refresh_seal_list(self):
        """Refresh danh sách mã niêm phong"""
        self.seal_listbox.delete(0, tk.END)
        for code in sorted(self.seal_codes):
            self.seal_listbox.insert(tk.END, code)
    
    def add_seal_code(self):
        """Thêm mã niêm phong"""
        code = self.seal_entry.get().strip().upper()
        if not code:
            messagebox.showerror("Lỗi", "Vui lòng nhập mã niêm phong!")
            return
        
        if len(code) != 7 or not code[0].isalpha() or not code[1:].isdigit():
            messagebox.showerror("Lỗi", "Mã niêm phong phải có 1 chữ cái + 6 số!")
            return
        
        if code in self.seal_codes:
            messagebox.showerror("Lỗi", "Mã niêm phong đã tồn tại!")
            return
        
        self.seal_codes.append(code)
        self.save_seal_codes()
        self.refresh_seal_list()
        self.seal_entry.delete(0, tk.END)
        messagebox.showinfo("Thành công", f"Đã thêm mã niêm phong: {code}")
    
    def edit_seal_code(self):
        """Sửa mã niêm phong"""
        selection = self.seal_listbox.curselection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn mã niêm phong để sửa!")
            return
        
        old_code = self.seal_listbox.get(selection[0])
        new_code = self.seal_entry.get().strip().upper()
        
        if not new_code:
            messagebox.showerror("Lỗi", "Vui lòng nhập mã niêm phong mới!")
            return
        
        if len(new_code) != 7 or not new_code[0].isalpha() or not new_code[1:].isdigit():
            messagebox.showerror("Lỗi", "Mã niêm phong phải có 1 chữ cái + 6 số!")
            return
        
        if new_code != old_code and new_code in self.seal_codes:
            messagebox.showerror("Lỗi", "Mã niêm phong đã tồn tại!")
            return
        
        self.seal_codes[self.seal_codes.index(old_code)] = new_code
        self.save_seal_codes()
        self.refresh_seal_list()
        self.seal_entry.delete(0, tk.END)
        messagebox.showinfo("Thành công", f"Đã sửa mã niêm phong: {old_code} → {new_code}")
    
    def delete_seal_code(self):
        """Xóa mã niêm phong"""
        selection = self.seal_listbox.curselection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn mã niêm phong để xóa!")
            return
        
        code = self.seal_listbox.get(selection[0])
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa mã niêm phong: {code}?"):
            self.seal_codes.remove(code)
            self.save_seal_codes()
            self.refresh_seal_list()
            messagebox.showinfo("Thành công", f"Đã xóa mã niêm phong: {code}")
    
    def on_seal_double_click(self, event):
        """Double click để sửa mã niêm phong"""
        selection = self.seal_listbox.curselection()
        if selection:
            code = self.seal_listbox.get(selection[0])
            self.seal_entry.delete(0, tk.END)
            self.seal_entry.insert(0, code)
    
    def import_seal_codes(self):
        """Import mã niêm phong từ file"""
        file_path = filedialog.askopenfilename(
            title="Chọn file import mã niêm phong",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    new_codes = [line.strip().upper() for line in f if line.strip()]
                
                # Validate codes
                valid_codes = []
                for code in new_codes:
                    if len(code) == 7 and code[0].isalpha() and code[1:].isdigit():
                        valid_codes.append(code)
                
                if valid_codes:
                    # Add new codes (skip duplicates)
                    added_count = 0
                    for code in valid_codes:
                        if code not in self.seal_codes:
                            self.seal_codes.append(code)
                            added_count += 1
                    
                    self.save_seal_codes()
                    self.refresh_seal_list()
                    messagebox.showinfo("Thành công", f"Đã import {added_count} mã niêm phong mới!")
                else:
                    messagebox.showerror("Lỗi", "Không có mã niêm phong hợp lệ trong file!")
                    
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")
    
    def save_seal_codes(self):
        """Lưu mã niêm phong vào file"""
        with open("niem_phong.txt", "w", encoding="utf-8") as f:
            for code in sorted(self.seal_codes):
                f.write(code + "\n")
    
    # === API METHODS ===
    def load_api_config(self):
        """Load cấu hình API"""
        try:
            with open("api_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.api_key_entry.insert(0, config.get("api_key", ""))
                self.model_var.set(config.get("model", "gemini-2.5-flash-lite"))
        except FileNotFoundError:
            # Tạo file api_config.json mặc định
            default_config = {
                "api_key": "",
                "model": "gemini-2.5-flash-lite",
                "created_at": datetime.now().isoformat()
            }
            try:
                with open("api_config.json", "w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                print("📝 Đã tạo file api_config.json mặc định")
            except Exception as e:
                print(f"❌ Không thể tạo file api_config.json: {e}")
    
    def save_api_config(self):
        """Lưu cấu hình API"""
        api_key = self.api_key_entry.get().strip()
        model = self.model_var.get()
        
        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API Key!")
            return
        
        config = {
            "api_key": api_key,
            "model": model,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            with open("api_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Update create_folder.py
            self.update_create_folder_api(api_key, model)
            
            messagebox.showinfo("Thành công", "Đã lưu cấu hình API!")
            self.api_status_label.config(text="✅ API đã được cấu hình", fg="green")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình: {e}")
    
    def update_create_folder_api(self, api_key, model):
        """Cập nhật API trong create_folder.py"""
        try:
            with open("create_folder.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace API key
            content = re.sub(r'GOOGLE_API_KEY = "[^"]+"', f'GOOGLE_API_KEY = "{api_key}"', content)
            content = re.sub(r"model = genai\.GenerativeModel\('[^']+'\)", f"model = genai.GenerativeModel('{model}')", content)
            
            with open("create_folder.py", "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"Không thể cập nhật create_folder.py: {e}")
    
    def toggle_api_key_visibility(self):
        """Toggle hiển thị API key"""
        if self.api_key_entry.cget('show') == '*':
            self.api_key_entry.config(show='')
        else:
            self.api_key_entry.config(show='*')
    
    def test_api(self):
        """Test API Gemini"""
        api_key = self.api_key_entry.get().strip()
        model = self.model_var.get()
        
        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API Key!")
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            test_model = genai.GenerativeModel(model)
            
            # Test với prompt đơn giản
            response = test_model.generate_content("Hello, test API")
            
            if response.text:
                messagebox.showinfo("Thành công", "API hoạt động bình thường!")
                self.api_status_label.config(text="✅ API hoạt động tốt", fg="green")
            else:
                messagebox.showerror("Lỗi", "API không trả về kết quả!")
                self.api_status_label.config(text="❌ API lỗi", fg="red")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"API không hoạt động: {e}")
            self.api_status_label.config(text="❌ API lỗi", fg="red")
    
    # === DAILY METHODS ===
    def load_daily_config(self):
        """Load cấu hình đại lý"""
        try:
            with open("dai_ly_config.txt", "r", encoding="utf-8") as f:
                self.daily_data = {}
                for line in f:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        self.daily_data[key.strip()] = value.strip()
        except FileNotFoundError:
            self.daily_data = {}
        
        self.refresh_daily_tree()
    
    def refresh_daily_tree(self):
        """Refresh tree đại lý"""
        for item in self.daily_tree.get_children():
            self.daily_tree.delete(item)
        
        for name, code in self.daily_data.items():
            self.daily_tree.insert("", tk.END, values=(name, code))
    
    def add_daily(self):
        """Thêm đại lý"""
        name = self.daily_name_entry.get().strip()
        code = self.daily_code_entry.get().strip()
        
        if not name or not code:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ tên và mã đại lý!")
            return
        
        if name in self.daily_data:
            messagebox.showerror("Lỗi", "Tên đại lý đã tồn tại!")
            return
        
        self.daily_data[name] = code
        self.save_daily_config()
        self.refresh_daily_tree()
        self.clear_daily_entries()
        messagebox.showinfo("Thành công", f"Đã thêm đại lý: {name}")
    
    def edit_daily(self):
        """Sửa đại lý"""
        selection = self.daily_tree.selection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn đại lý để sửa!")
            return
        
        item = self.daily_tree.item(selection[0])
        old_name = item['values'][0]
        new_name = self.daily_name_entry.get().strip()
        new_code = self.daily_code_entry.get().strip()
        
        if not new_name or not new_code:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ tên và mã đại lý!")
            return
        
        if new_name != old_name and new_name in self.daily_data:
            messagebox.showerror("Lỗi", "Tên đại lý đã tồn tại!")
            return
        
        del self.daily_data[old_name]
        self.daily_data[new_name] = new_code
        self.save_daily_config()
        self.refresh_daily_tree()
        self.clear_daily_entries()
        messagebox.showinfo("Thành công", f"Đã sửa đại lý: {old_name} → {new_name}")
    
    def delete_daily(self):
        """Xóa đại lý"""
        selection = self.daily_tree.selection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn đại lý để xóa!")
            return
        
        item = self.daily_tree.item(selection[0])
        name = item['values'][0]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa đại lý: {name}?"):
            del self.daily_data[name]
            self.save_daily_config()
            self.refresh_daily_tree()
            messagebox.showinfo("Thành công", f"Đã xóa đại lý: {name}")
    
    def on_daily_double_click(self, event):
        """Double click để sửa đại lý"""
        selection = self.daily_tree.selection()
        if selection:
            item = self.daily_tree.item(selection[0])
            name, code = item['values']
            self.daily_name_entry.delete(0, tk.END)
            self.daily_name_entry.insert(0, name)
            self.daily_code_entry.delete(0, tk.END)
            self.daily_code_entry.insert(0, code)
    
    def clear_daily_entries(self):
        """Clear các entry đại lý"""
        self.daily_name_entry.delete(0, tk.END)
        self.daily_code_entry.delete(0, tk.END)
    
    def save_daily_config(self):
        """Lưu cấu hình đại lý"""
        with open("dai_ly_config.txt", "w", encoding="utf-8") as f:
            for name, code in self.daily_data.items():
                f.write(f"{name}:{code}\n")
    
    # === TINH METHODS ===
    def load_tinh_config(self):
        """Load cấu hình tỉnh thành"""
        try:
            with open("ma_tinh_config.txt", "r", encoding="utf-8") as f:
                self.tinh_data = {}
                for line in f:
                    if ':' in line:
                        name, code = line.strip().split(':', 1)
                        self.tinh_data[name.strip()] = code.strip()
        except FileNotFoundError:
            self.tinh_data = {}
        
        self.refresh_tinh_tree()
    
    def refresh_tinh_tree(self):
        """Refresh tree tỉnh thành"""
        for item in self.tinh_tree.get_children():
            self.tinh_tree.delete(item)
        
        for name, code in self.tinh_data.items():
            self.tinh_tree.insert("", tk.END, values=(name, code))
    
    def add_tinh(self):
        """Thêm tỉnh thành"""
        name = self.tinh_name_entry.get().strip()
        code = self.tinh_code_entry.get().strip()
        
        if not name or not code:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ tên và mã tỉnh!")
            return
        
        if name in self.tinh_data:
            messagebox.showerror("Lỗi", "Tên tỉnh đã tồn tại!")
            return
        
        self.tinh_data[name] = code
        self.save_tinh_config()
        self.refresh_tinh_tree()
        self.clear_tinh_entries()
        messagebox.showinfo("Thành công", f"Đã thêm tỉnh: {name}")
    
    def edit_tinh(self):
        """Sửa tỉnh thành"""
        selection = self.tinh_tree.selection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn tỉnh để sửa!")
            return
        
        item = self.tinh_tree.item(selection[0])
        old_name = item['values'][0]
        new_name = self.tinh_name_entry.get().strip()
        new_code = self.tinh_code_entry.get().strip()
        
        if not new_name or not new_code:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ tên và mã tỉnh!")
            return
        
        if new_name != old_name and new_name in self.tinh_data:
            messagebox.showerror("Lỗi", "Tên tỉnh đã tồn tại!")
            return
        
        del self.tinh_data[old_name]
        self.tinh_data[new_name] = new_code
        self.save_tinh_config()
        self.refresh_tinh_tree()
        self.clear_tinh_entries()
        messagebox.showinfo("Thành công", f"Đã sửa tỉnh: {old_name} → {new_name}")
    
    def delete_tinh(self):
        """Xóa tỉnh thành"""
        selection = self.tinh_tree.selection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn tỉnh để xóa!")
            return
        
        item = self.tinh_tree.item(selection[0])
        name = item['values'][0]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tỉnh: {name}?"):
            del self.tinh_data[name]
            self.save_tinh_config()
            self.refresh_tinh_tree()
            messagebox.showinfo("Thành công", f"Đã xóa tỉnh: {name}")
    
    def on_tinh_double_click(self, event):
        """Double click để sửa tỉnh thành"""
        selection = self.tinh_tree.selection()
        if selection:
            item = self.tinh_tree.item(selection[0])
            name, code = item['values']
            self.tinh_name_entry.delete(0, tk.END)
            self.tinh_name_entry.insert(0, name)
            self.tinh_code_entry.delete(0, tk.END)
            self.tinh_code_entry.insert(0, code)
    
    def clear_tinh_entries(self):
        """Clear các entry tỉnh thành"""
        self.tinh_name_entry.delete(0, tk.END)
        self.tinh_code_entry.delete(0, tk.END)
    
    def save_tinh_config(self):
        """Lưu cấu hình tỉnh thành"""
        with open("ma_tinh_config.txt", "w", encoding="utf-8") as f:
            for name, code in self.tinh_data.items():
                f.write(f"{name}:{code}\n")
    
    def run(self):
        """Chạy ứng dụng"""
        self.window.mainloop()

if __name__ == "__main__":
    app = ConfigManager()
    app.run()
