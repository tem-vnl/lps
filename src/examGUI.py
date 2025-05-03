"""
GUI module for the Lightweight Proctoring System (LPS).

Provides a simple interface with start, stop, and exit controls
for managing exam sessions.
"""

import tkinter as tk
from tkinter import ttk

class ExamGUI:
    """
    Main GUI class for the exam application.
    
    Provides a window with three control buttons:
    - Start: Begins a new exam session
    - Stop: Ends the current exam session
    - Exit: Closes the application
    """
    
    def __init__(self, root):
        """
        Initialize the GUI window and its components.
        
        Args:
            root: The root window (Tk instance) for the application
        """
        self.root = root
        self.root.title("Exam Application")
        self.root.geometry("400x200")

        # Create and configure the button container
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(expand=True)
        
        # Initialize control buttons
        self._setup_buttons()
    
    def _setup_buttons(self):
        """Create and layout the control buttons."""
        self.start_button = ttk.Button(self.button_frame, text="Start")
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Stop")
        self.stop_button.pack(side='left', padx=5)
        
        self.exit_button = ttk.Button(self.button_frame, text="Exit", 
                                    command=self.root.destroy)
        self.exit_button.pack(side='left', padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExamGUI(root)
    root.mainloop()

