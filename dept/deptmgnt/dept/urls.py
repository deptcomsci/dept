from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
   # Replace the logout line with:
    path('logout/', views.custom_logout, name='logout'),
    
    # Registration
    path('register/student/', views.student_register, name='student_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Student views
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/marks/', views.student_marks, name='student_marks'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),
    path('student/lectures/', views.student_lectures, name='student_lectures'),
    
    # Staff views
    path('staff/students/', views.staff_students, name='staff_students'),
    path('staff/attendance/', views.staff_attendance, name='staff_attendance'),
    path('staff/marks/', views.staff_marks, name='staff_marks'),
    path('staff/announcements/', views.staff_announcements, name='staff_announcements'),
    path('staff/lectures/', views.staff_lectures, name='staff_lectures'),
    
    # HOD views
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/reports/', views.hod_reports, name='hod_reports'),
    
    # API endpoints
    path('api/mark_attendance/', views.mark_attendance, name='mark_attendance'),
    path('api/enter_marks/', views.enter_marks, name='enter_marks'),
    path('api/approve_student/<int:student_id>/', views.approve_student, name='approve_student'),

    path('api/get-classrooms/', views.get_classrooms, name='get_classrooms'),

    path('debug-session/', views.debug_session, name='debug_session'),

    path('attendance/', views.attendance_view, name='attendance_view'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),

    path('manage-students/', views.manage_students, name='manage_students'),
]

