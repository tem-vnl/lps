"""
    Report generation module for LPS
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

class Report:
    """
    A class to generate PDF reports of exam sessions.
    
    Provides functionality to create reports containing exam statistics.
    """

    @staticmethod
    def generate_report(time_data, process_entries, filename="exam_report"):
        """
        Generate a PDF report with exam monitoring results.
        
        Args:
            time_data (dict): Dictionary containing exam timing information.
            process_entries (list): List of tuples containing process information.
            filename (str): Name of the output PDF file.
        """
        EXAM_FOLDER = "./exams/"

        # Create folder for reports
        if not os.path.exists(EXAM_FOLDER):
            os.makedirs(EXAM_FOLDER)
        
        processed_filename = Report.file_name(EXAM_FOLDER, filename, time_data)

        # Initialize the PDF canvas with letter size
        c = canvas.Canvas(processed_filename, pagesize=letter)
        width, height = letter
        y = height - inch
        page = 1

        # Create the first page with header
        c, y, width, height, page = Report.new_page(c, y, width, height, page)
        
        # Exam details section
        c.setFont("Helvetica", 12)
        c.drawString(inch, y, f"Exam Start Time: {time_data['start']}, End Time: {time_data['end']}")
        y -= 0.3*inch
        minutes = time_data["time"].value / 60
        c.drawString(inch, y, f"Total Time Gazing Away: {minutes:.1f} minutes ({time_data['time'].value:.1f} seconds)")
        y -= 0.5*inch
        
        # Process list section title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(inch, y, "New Processes During Exam:")
        y -= 0.4*inch
        
        # Column headers for process table
        c.setFont("Helvetica-Bold", 10)
        c.drawString(inch, y, "Time")
        c.drawString(3*inch, y, "PID")
        c.drawString(4*inch, y, "Process Name")
        y -= 0.3*inch

        # List each process entry
        c.setFont("Helvetica", 10)
        for timestamp, pid, name in process_entries:
            # Check if a new page is needed
            if y < inch:
                page += 1
                c, y, width, height, page = Report.new_page(c, y, width, height, page)
            
            # Draw the process entry details
            c.drawString(inch, y, timestamp.strftime("%H:%M:%S"))
            c.drawString(3*inch, y, str(pid))
            c.drawString(4*inch, y, name)
            y -= 0.25*inch
        
        # Save the completed PDF document
        c.save()

    @staticmethod
    def new_page(c, y, width, height, page):
        """
        Creates a new page in the PDF document with standard header.
        
        Handles page transitions and ensures consistent formatting across
        multiple pages in the report.
        
        Args:
            c (Canvas): The ReportLab canvas object.
            y (float): Current vertical position on the page.
            width (float): Page width.
            height (float): Page height.
            page (int): Current page number.
            
        Returns:
            tuple: Updated canvas, y-position, width, height, and page number.
        """
        # If this isn't the first page, create a new page
        if page > 1:
            c.showPage()
        
        # Reset y position to top of page minus margin
        y = height - inch
        
        # Add standard header on each page
        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, height - 0.5*inch, "Exam Monitoring Report")
        c.setFont("Helvetica", 8)
        c.drawString(width - 1.5*inch, height - 0.5*inch, f"Page {page}")
        y -= inch
        
        return c, y, width, height, page
    
    @staticmethod
    def file_name(path, filename, time_data):
        timestamped = f"{filename}-{time_data['start'].strftime('%Y%m%d-%H%M%S')}"
        duplicates = 0
        extension = ".pdf"
        fullpath = f"{path}{timestamped}{extension}"
        while True:
            if not os.path.exists(fullpath):
                break
            else:
                duplicates += 1
                fullpath = f"{path}{timestamped}({duplicates}){extension}"
        return fullpath