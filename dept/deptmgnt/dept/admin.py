from django.contrib import admin
from .models import *

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'established_date']
    search_fields = ['name', 'code']
    list_filter = ['established_date']

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_code', 'department', 'academic_year']
    list_filter = ['department', 'class_code', 'academic_year']
    search_fields = ['name', 'class_code', 'academic_year']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['roll_no', 'user', 'department', 'classroom', 'is_approved', 'created_at']
    list_filter = ['department', 'classroom', 'is_approved', 'created_at']
    search_fields = ['roll_no', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at']
    actions = ['approve_students', 'disapprove_students']

    def approve_students(self, request, queryset):
        queryset.update(is_approved=True)
    approve_students.short_description = "Approve selected students"

    def disapprove_students(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_students.short_description = "Disapprove selected students"

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'user', 'department', 'designation', 'is_hod']
    list_filter = ['department', 'designation', 'is_hod']
    search_fields = ['staff_id', 'user__first_name', 'user__last_name']
    filter_horizontal = ['classes']
    actions = ['approve_staff', 'disapprove_staff']

    def approve_staff(self, request, queryset):
        queryset.update(is_approved=True)
    approve_staff.short_description = "Approve selected staff"

    def disapprove_staff(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_staff.short_description = "Disapprove selected staff"



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'classroom', 'date', 'status', 'marked_by']
    list_filter = ['classroom', 'date', 'status', 'marked_by']
    search_fields = ['student__roll_no', 'student__user__first_name']
    readonly_fields = ['marked_by']

    def save_model(self, request, obj, form, change):
        if not obj.marked_by_id:
            if hasattr(request.user, 'staffprofile'):
                obj.marked_by = request.user.staffprofile
        super().save_model(request, obj, form, change)

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'marks_obtained', 'maximum_marks', 'entered_by']
    list_filter = ['classroom', 'exam_type', 'entered_by']
    search_fields = ['student__roll_no', 'subject']
    readonly_fields = ['entered_by', 'entered_at']

    def save_model(self, request, obj, form, change):
        if not obj.entered_by_id:
            if hasattr(request.user, 'staffprofile'):
                obj.entered_by = request.user.staffprofile
        super().save_model(request, obj, form, change)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'classroom', 'created_by', 'important', 'created_at']
    list_filter = ['classroom', 'important', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            if hasattr(request.user, 'staffprofile'):
                obj.created_by = request.user.staffprofile
        super().save_model(request, obj, form, change)

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ['title', 'classroom', 'uploaded_by', 'uploaded_at']
    list_filter = ['classroom', 'uploaded_at']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_by', 'uploaded_at']

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            if hasattr(request.user, 'staffprofile'):
                obj.uploaded_by = request.user.staffprofile
        super().save_model(request, obj, form, change)

@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ['announcement', 'student', 'read_at']
    list_filter = ['read_at']
    search_fields = ['announcement__title', 'student__roll_no']

from django.contrib import admin
from .models import Announcement

# Check if Announcement is already registered and unregister it
try:
    admin.site.unregister(Announcement)
except admin.sites.NotRegistered:
    pass




