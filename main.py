import tkinter as tk
from create_folder import create_folder_ui
# from manager_folder import manager_folder_ui
from change_name_folder import change_name_folder_ui

def main():
    window = tk.Tk()
    window.title("test")
    window.iconbitmap("iconZ.ico")

    # Tạo nút "Tạo Folder"
    button_create_folder = tk.Button(window, text="Tạo Folder", command=create_folder_ui)
    button_create_folder.grid(padx=10, pady=10)

    # button_manager_folder = tk.Button(window, text="Manager Folder", command=manager_folder_ui)
    # button_manager_folder.grid(padx=10, pady=10)

    button_change_folder_name = tk.Button(window, text="Change Name Folder", command=change_name_folder_ui)
    button_change_folder_name.grid(padx=10, pady=10)

    window.mainloop()

if __name__ == "__main__":
    main()