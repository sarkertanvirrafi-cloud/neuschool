from django.contrib import admin
from .models import Answer, Course, Enrollment, Faculty, Lecture, Material, Question, Section, Subsection, UserProfile


class SubsectionInline(admin.TabularInline):
    model = Subsection
    extra = 0


class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 0
    fields = ('title', 'subsection', 'vdocipher_video_id', 'duration_minutes', 'order')


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'is_featured')
    list_filter = ('is_featured',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'faculty', 'is_published', 'created_at')
    search_fields = ('code', 'title')
    list_filter = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'order', 'title')
    list_filter = ('course',)
    inlines = [SubsectionInline, LectureInline]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'vdocipher_video_id', 'duration_minutes', 'order')
    search_fields = ('title', 'vdocipher_video_id', 'section__course__code')
    list_filter = ('section__course',)


admin.site.register(Subsection)
admin.site.register(Material)
admin.site.register(Enrollment)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(UserProfile)
