from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class ClassRoom(models.Model):
    CLASS_CHOICES = [
        ('I_BSC_CS', 'I B.Sc Computer Science'),
        ('II_BSC_CS', 'II B.Sc Computer Science'), 
        ('III_BSC_CS', 'III B.Sc Computer Science'),
        ('I_MSC_CS', 'I M.Sc Computer Science'),
        ('II_MSC_CS', 'II M.Sc Computer Science'),
    ]
    
    name = models.CharField(max_length=100)
    class_code = models.CharField(max_length=20, choices=CLASS_CHOICES, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=20)
    
    class Meta:
        unique_together = ['class_code', 'academic_year']
    
    def __str__(self):
        return f"{self.get_class_code_display()} ({self.academic_year})"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_no = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.roll_no}"

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    designation = models.CharField(max_length=100)
    classes = models.ManyToManyField(ClassRoom, blank=True)
    is_hod = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='staff_photos/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"

# In dept/models.py
from django.contrib.auth.models import User

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Marked By")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'classroom', 'date']
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-set marked_by if not set (you can set this in your view)
        if not self.marked_by and hasattr(self, '_current_user'):
            self.marked_by = self._current_user
        super().save(*args, **kwargs)
        
class Mark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=50)  # Mid-term, Final, etc.
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    maximum_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    entered_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    entered_at = models.DateTimeField(auto_now_add=True)
    
    def percentage(self):
        return (self.marks_obtained / self.maximum_marks) * 100
    
    def __str__(self):
        return f"{self.student.roll_no} - {self.subject} - {self.marks_obtained}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Lecture(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to='lectures/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'student']

# Signals to create profiles automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Profile will be created through registration form
        pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if student profile exists and save it
    if hasattr(instance, 'studentprofile'):
        instance.studentprofile.save()
    # Check if staff profile exists and save it
    if hasattr(instance, 'staffprofile'):
        instance.staffprofile.save()

