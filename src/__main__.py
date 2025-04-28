import argparse

from proctoring import Proctoring

def main():
    parser = argparse.ArgumentParser(prog='LPS', add_help=False)
    parser.add_argument('-h', '--help', help="show this help message and exit", action="store_true")
    parser.add_argument('-d', '--demo', help="run the program in demo mode", action="store_true")
    args = vars(parser.parse_args())

    if args["help"]:
        parser.print_help()
        return

    proctoring = Proctoring(demo=args["demo"])

    print("Welcome to the LPS application!\nstart: To start an exam session.\nstop: To end a running exam session.\nexit: To exit the program.")

    while True:
        command = input("> ")
        if command == "start":
            if not proctoring.running:
                valid, message = proctoring.valid_startup()
                if valid:
                    proctoring.start_exam()
                else:
                    print(f"Please close the following programs before starting an exam: {message}")
            else:
                print("An exam is allready running.")
        elif command == "stop":
            if proctoring.running:
                proctoring.end_exam()
            else:
                print("There is no exam running at the moment.")
        elif command == "exit":
            if proctoring.running:
                print("Can't exit with an active exam session.")
            else:
                break

if __name__ == "__main__":
    main()