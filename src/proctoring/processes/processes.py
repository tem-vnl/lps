import os
import pwd
import time
import psutil
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

class ProcessMonitor:
    def __init__(self, queue, temp_file="temp_processes.txt"):
        self.queue = queue
        self.username = pwd.getpwuid(os.getuid())[0]
        self.temp_file = temp_file
        self.entries = []
        self.start_time = datetime.now()
        # Write header to temp file
        with open(self.temp_file, 'w') as f:
            f.write(f"Process Monitoring Started at: {self.start_time}\n")
            f.write("-" * 80 + "\n")

    def add_entry(self, timestamp, pid, name):
        entry = f"{timestamp} - PID: {pid} - {name}\n"
        self.entries.append((timestamp, pid, name))
        # Immediately write to temp file
        with open(self.temp_file, 'a') as f:
            f.write(entry)

    def run(self):
        print("Process monitoring started\n")
        previous_processes = self._get_user_processes()
        
        try:
            while True:
                time.sleep(5)
                current_processes = self._get_user_processes()
                started, stopped = self._compare_processes(previous_processes, current_processes)
                
                if started or stopped:
                    self.queue.put({"started": started, "stopped": stopped})
                    # Add new processes to the report
                    for name, procs in started.items():
                        for proc in procs:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            self.add_entry(timestamp, proc['pid'], name)
                
                previous_processes = current_processes
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            self.generate_pdf()
            print(f"PDF report has been generated")
            print(f"Temporary log file preserved as '{self.temp_file}'")

    def _get_user_processes(self):
        processes_dict = {}
        for process in psutil.process_iter(['pid', 'name', 'username']):
            try:
                if process.info['username'] == self.username:
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

    def _compare_processes(self, old, new):
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

    def generate_pdf(self, filename="process_report.pdf"):
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - inch
        items_per_page = 0
        page = 1
        
        def start_new_page():
            nonlocal y, items_per_page
            if page > 1:
                c.showPage()
            y = height - inch
            items_per_page = 0
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, height - 0.5*inch, "New Processes During Exam")
            c.setFont("Helvetica", 10)
            c.drawString(inch, height - 0.8*inch, f"Started: {self.start_time}")
            y -= inch
            
            # Column headers
            c.setFont("Helvetica-Bold", 12)
            c.drawString(inch, y, "Time Started")
            c.drawString(3*inch, y, "Process ID")
            c.drawString(4.5*inch, y, "Process Name")
            y -= 0.3*inch
            
            # Page number
            c.setFont("Helvetica", 8)
            c.drawString(width - inch, 0.5*inch, f"Page {page}")

        start_new_page()
        
        for timestamp, pid, name in self.entries:
            if y < inch:
                page += 1
                start_new_page()
            
            c.setFont("Helvetica", 10)
            c.drawString(inch, y, timestamp)
            c.drawString(3*inch, y, str(pid))
            c.drawString(4.5*inch, y, name)
            y -= 0.25*inch
        
        c.save()