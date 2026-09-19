from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.template.defaultfilters import slugify


vdocipher_id_validator = RegexValidator(
    regex=r'^[A-Za-z0-9_-]+$',
    message='Enter a valid VdoCipher video ID.',
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    contact_info = models.CharField(max_length=200, blank=True)
    motive = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Faculty(models.Model):
    name = models.CharField(max_length=160)
    title = models.CharField(max_length=180, blank=True)
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=220, blank=True)
    experience = models.CharField(max_length=220, blank=True)
    academic_profile = models.CharField(max_length=220, blank=True)
    photo_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField(default=0)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    banner_url = models.URLField(blank=True)
    static_banner = models.CharField(max_length=255, blank=True)
    banner_symbol = models.CharField(max_length=10, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or slugify(self.code)
            candidate = base
            index = 2
            while Course.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f'{base}-{index}'
                index += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def formatted_duration(self):
        if not self.duration_minutes:
            return 'To be added'
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours and minutes:
            return f'{hours} hr {minutes} min'
        if hours:
            return f'{hours} hr'
        return f'{minutes} min'

    @property
    def lecture_count(self):
        return Lecture.objects.filter(section__course=self).count()

    @property
    def enrolled_count(self):
        return self.enrollments.count()

    def __str__(self):
        return f'{self.code} — {self.title}'


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=220)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.course.code} / {self.title}'


class Subsection(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subsections')
    title = models.CharField(max_length=220)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.section.title} / {self.title}'


class Lecture(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lectures')
    subsection = models.ForeignKey(Subsection, on_delete=models.SET_NULL, null=True, blank=True, related_name='lectures')
    title = models.CharField(max_length=240)
    vdocipher_video_id = models.CharField(
        max_length=80,
        blank=True,
        db_index=True,
        validators=[vdocipher_id_validator],
        help_text='VdoCipher video ID. The API secret is never stored here.',
    )
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['section__order', 'order', 'id']

    @property
    def has_drm_video(self):
        return bool(self.vdocipher_video_id)

    def __str__(self):
        return self.title


class Material(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=220)
    file_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'course')]
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.user.username} → {self.course.code}'


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    lecture = models.ForeignKey(Lecture, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    asked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    body = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def has_admin_answer(self):
        return self.answers.filter(is_admin_answer=True).exists()

    def __str__(self):
        return f'Q#{self.pk} {self.course.code}'


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    body = models.TextField()
    is_admin_answer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Answer #{self.pk}'
