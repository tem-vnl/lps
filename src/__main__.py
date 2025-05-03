"""
    Main entry point for the LPS (Lightweight Proctoring System) application
"""

import argparse
import tkinter as tk
from tkinter import messagebox
from proctoring import Proctoring
from examGUI import ExamGUI

def main():
    """
    Main function that initializes the proctoring system and handles user commands.
    
    Parses command-line arguments, creates the proctoring object, and runs the
    command loop for controlling exam sessions.
    """
    # Setup command-line argument parser
    parser = argparse.ArgumentParser(prog='LPS', add_help=False)
    parser.add_argument('-h', '--help', help="show this help message and exit", action="store_true")
    parser.add_argument('-d', '--demo', help="run the program in demo mode", action="store_true")
    args = vars(parser.parse_args())

    # Display help if requested and exit
    if args["help"]:
        parser.print_help()
        return

    # Initialize the proctoring system with demo mode if specified
    proctoring = Proctoring(demo=args["demo"])
    
    # Create GUI
    root = tk.Tk()
    app = ExamGUI(root)
    
    # Connect buttons to proctoring functions
    def start_exam():
        if not proctoring.running:
            valid, message = proctoring.valid_startup()
            if valid:
                proctoring.start_exam()
            else:
                messagebox.showerror("Invalid Startup", 
                    f"Please close the following programs before starting:\n{message}")
        else:
            messagebox.showinfo("Exam Status", "An exam is already running.")
    
    def stop_exam():
        if proctoring.running:
            proctoring.end_exam()
        else:
            messagebox.showinfo("Exam Status", "No exam is currently running.")
    
    def exit_app():
        if not proctoring.running:
            root.destroy()
        else:
            messagebox.showerror("Cannot Exit", 
                "Please end the active exam session before exiting.")
    
    app.start_button.configure(command=start_exam)
    app.stop_button.configure(command=stop_exam)
    app.exit_button.configure(command=exit_app)
    
    root.mainloop()

if __name__ == "__main__":
    # Execute main function when script is run directly
    main()