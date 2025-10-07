from django import forms
from django.contrib.auth.models import User
from .models import *

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['roll_no', 'department', 'classroom', 'phone', 'address', 'photo', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classroom'].queryset = ClassRoom.objects.none()
        
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['classroom'].queryset = ClassRoom.objects.filter(department_id=department_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['classroom'].queryset = self.instance.department.classroom_set

class StaffRegistrationForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['staff_id', 'department', 'phone', 'designation', 'photo']

class MarksEntryForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = ['student', 'classroom', 'subject', 'exam_type', 'marks_obtained', 'maximum_marks']
    
    def __init__(self, staff, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = StudentProfile.objects.filter(
            classroom__in=staff.classes.all(),
            is_approved=True
        )
        self.fields['classroom'].queryset = staff.classes.all()

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'classroom', 'important']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, staff, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classroom'].queryset = staff.classes.all()

class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['title', 'description', 'classroom', 'file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, staff, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classroom'].queryset = staff.classes.all()

