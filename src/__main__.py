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

    Proctoring(demo=args["demo"])


if __name__ == "__main__":
    main()