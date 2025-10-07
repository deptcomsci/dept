from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dept.models import *
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Generate comprehensive sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Generating sample data...')
        
        # Create Departments
        cse_dept, _ = Department.objects.get_or_create(
            name="Computer Science and Engineering",
            code="CSE",
            description="Department of Computer Science and Engineering"
        )
        
        ece_dept, _ = Department.objects.get_or_create(
            name="Electronics and Communication Engineering",
            code="ECE",
            description="Department of Electronics and Communication Engineering"
        )
        
        # Create Classrooms
        classrooms = []
        for dept in [cse_dept, ece_dept]:
            for semester in [1, 3, 5, 7]:
                classroom, _ = ClassRoom.objects.get_or_create(
                    name=f"{dept.code} Sem {semester}",
                    department=dept,
                    semester=semester,
                    academic_year="2024-25"
                )
                classrooms.append(classroom)
        
        # Create HODs
        hod_cse, _ = StaffProfile.objects.get_or_create(
            staff_id="HODCSE001",
            defaults={
                'user': User.objects.create_user(
                    username='hod_cse',
                    first_name='Rajesh',
                    last_name='Kumar',
                    email='hod.cse@university.edu',
                    password='password123'
                ),
                'department': cse_dept,
                'designation': 'Head of Department',
                'is_hod': True
            }
        )
        hod_cse.classes.set(classrooms[:4])
        
        # Create Staff Members
        staff_members = []
        staff_data = [
            {'username': 'staff1', 'staff_id': 'STF001', 'name': 'Priya Sharma', 'dept': cse_dept},
            {'username': 'staff2', 'staff_id': 'STF002', 'name': 'Amit Patel', 'dept': cse_dept},
            {'username': 'staff3', 'staff_id': 'STF003', 'name': 'Sneha Reddy', 'dept': ece_dept},
        ]
        
        for data in staff_data:
            user, _ = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['name'].split()[0],
                    'last_name': data['name'].split()[1],
                    'email': f"{data['username']}@university.edu",
                    'is_staff': True
                }
            )
            user.set_password('password123')
            user.save()
            
            staff, _ = StaffProfile.objects.get_or_create(
                staff_id=data['staff_id'],
                defaults={
                    'user': user,
                    'department': data['dept'],
                    'designation': 'Assistant Professor'
                }
            )
            # Assign random classrooms
            dept_classrooms = [c for c in classrooms if c.department == data['dept']]
            staff.classes.set(random.sample(dept_classrooms, min(2, len(dept_classrooms))))
            staff_members.append(staff)
        
        # Create Students
        students = []
        for i in range(1, 21):
            dept = random.choice([cse_dept, ece_dept])
            dept_classrooms = [c for c in classrooms if c.department == dept]
            classroom = random.choice(dept_classrooms)
            
            user, _ = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'first_name': f'Student{i}',
                    'last_name': f'LastName{i}',
                    'email': f'student{i}@university.edu'
                }
            )
            user.set_password('password123')
            user.save()
            
            student, _ = StudentProfile.objects.get_or_create(
                roll_no=f"{dept.code}00{i}",
                defaults={
                    'user': user,
                    'department': dept,
                    'classroom': classroom,
                    'phone': f'98765432{i:02d}',
                    'is_approved': True
                }
            )
            students.append(student)
        
        # Generate Attendance Records (last 30 days)
        self.stdout.write('Generating attendance records...')
        for student in students:
            for day in range(30):
                record_date = date.today() - timedelta(days=day)
                if random.random() > 0.1:  # 90% attendance rate
                    status = 'P'
                else:
                    status = 'A'
                
                Attendance.objects.get_or_create(
                    student=student,
                    date=record_date,
                    defaults={
                        'classroom': student.classroom,
                        'status': status,
                        'marked_by': random.choice(staff_members)
                    }
                )
        
        # Generate Marks
        self.stdout.write('Generating marks records...')
        subjects = ['Mathematics', 'Physics', 'Programming', 'Database', 'Networking']
        exam_types = ['Mid-term', 'Final', 'Quiz 1', 'Quiz 2']
        
        for student in students:
            for subject in subjects[:3]:  # 3 subjects per student
                for exam_type in exam_types[:2]:  # 2 exam types per subject
                    Mark.objects.get_or_create(
                        student=student,
                        classroom=student.classroom,
                        subject=subject,
                        exam_type=exam_type,
                        defaults={
                            'marks_obtained': random.uniform(60, 95),
                            'maximum_marks': 100,
                            'entered_by': random.choice(staff_members)
                        }
                    )
        
        # Generate Announcements
        self.stdout.write('Generating announcements...')
        announcements = [
            "Mid-term examination schedule released",
            "Last date for fee submission extended",
            "Guest lecture on AI and Machine Learning",
            "Holiday announcement for Diwali festival",
            "Library will remain closed for maintenance"
        ]
        
        for announcement_text in announcements:
            for classroom in classrooms[:2]:  # Add to first 2 classrooms
                staff = random.choice([m for m in staff_members if classroom in m.classes.all()])
                if staff:
                    Announcement.objects.create(
                        title=announcement_text,
                        content=f"This is regarding {announcement_text.lower()} Please make note of it.",
                        created_by=staff,
                        classroom=classroom,
                        important=random.choice([True, False])
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully generated comprehensive sample data!')
        )
        self.stdout.write('\nSample Login Credentials:')
        self.stdout.write('HOD CSE: hod_cse / password123')
        self.stdout.write('Staff 1: staff1 / password123')
        self.stdout.write('Student 1: student1 / password123')
        self.stdout.write(f'\nGenerated:')
        self.stdout.write(f'- {Department.objects.count()} Departments')
        self.stdout.write(f'- {ClassRoom.objects.count()} Classrooms')
        self.stdout.write(f'- {StaffProfile.objects.count()} Staff Members')
        self.stdout.write(f'- {StudentProfile.objects.count()} Students')
        self.stdout.write(f'- {Attendance.objects.count()} Attendance Records')
        self.stdout.write(f'- {Mark.objects.count()} Marks Records')
        self.stdout.write(f'- {Announcement.objects.count()} Announcements')