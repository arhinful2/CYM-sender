import csv
import io
from datetime import date, timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from members.models import Member, Attendance

class ReportGenerator:
    @staticmethod
    def generate_member_report(format='pdf', filters=None):
        """
        Generate member report in various formats
        """
        members = Member.objects.all()
        
        if filters:
            if filters.get('status'):
                members = members.filter(status=filters['status'])
            if filters.get('date_joined_start'):
                members = members.filter(date_joined__gte=filters['date_joined_start'])
            if filters.get('date_joined_end'):
                members = members.filter(date_joined__lte=filters['date_joined_end'])
        
        if format == 'pdf':
            return ReportGenerator._generate_pdf_report(members)
        elif format == 'excel':
            return ReportGenerator._generate_excel_report(members)
        elif format == 'csv':
            return ReportGenerator._generate_csv_report(members)
        else:
            return ReportGenerator._generate_html_report(members)
    
    @staticmethod
    def _generate_pdf_report(members):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="member_report.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Church Member Report")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, f"Generated on: {date.today()}")
        p.drawString(50, height - 85, f"Total Members: {members.count()}")
        
        # Table headers
        y = height - 120
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Name")
        p.drawString(200, y, "Phone")
        p.drawString(300, y, "Email")
        p.drawString(450, y, "Status")
        
        # Member data
        p.setFont("Helvetica", 9)
        y -= 20
        
        for member in members:
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 9)
            
            p.drawString(50, y, member.full_name()[:30])
            p.drawString(200, y, str(member.phone_number)[:15])
            p.drawString(300, y, member.email[:20])
            p.drawString(450, y, member.status)
            y -= 15
        
        p.save()
        return response
    
    @staticmethod
    def _generate_excel_report(members):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="member_report.xlsx"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Members"
        
        # Headers
        headers = ['ID', 'First Name', 'Last Name', 'Phone', 'Email', 'Status', 
                  'Date Joined', 'Birth Date', 'Age', 'Gender', 'Department']
        ws.append(headers)
        
        # Data
        for member in members:
            ws.append([
                member.id,
                member.first_name,
                member.last_name,
                str(member.phone_number),
                member.email,
                member.status,
                member.date_joined,
                member.date_of_birth,
                member.age(),
                member.get_gender_display(),
                member.department or ''
            ])
        
        # Save to response
        output = io.BytesIO()
        wb.save(output)
        response.write(output.getvalue())
        
        return response
    
    @staticmethod
    def _generate_csv_report(members):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="member_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Phone', 'Email', 'Status', 'Date Joined', 'Age'])
        
        for member in members:
            writer.writerow([
                member.id,
                member.full_name(),
                member.phone_number,
                member.email,
                member.status,
                member.date_joined,
                member.age()
            ])
        
        return response
    
    @staticmethod
    def _generate_html_report(members):
        context = {
            'members': members,
            'report_date': date.today(),
            'total_count': members.count()
        }
        
        html = render_to_string('portal/reports/member_report.html', context)
        response = HttpResponse(content_type='text/html')
        response.write(html)
        return response
    
    @staticmethod
    def generate_attendance_report(start_date, end_date):
        """
        Generate attendance report for a date range
        """
        attendance = Attendance.objects.filter(
            service_date__range=[start_date, end_date]
        ).select_related('member')
        
        # Group by service date
        report_data = {}
        for record in attendance:
            date_str = record.service_date.strftime('%Y-%m-%d')
            if date_str not in report_data:
                report_data[date_str] = {
                    'present': 0,
                    'absent': 0,
                    'total': 0,
                    'service_type': record.service_type
                }
            
            report_data[date_str]['total'] += 1
            if record.attended:
                report_data[date_str]['present'] += 1
            else:
                report_data[date_str]['absent'] += 1
        
        return report_data