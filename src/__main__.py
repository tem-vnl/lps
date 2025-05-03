"""
    Main entry point for the LPS (Lightweight Proctoring System) application
"""

import argparse

from proctoring import Proctoring

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

    # Display welcome message and available commands
    print("Welcome to the LPS application!\nstart: To start an exam session.\nstop: To end a running exam session.\nexit: To exit the program.")

    # Main command loop for user interaction
    while True:
        command = input("> ")
        if command == "start":
            # Handle the start command - begins an exam session if none is running
            if not proctoring.running:
                valid, message = proctoring.valid_startup()
                if valid:
                    proctoring.start_exam()
                else:
                    print(f"Please close the following programs before starting an exam: {message}")
            else:
                print("An exam is allready running.")
        elif command == "stop":
            # Handle the stop command - ends an active exam session
            if proctoring.running:
                proctoring.end_exam()
            else:
                print("There is no exam running at the moment.")
        elif command == "exit":
            # Handle the exit command - terminates the application if no exam is active
            if proctoring.running:
                print("Can't exit with an active exam session.")
            else:
                break

if __name__ == "__main__":
    # Execute main function when script is run directly
    main()