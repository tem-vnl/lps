import tkinter as tk
from tkinter import ttk

class ExamGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Application")
        self.root.geometry("400x200")  # Smaller window size since we have fewer elements

        # Button frame
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(expand=True)
        
        self.start_button = ttk.Button(self.button_frame, text="Start")
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Stop")
        self.stop_button.pack(side='left', padx=5)
        
        self.exit_button = ttk.Button(self.button_frame, text="Exit", command=self.root.destroy)
        self.exit_button.pack(side='left', padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExamGUI(root)
    root.mainloop()

