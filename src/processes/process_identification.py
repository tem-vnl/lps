import psutil
import platform
import subprocess
import os
import pwd


#import pyautogui

def get_username():
    return pwd.getpwuid(os.getuid())[0]

def main():
    processes = psutil.process_iter()
    for process in processes:
        if(process.username() == get_username()):
            #print(f"Process ID: {process.pid}, Name: {process.name()}, User: {process.username()}, MemInfo: {process.memory_info()}")
            if len(process.children()) != 0:
                print(process.as_dict())
                #print(process.children())

main()