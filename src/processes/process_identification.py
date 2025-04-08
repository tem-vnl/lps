import psutil
import os
import pwd

def get_username():
    return pwd.getpwuid(os.getuid())[0]

def print_dictionary(dictionary):
    """
    Prints the dictionary in a readable manner.
    Could be useful for writting to file when generating report.
    """
    for name, proc_list in dictionary.items():
        print(f"\nProcess Name: {name}")
        for proc in proc_list:
            print(f"  PID: {proc['pid']}, User: {proc['username']}")

def main():
    processes_dict = {}
    processes = psutil.process_iter()
    
    for process in processes:
        try:
            if process.username() == get_username():
                proc_name = process.name()
                proc_info = {
                    "pid": process.pid,
                    "username": process.username()
                }
                if proc_name not in processes_dict:
                    processes_dict[proc_name] = []
                processes_dict[proc_name].append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Ignore processes that can't be accessed
    
    #print_dictionary(processes_dict)

if __name__ == "__main__":
    main()