from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dept.models import *
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create Department
        dept, created = Department.objects.get_or_create(
            name="Computer Science",
            code="CS",
            description="Department of Computer Science"
        )
        
        # Create Classrooms for B.Sc and M.Sc
        classrooms = []
        class_data = [
            {'code': 'I_BSC_CS', 'name': 'I B.Sc Computer Science'},
            {'code': 'II_BSC_CS', 'name': 'II B.Sc Computer Science'},
            {'code': 'III_BSC_CS', 'name': 'III B.Sc Computer Science'},
            {'code': 'I_MSC_CS', 'name': 'I M.Sc Computer Science'},
            {'code': 'II_MSC_CS', 'name': 'II M.Sc Computer Science'},
        ]
        
        for class_info in class_data:
            classroom, created = ClassRoom.objects.get_or_create(
                class_code=class_info['code'],
                defaults={
                    'name': class_info['name'],
                    'department': dept,
                    'academic_year': '2024-25'
                }
            )
            classrooms.append(classroom)
        
        # Create HOD
        hod_user, created = User.objects.get_or_create(
            username='hod_cs',
            defaults={
                'first_name': 'Dr. Rajesh',
                'last_name': 'Kumar',
                'email': 'hod.cs@university.edu',
                'is_staff': True
            }
        )
        hod_user.set_password('password123')
        hod_user.save()
        
        hod_profile, created = StaffProfile.objects.get_or_create(
            user=hod_user,
            defaults={
                'staff_id': 'HODCS001',
                'department': dept,
                'designation': 'Head of Department',
                'is_hod': True
            }
        )
        hod_profile.classes.set(classrooms)
        
        # Create Staff Members
        staff_members = []
        staff_data = [
            {'username': 'staff1', 'staff_id': 'STF001', 'name': 'Dr. Priya', 'lastname': 'Sharma'},
            {'username': 'staff2', 'staff_id': 'STF002', 'name': 'Dr. Amit', 'lastname': 'Patel'},
            {'username': 'staff3', 'staff_id': 'STF003', 'name': 'Dr. Sneha', 'lastname': 'Reddy'},
        ]
        
        for data in staff_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['name'],
                    'last_name': data['lastname'],
                    'email': f"{data['username']}@university.edu",
                    'is_staff': True
                }
            )
            user.set_password('password123')
            user.save()
            
            staff, created = StaffProfile.objects.get_or_create(
                staff_id=data['staff_id'],
                defaults={
                    'user': user,
                    'department': dept,
                    'designation': 'Assistant Professor'
                }
            )
            # Assign 2-3 random classrooms to each staff
            assigned_classes = random.sample(classrooms, min(3, len(classrooms)))
            staff.classes.set(assigned_classes)
            staff_members.append(staff)
        
        # Create Sample Students for each class
        students = []
        class_student_count = {
            'I_BSC_CS': 8,
            'II_BSC_CS': 7, 
            'III_BSC_CS': 6,
            'I_MSC_CS': 5,
            'II_MSC_CS': 4
        }
        
        student_counter = 1
        for class_code, count in class_student_count.items():
            classroom = ClassRoom.objects.get(class_code=class_code)
            
            for i in range(count):
                user, created = User.objects.get_or_create(
                    username=f'student{student_counter}',
                    defaults={
                        'first_name': f'Student{student_counter}',
                        'last_name': f'LastName{student_counter}',
                        'email': f'student{student_counter}@university.edu'
                    }
                )
                user.set_password('password123')
                user.save()
                
                # Generate roll number based on class
                year_prefix = '24' if 'BSC' in class_code else '23'
                roll_no = f"CS{year_prefix}{student_counter:03d}"
                
                student, created = StudentProfile.objects.get_or_create(
                    roll_no=roll_no,
                    defaults={
                        'user': user,
                        'department': dept,
                        'classroom': classroom,
                        'phone': f'98765432{student_counter:02d}',
                        'is_approved': True
                    }
                )
                students.append(student)
                student_counter += 1
        
        # Generate Attendance Records
        self.stdout.write('Generating attendance records...')
        for student in students:
            for day in range(30):
                record_date = date.today() - timedelta(days=day)
                if random.random() > 0.15:  # 85% attendance rate
                    status = 'P'
                else:
                    status = 'A'
                
                # Get staff who teaches this class
                class_staff = [s for s in staff_members if student.classroom in s.classes.all()]
                if class_staff:
                    marked_by = random.choice(class_staff)
                    
                    Attendance.objects.get_or_create(
                        student=student,
                        date=record_date,
                        defaults={
                            'classroom': student.classroom,
                            'status': status,
                            'marked_by': marked_by
                        }
                    )
        
        # Generate Marks
        self.stdout.write('Generating marks records...')
        subjects = {
            'I_BSC_CS': ['Programming Fundamentals', 'Mathematics I', 'Digital Electronics'],
            'II_BSC_CS': ['Data Structures', 'Database Systems', 'Operating Systems'],
            'III_BSC_CS': ['Algorithms', 'Computer Networks', 'Software Engineering'],
            'I_MSC_CS': ['Advanced Algorithms', 'Machine Learning', 'Big Data Analytics'],
            'II_MSC_CS': ['Deep Learning', 'Cloud Computing', 'Research Methodology']
        }
        
        exam_types = ['Mid-term', 'Final', 'Assignment']
        
        for student in students:
            class_subjects = subjects.get(student.classroom.class_code, ['Subject 1', 'Subject 2', 'Subject 3'])
            
            for subject in class_subjects:
                for exam_type in exam_types:
                    # Get staff who teaches this class
                    class_staff = [s for s in staff_members if student.classroom in s.classes.all()]
                    if class_staff:
                        entered_by = random.choice(class_staff)
                        
                        Mark.objects.get_or_create(
                            student=student,
                            classroom=student.classroom,
                            subject=subject,
                            exam_type=exam_type,
                            defaults={
                                'marks_obtained': round(random.uniform(65, 95), 2),
                                'maximum_marks': 100,
                                'entered_by': entered_by
                            }
                        )
        
        # Generate Announcements
        self.stdout.write('Generating announcements...')
        announcements = [
            "Mid-term examination schedule released for all classes",
            "Last date for project submission extended",
            "Guest lecture on Artificial Intelligence and Machine Learning",
            "College will remain closed for Diwali festival",
            "Library will remain closed for maintenance this weekend",
            "Industrial visit scheduled for final year students",
            "Placement training program starts next week"
        ]
        
        for announcement_text in announcements:
            for classroom in classrooms[:3]:  # Add to first 3 classrooms
                staff = random.choice([m for m in staff_members if classroom in m.classes.all()])
                if staff:
                    Announcement.objects.create(
                        title=announcement_text,
                        content=f"This is regarding {announcement_text.lower()} Please make note of it and follow the instructions accordingly.",
                        created_by=staff,
                        classroom=classroom,
                        important=random.choice([True, False])
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully generated sample data with B.Sc/M.Sc classes!')
        )
        self.stdout.write('\nSample Login Credentials:')
        self.stdout.write('HOD CS: hod_cs / password123')
        self.stdout.write('Staff 1: staff1 / password123')
        self.stdout.write('Student 1: student1 / password123')
        self.stdout.write(f'\nGenerated:')
        self.stdout.write(f'- {Department.objects.count()} Departments')
        self.stdout.write(f'- {ClassRoom.objects.count()} Classes')
        self.stdout.write(f'- {StaffProfile.objects.count()} Staff Members')
        self.stdout.write(f'- {StudentProfile.objects.count()} Students')
        self.stdout.write(f'- {Attendance.objects.count()} Attendance Records')
        self.stdout.write(f'- {Mark.objects.count()} Marks Records')
        self.stdout.write(f'- {Announcement.objects.count()} Announcements')
        
        self.stdout.write('\nClasses Created:')
        for classroom in ClassRoom.objects.all():
            student_count = StudentProfile.objects.filter(classroom=classroom).count()
            self.stdout.write(f'- {classroom.name}: {student_count} students')