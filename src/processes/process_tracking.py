import psutil
import os
import pwd
import time

def get_username():
    return pwd.getpwuid(os.getuid())[0]

def get_user_processes():
    processes_dict = {}
    for process in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if process.info['username'] == get_username():
                proc_name = process.info['name']
                proc_info = {
                    "pid": process.info['pid'],
                    "username": process.info['username']
                }
                if proc_name not in processes_dict:
                    processes_dict[proc_name] = []
                processes_dict[proc_name].append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes_dict

def compare_processes(old, new):
    started = {}
    stopped = {}

    # Detect started
    for name, new_list in new.items():
        old_list = old.get(name, [])
        new_pids = {proc['pid'] for proc in new_list}
        old_pids = {proc['pid'] for proc in old_list}
        added_pids = new_pids - old_pids
        if added_pids:
            started[name] = [proc for proc in new_list if proc['pid'] in added_pids]

    # Detect stopped
    for name, old_list in old.items():
        new_list = new.get(name, [])
        old_pids = {proc['pid'] for proc in old_list}
        new_pids = {proc['pid'] for proc in new_list}
        removed_pids = old_pids - new_pids
        if removed_pids:
            stopped[name] = [proc for proc in old_list if proc['pid'] in removed_pids]

    return started, stopped

def monitor(interval=5):
    print("Monitoring started\n")
    previous_processes = get_user_processes()

    while True:
        time.sleep(interval)
        current_processes = get_user_processes()
        started, stopped = compare_processes(previous_processes, current_processes)

        if started:
            print("\n New Processes:")
            for name, procs in started.items():
                for proc in procs:
                    print(f"  {name} - PID: {proc['pid']}")
        
        if stopped:
            print("\n Terminated Processes:")
            for name, procs in stopped.items():
                for proc in procs:
                    print(f"  {name} - PID: {proc['pid']}")
        
        if not started and not stopped:
            print(".", end="", flush=True)  # Just a dot to show it's still alive

        previous_processes = current_processes

monitor(interval=5)
