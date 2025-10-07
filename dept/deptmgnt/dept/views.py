from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Q
from .models import *
from .forms import *
from reportlab.pdfgen import canvas
import csv
from datetime import datetime, date

def home(request):
    return render(request, 'home.html')

def student_register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        student_form = StudentRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            student_profile = student_form.save(commit=False)
            student_profile.user = user
            student_profile.save()
            
            messages.success(request, 'Registration successful! Please wait for admin approval.')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        student_form = StudentRegistrationForm()
    
    return render(request, 'auth/student_register.html', {
        'user_form': user_form,
        'student_form': student_form
    })

def staff_register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        staff_form = StaffRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and staff_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.is_staff = True
            user.save()
            
            staff_profile = staff_form.save(commit=False)
            staff_profile.user = user
            staff_profile.save()
            
            messages.success(request, 'Staff registration successful!')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        staff_form = StaffRegistrationForm()
    
    return render(request, 'auth/staff_register.html', {
        'user_form': user_form,
        'staff_form': staff_form
    })

@login_required
def dashboard(request):
    context = {}
    
    if hasattr(request.user, 'studentprofile'):
        student = request.user.studentprofile
        context['role'] = 'student'
        context['student'] = student
        
        # Get recent announcements
        context['announcements'] = Announcement.objects.filter(
            classroom=student.classroom
        ).order_by('-created_at')[:5]
        
        # Get attendance summary
        total_days = Attendance.objects.filter(
            student=student, 
            classroom=student.classroom
        ).count()
        present_days = Attendance.objects.filter(
            student=student, 
            classroom=student.classroom,
            status='P'
        ).count()
        context['attendance_percentage'] = (present_days / total_days * 100) if total_days > 0 else 0
        
    elif hasattr(request.user, 'staffprofile'):
        staff = request.user.staffprofile
        context['role'] = 'staff'
        context['staff'] = staff
        
        if staff.is_hod:
            context['role'] = 'hod'
            # HOD specific data
            department = staff.department
            context['total_students'] = StudentProfile.objects.filter(
                department=department, 
                is_approved=True
            ).count()
            context['total_staff'] = StaffProfile.objects.filter(
                department=department,
                is_approved=True
            ).count()
            context['total_classes'] = ClassRoom.objects.filter(
                department=department
            ).count()
        
        # Get staff's classes
        context['classes'] = staff.classes.all()
        
    else:
        context['role'] = 'admin'
    
    return render(request, 'dashboard.html', context)

# Student Views
@login_required
@user_passes_test(lambda u: hasattr(u, 'studentprofile'))
def student_attendance(request):
    student = request.user.studentprofile
    
    # Calculate attendance percentage
    total_days = Attendance.objects.filter(
        student=student, 
        classroom=student.classroom
    ).count()
    present_days = Attendance.objects.filter(
        student=student, 
        classroom=student.classroom,
        status='P'
    ).count()
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    attendances = Attendance.objects.filter(
        student=student, 
        classroom=student.classroom
    ).order_by('-date')
    
    return render(request, 'student/attendance.html', {
        'attendances': attendances,
        'student': student,
        'attendance_percentage': attendance_percentage
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'studentprofile'))
def student_marks(request):
    student = request.user.studentprofile
    marks = Mark.objects.filter(
        student=student, 
        classroom=student.classroom
    ).order_by('-entered_at')
    
    return render(request, 'student/marks.html', {
        'marks': marks,
        'student': student
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'studentprofile'))
def student_announcements(request):
    student = request.user.studentprofile
    announcements = Announcement.objects.filter(
        classroom=student.classroom
    ).order_by('-created_at')
    
    # Mark as read when viewed
    for announcement in announcements:
        AnnouncementRead.objects.get_or_create(
            announcement=announcement,
            student=student
        )
    
    return render(request, 'student/announcements.html', {
        'announcements': announcements
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'studentprofile'))
def student_lectures(request):
    student = request.user.studentprofile
    lectures = Lecture.objects.filter(
        classroom=student.classroom
    ).order_by('-uploaded_at')
    
    return render(request, 'student/lectures.html', {
        'lectures': lectures
    })

