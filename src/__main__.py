import argparse
from multiprocessing import Process
import signal
import sys

from proctoring import Proctoring
from processes import Processes
from processes.kiosk_browser import start_browser

def signal_handler(signum, frame):
    print("\nShutting down...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(prog='LPS', add_help=False)
    parser.add_argument('-h', '--help', help="show this help message and exit", action="store_true")
    parser.add_argument('-d', '--demo', help="run the program in demo mode", action="store_true")
    args = vars(parser.parse_args())

    if args["help"]:
        parser.print_help()
        return

    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start process monitoring
        process_monitor = Processes()
        proc_process = Process(target=process_monitor.monitor)
        proc_process.start()

        # Start proctoring
        proctor = Proctoring(demo=args["demo"])

        # Start kiosk browser
        browser_process = Process(target=start_browser)
        browser_process.start()

        # Wait for processes
        proc_process.join()
        browser_process.join()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cleanup
        if 'proc_process' in locals() and proc_process.is_alive():
            proc_process.terminate()
        if 'browser_process' in locals() and browser_process.is_alive():
            browser_process.terminate()

if __name__ == "__main__":
    main()