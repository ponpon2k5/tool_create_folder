from tkinter import *
import create_folder


def call_GUI1():
    win1 = Toplevel(root)
    button_create_folder = Button(win1, text="Create Folder", command=lambda: create_folder.create_folder(win1))
    button_create_folder.pack()
    return

# the first gui owns the root window
if __name__ == "__main__":
    root = Tk()
    root.title('Caller GUI')
    root.minsize(720, 600)
    button_1 = Button(root, text='Call GUI1', width='20', height='20', command=call_GUI1)
    button_1.pack()
    root.mainloop()