# Staff Views
@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def staff_students(request):
    staff = request.user.staffprofile
    classroom_id = request.GET.get('classroom')
    
    if classroom_id:
        classroom = get_object_or_404(ClassRoom, id=classroom_id)
        students = StudentProfile.objects.filter(
            classroom=classroom, 
            is_approved=True
        )
    else:
        classroom = None
        students = StudentProfile.objects.none()
    
    return render(request, 'staff/students.html', {
        'students': students,
        'classrooms': staff.classes.all(),
        'selected_classroom': classroom
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def staff_attendance(request):
    staff = request.user.staffprofile
    classroom_id = request.GET.get('classroom')
    selected_date = request.GET.get('date', date.today().isoformat())
    
    if classroom_id:
        classroom = get_object_or_404(ClassRoom, id=classroom_id)
        students = StudentProfile.objects.filter(
            classroom=classroom, 
            is_approved=True
        )
        
        # Get existing attendance for the date
        attendance_data = {}
        for student in students:
            attendance = Attendance.objects.filter(
                student=student,
                date=selected_date
            ).first()
            attendance_data[student.id] = attendance.status if attendance else None
    else:
        classroom = None
        students = []
        attendance_data = {}
    
    return render(request, 'staff/attendance.html', {
        'students': students,
        'classrooms': staff.classes.all(),
        'selected_classroom': classroom,
        'selected_date': selected_date,
        'attendance_data': attendance_data
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def staff_marks(request):
    staff = request.user.staffprofile
    
    if request.method == 'POST':
        form = MarksEntryForm(staff, request.POST)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.entered_by = staff
            mark.save()
            messages.success(request, 'Marks entered successfully!')
            return redirect('staff_marks')
    else:
        form = MarksEntryForm(staff)
    
    marks = Mark.objects.filter(entered_by=staff).order_by('-entered_at')
    
    return render(request, 'staff/marks.html', {
        'form': form,
        'marks': marks,
        'classrooms': staff.classes.all()
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def staff_announcements(request):
    staff = request.user.staffprofile
    
    if request.method == 'POST':
        form = AnnouncementForm(staff, request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = staff
            announcement.save()
            messages.success(request, 'Announcement created successfully!')
            return redirect('staff_announcements')
    else:
        form = AnnouncementForm(staff)
    
    announcements = Announcement.objects.filter(created_by=staff).order_by('-created_at')
    
    return render(request, 'staff/announcements.html', {
        'form': form,
        'announcements': announcements
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def staff_lectures(request):
    staff = request.user.staffprofile

    if request.method == 'POST':
        form = LectureForm(staff, request.POST, request.FILES)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.uploaded_by = staff
            lecture.save()
            messages.success(request, 'Lecture uploaded successfully!')
            return redirect('staff_lectures')
    else:
        form = LectureForm(staff)
    
    lectures = Lecture.objects.filter(uploaded_by=staff).order_by('-uploaded_at')


    
    return render(request, 'staff/lectures.html', {
        'form': form,
        'lectures': lectures
    })


# HOD Views
@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile') and u.staffprofile.is_hod)
def hod_dashboard(request):
    staff = request.user.staffprofile
    department = staff.department
    
    # Department statistics
    total_students = StudentProfile.objects.filter(department=department, is_approved=True).count()
    total_staff = StaffProfile.objects.filter(department=department).count()
    total_classes = ClassRoom.objects.filter(department=department).count()
    
    # Recent activities
    recent_announcements = Announcement.objects.filter(
        created_by__department=department
    ).order_by('-created_at')[:5]
    
    pending_approvals = StudentProfile.objects.filter(
        department=department, 
        is_approved=False
    ).count()
    
    context = {
        'department': department,
        'total_students': total_students,
        'total_staff': total_staff,
        'total_classes': total_classes,
        'recent_announcements': recent_announcements,
        'pending_approvals': pending_approvals,
    }
    
    return render(request, 'hod/dashboard.html', context)

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile') and u.staffprofile.is_hod)
def hod_reports(request):
    staff = request.user.staffprofile
    department = staff.department
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        classroom_id = request.POST.get('classroom')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if report_type == 'attendance':
            return generate_attendance_report(department, classroom_id, start_date, end_date)
        elif report_type == 'performance':
            return generate_performance_report(department, classroom_id)
    
    classrooms = ClassRoom.objects.filter(department=department)
    
    return render(request, 'hod/reports.html', {
        'classrooms': classrooms
    })

# API Views
@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def mark_attendance(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        classroom_id = request.POST.get('classroom_id')
        date_str = request.POST.get('date')
        status = request.POST.get('status')
        
        student = get_object_or_404(StudentProfile, id=student_id)
        classroom = get_object_or_404(ClassRoom, id=classroom_id)
        staff = request.user.staffprofile
        
        # Check if staff has access to this classroom
        if classroom not in staff.classes.all():
            return JsonResponse({'success': False, 'error': 'Access denied to this classroom'})
        
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=date_str,
            defaults={
                'classroom': classroom,
                'status': status,
                'marked_by': staff
            }
        )
        
        if not created:
            attendance.status = status
            attendance.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def enter_marks(request):
    if request.method == 'POST':
        staff = request.user.staffprofile
        
        # Get form data
        student_id = request.POST.get('student_id')
        classroom_id = request.POST.get('classroom_id')
        subject = request.POST.get('subject')
        exam_type = request.POST.get('exam_type')
        marks_obtained = request.POST.get('marks_obtained')
        maximum_marks = request.POST.get('maximum_marks', 100)
        
        try:
            student = StudentProfile.objects.get(id=student_id, is_approved=True)
            classroom = ClassRoom.objects.get(id=classroom_id)
            
            # Check if staff has access to this classroom
            if classroom not in staff.classes.all():
                return JsonResponse({'success': False, 'error': 'Access denied to this classroom'})
            
            # Create or update mark
            mark, created = Mark.objects.get_or_create(
                student=student,
                classroom=classroom,
                subject=subject,
                exam_type=exam_type,
                defaults={
                    'marks_obtained': marks_obtained,
                    'maximum_marks': maximum_marks,
                    'entered_by': staff
                }
            )
            
            if not created:
                mark.marks_obtained = marks_obtained
                mark.maximum_marks = maximum_marks
                mark.save()
            
            return JsonResponse({'success': True, 'message': 'Marks entered successfully!'})
            
        except StudentProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
        except ClassRoom.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Classroom not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@user_passes_test(lambda u: hasattr(u, 'staffprofile'))
def approve_student(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(StudentProfile, id=student_id)
        student.is_approved = True
        student.save()
        
        messages.success(request, f'Student {student.user.get_full_name()} approved successfully!')
        return redirect('staff_students')
    
    return JsonResponse({'success': False})

# Helper functions for reports
def generate_attendance_report(department, classroom_id, start_date, end_date):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Roll No', 'Student Name', 'Total Days', 'Present Days', 'Attendance %'])
    
    if classroom_id:
        students = StudentProfile.objects.filter(
            department=department, 
            classroom_id=classroom_id,
            is_approved=True
        )
    else:
        students = StudentProfile.objects.filter(
            department=department, 
            is_approved=True
        )
    
    for student in students:
        total_days = Attendance.objects.filter(
            student=student,
            date__range=[start_date, end_date]
        ).count()
        
        present_days = Attendance.objects.filter(
            student=student,
            date__range=[start_date, end_date],
            status='P'
        ).count()
        
        percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        writer.writerow([
            student.roll_no,
            student.user.get_full_name(),
            total_days,
            present_days,
            f"{percentage:.2f}%"
        ])
    
    return response

def generate_performance_report(department, classroom_id):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="performance_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Performance Report - {department.name}")
    p.drawString(100, 780, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if classroom_id:
        classroom = ClassRoom.objects.get(id=classroom_id)
        p.drawString(100, 760, f"Class: {classroom.name}")
        students = StudentProfile.objects.filter(
            department=department, 
            classroom=classroom,
            is_approved=True
        )
    else:
        students = StudentProfile.objects.filter(
            department=department, 
            is_approved=True
        )
    
    y_position = 740
    for student in students[:20]:  # Limit to first 20 students for demo
        avg_marks = Mark.objects.filter(student=student).aggregate(avg=Avg('marks_obtained'))['avg'] or 0
        p.drawString(100, y_position, f"{student.roll_no} - {student.user.get_full_name()}: {avg_marks:.2f}%")
        y_position -= 20
        if y_position < 100:
            p.showPage()
            y_position = 800
    
    p.save()
    return response

from django.http import JsonResponse
from .models import ClassRoom

def get_classrooms(request):
    department_id = request.GET.get('department_id')
    if department_id:
        classrooms = ClassRoom.objects.filter(department_id=department_id)
        data = {
            'classrooms': [
                {'id': classroom.id, 'name': classroom.name}
                for classroom in classrooms
            ]
        }
        return JsonResponse(data)
    return JsonResponse({'classrooms': []})

from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect

def custom_logout(request):
    auth_logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')

def debug_session(request):
    print("Current user:", request.user)
    print("Is authenticated:", request.user.is_authenticated)
    print("Session data:", dict(request.session))
    return HttpResponse("Check console for session info")

from django.http import JsonResponse

def get_classrooms(request):
    department_id = request.GET.get('department_id')
    if department_id:
        classrooms = ClassRoom.objects.filter(department_id=department_id)
        data = {
            'classrooms': [
                {'id': classroom.id, 'name': classroom.name}
                for classroom in classrooms
            ]
        }
        return JsonResponse(data)
    return JsonResponse({'classrooms': []})

def attendance_view(request):
    students = StudentProfile.objects.all()
    
    # Convert attendance data to dictionary format
    attendance_data = {}
    attendance_records = Attendance.objects.filter(date=date.today())
    for record in attendance_records:
        attendance_data[str(record.student.id)] = record.status  # 'P' or 'A'
    
    context = {
        'students': students,
        'attendance_data': attendance_data,
    }
    return render(request, 'staff/attendance.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.dateparse import parse_date
from .models import Attendance, StudentProfile, ClassRoom

def mark_attendance(request):
    if request.method == 'POST':
        try:
            classroom_id = request.POST.get('classroom_id')
            date_str = request.POST.get('date')
            students_data = request.POST.getlist('students')
            
            # Parse the date
            date = parse_date(date_str)
            if not date:
                return JsonResponse({'success': False, 'error': 'Invalid date format'})
            
            # Get classroom
            classroom = ClassRoom.objects.get(id=classroom_id)
            
            # Process each student's attendance
            for student_data in students_data:
                if ':' in student_data:
                    student_id, status = student_data.split(':', 1)
                    
                    # Get student
                    student = StudentProfile.objects.get(id=student_id)
                    
                    # Create or update attendance record
                    attendance, created = Attendance.objects.update_or_create(
                        student=student,
                        classroom=classroom,
                        date=date,
                        defaults={'status': status}
                    )
            
            return JsonResponse({'success': True, 'message': 'Attendance saved successfully'})
            
        except ClassRoom.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Classroom not found'})
        except StudentProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def attendance_view(request):
    classrooms = ClassRoom.objects.all()
    selected_classroom = None
    students = []
    attendance_records = []
    selected_date = request.GET.get('date')
    
    # Set default date to today if not provided
    if not selected_date:
        from datetime import date
        selected_date = date.today().isoformat()
    
    # Get selected classroom
    classroom_id = request.GET.get('classroom')
    if classroom_id:
        try:
            selected_classroom = ClassRoom.objects.get(id=classroom_id)
            students = StudentProfile.objects.filter(classroom=selected_classroom, is_approved=True)
            
            # Get existing attendance records for the selected date
            date_obj = parse_date(selected_date)
            if date_obj:
                attendance_records = Attendance.objects.filter(
                    classroom=selected_classroom,
                    date=date_obj
                )
        except ClassRoom.DoesNotExist:
            pass
    
    context = {
        'classrooms': classrooms,
        'selected_classroom': selected_classroom,
        'students': students,
        'attendance_records': attendance_records,
        'selected_date': selected_date,
    }
    return render(request, 'staff/attendance.html', context)

# dept/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ClassRoom, StudentProfile

@login_required
def manage_students(request):
    # Get all active classrooms with their departments
    classrooms = ClassRoom.objects.filter(is_active=True).select_related('department')
    
    selected_classroom = None
    students = []
    
    # Debug info
    print(f"DEBUG: Found {classrooms.count()} classrooms")
    for classroom in classrooms:
        print(f"DEBUG: Classroom - {classroom.name} (ID: {classroom.id})")
    
    # Get selected classroom from GET parameter
    classroom_id = request.GET.get('classroom')
    if classroom_id:
        try:
            selected_classroom = ClassRoom.objects.get(id=classroom_id, is_active=True)
            students = StudentProfile.objects.filter(classroom=selected_classroom).select_related('user')
            print(f"DEBUG: Selected classroom - {selected_classroom.name}")
        except ClassRoom.DoesNotExist:
            print(f"DEBUG: Classroom with ID {classroom_id} not found")
    
    context = {
        'classrooms': classrooms,
        'selected_classroom': selected_classroom,
        'students': students,
        'debug_classroom_count': classrooms.count(),  # For template debugging
    }
    return render(request, 'hod/manage_students.html', context)