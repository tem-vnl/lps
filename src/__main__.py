"""
    Main entry point for the Lightweight Proctoring System (LPS).

    This module initializes the GUI and connects it to the proctoring system.
    It handles the startup configuration including command line arguments and
    creates the main application window.
"""

import argparse
import tkinter as tk
from tkinter import messagebox
from proctoring import Proctoring
from proctoring.examGUI import ExamGUI

def main():
    """
    Initialize and run the LPS application.
    
    Sets up the GUI, processes command line arguments, and establishes the connection
    between the GUI controls and the proctoring system functionality.
    
    Command line arguments:
        -h, --help: Display help message
        -d, --demo: Run in demo mode with camera feed for eye tracking
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(prog='LPS', add_help=False)
    parser.add_argument('-h', '--help', help="show this help message and exit", action="store_true")
    parser.add_argument('-d', '--demo', help="run the program in demo mode", action="store_true")
    args = vars(parser.parse_args())

    # Display help if requested and exit
    if args["help"]:
        parser.print_help()
        return

    # Initialize proctoring system
    proctoring = Proctoring(demo=args["demo"])
    
    # Set up GUI window and components
    root = tk.Tk()
    app = ExamGUI(root)
    
    # Callback functions for GUI buttons
    def start_exam():
        """Handle exam start button click."""
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
        """Handle exam stop button click."""
        if proctoring.running:
            proctoring.end_exam()
        else:
            messagebox.showinfo("Exam Status", "No exam is currently running.")
    
    def exit_app():
        """Handle exit button click."""
        if not proctoring.running:
            root.destroy()
        else:
            messagebox.showerror("Cannot Exit", 
                "Please end the active exam session before exiting.")
    
    # Connect callbacks to GUI buttons
    app.start_button.configure(command=start_exam)
    app.stop_button.configure(command=stop_exam)
    app.exit_button.configure(command=exit_app)
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    # Execute main function when script is run directly
    main()