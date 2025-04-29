from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

class Report:

    @staticmethod
    def generate_report(time_data, process_entries, filename="exam_report.pdf"):
        """
        Generate a PDF report with exam monitoring results.
        """
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - inch
        page = 1

        c, y, width, height, page = Report.new_page(c, y, width, height, page)
        
        # Exam details
        c.setFont("Helvetica", 12)
        c.drawString(inch, y, f"Exam Start Time: {time_data["start"]}, End Time: {time_data["end"]}")
        y -= 0.3*inch
        minutes = time_data["time"].value / 60
        c.drawString(inch, y, f"Total Time Gazing Away: {minutes:.1f} minutes ({time_data["time"].value:.1f} seconds)")
        y -= 0.5*inch
        
        # Process list
        c.setFont("Helvetica-Bold", 14)
        c.drawString(inch, y, "New Processes During Exam:")
        y -= 0.4*inch
        
        # Column headers
        c.setFont("Helvetica-Bold", 10)
        c.drawString(inch, y, "Time")
        c.drawString(3*inch, y, "PID")
        c.drawString(4*inch, y, "Process Name")
        y -= 0.3*inch

        c.setFont("Helvetica", 10)
        for timestamp, pid, name in process_entries:
            if y < inch:
                page += 1
                c, y, width, height, page = Report.new_page(c, y, width, height, page)
            
            c.drawString(inch, y, timestamp.strftime("%H:%M:%S"))
            c.drawString(3*inch, y, str(pid))
            c.drawString(4*inch, y, name)
            y -= 0.25*inch
        
        c.save()

    @staticmethod
    def new_page(c, y, width, height, page):
        if page > 1:
            c.showPage()
        y = height - inch
        
        # Header on each page
        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, height - 0.5*inch, "Exam Monitoring Report")
        c.setFont("Helvetica", 8)
        c.drawString(width - 1.5*inch, height - 0.5*inch, f"Page {page}")
        y -= inch
        return c, y, width, height, page