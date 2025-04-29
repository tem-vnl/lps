import argparse
import tkinter as tk
from proctoring import Proctoring
from examGUI import ExamGUI

def main():
    parser = argparse.ArgumentParser(prog='LPS', add_help=False)
    parser.add_argument('-h', '--help', help="show this help message and exit", action="store_true")
    parser.add_argument('-d', '--demo', help="run the program in demo mode", action="store_true")
    args = vars(parser.parse_args())

    if args["help"]:
        parser.print_help()
        return

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
                print(f"Please close the following programs before starting an exam: {message}")
        else:
            print("An exam is already running.")
    
    def stop_exam():
        if proctoring.running:
            proctoring.end_exam()
        else:
            print("There is no exam running at the moment.")
    
    def exit_app():
        if not proctoring.running:
            root.destroy()
        else:
            print("Can't exit with an active exam session.")
    
    app.start_button.configure(command=start_exam)
    app.stop_button.configure(command=stop_exam)
    app.exit_button.configure(command=exit_app)
    
    root.mainloop()

if __name__ == "__main__":
    main()