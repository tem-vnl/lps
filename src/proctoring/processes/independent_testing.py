import psutil
import os
from datetime import datetime
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

class ProcessMonitor:
    def __init__(self, temp_file="temp_processes.txt"):
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

def generate_process_report(filename="process_report.pdf"):
    monitor = ProcessMonitor()
    current_user = os.getlogin()
    
    # Get initial set of processes
    initial_processes = set()
    for process in psutil.process_iter(['pid', 'name', 'username']):
        try:
            if process.info['username'] == current_user:
                initial_processes.add((process.info['pid'], process.info['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print("Monitoring for new processes... Press Enter to stop")
    print(f"Temporary log file: {monitor.temp_file}")
    
    previous_processes = set()
    
    try:
        while True:
            current_processes = set()
            
            for process in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    if process.info['username'] == current_user:
                        current_processes.add((process.info['pid'], process.info['name']))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            new_processes = current_processes - initial_processes
            for pid, name in new_processes - previous_processes:
                timestamp = datetime.now().strftime('%H:%M:%S')
                monitor.add_entry(timestamp, pid, name)
            
            previous_processes = new_processes
            
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit() and msvcrt.getch() == b'\r':
                    break
            else:
                import sys, select
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    sys.stdin.readline()
                    break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    finally:
        print("\nGenerating PDF report...")
        monitor.generate_pdf(filename)
        print(f"PDF report has been generated as '{filename}'")
        print(f"Temporary log file preserved as '{monitor.temp_file}'")

if __name__ == "__main__":
    generate_process_report()