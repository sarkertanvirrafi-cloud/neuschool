from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Course, Lecture, Section, Subsection


class SignUpForm(forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    contact_info = forms.CharField(max_length=200, required=False)
    motive = forms.CharField(widget=forms.Textarea, required=False)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class CourseForm(forms.ModelForm):
    banner_file = forms.FileField(required=False)

    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'duration_minutes', 'faculty', 'is_published']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['title', 'order']


class SubsectionForm(forms.ModelForm):
    section = forms.ModelChoiceField(queryset=Section.objects.none())

    class Meta:
        model = Subsection
        fields = ['section', 'title', 'order']

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields['section'].queryset = course.sections.all()


class LectureForm(forms.ModelForm):
    """Manual fallback for linking a video already uploaded to VdoCipher."""
    section = forms.ModelChoiceField(queryset=Section.objects.none())
    subsection = forms.ModelChoiceField(queryset=Subsection.objects.none(), required=False)

    class Meta:
        model = Lecture
        fields = ['section', 'subsection', 'title', 'vdocipher_video_id', 'duration_minutes', 'order']

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields['section'].queryset = course.sections.all()
            self.fields['subsection'].queryset = Subsection.objects.filter(section__course=course)

    def clean(self):
        data = super().clean()
        section = data.get('section')
        subsection = data.get('subsection')
        if subsection and section and subsection.section_id != section.id:
            self.add_error('subsection', 'The subsection must belong to the selected section.')
        return data


class MaterialForm(forms.Form):
    lecture = forms.ModelChoiceField(queryset=Lecture.objects.none())
    title = forms.CharField(max_length=220)
    material_file = forms.FileField(required=False)
    material_url = forms.URLField(required=False)

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields['lecture'].queryset = Lecture.objects.filter(section__course=course)

    def clean(self):
        data = super().clean()
        if not data.get('material_file') and not data.get('material_url'):
            raise ValidationError('Upload a material file or provide a material URL.')
        return data


class QuestionForm(forms.Form):
    lecture = forms.ModelChoiceField(queryset=Lecture.objects.none(), required=False)
    body = forms.CharField(widget=forms.Textarea, max_length=4000)

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields['lecture'].queryset = Lecture.objects.filter(section__course=course)


class AnswerForm(forms.Form):
    question_id = forms.IntegerField(widget=forms.HiddenInput)
    body = forms.CharField(widget=forms.Textarea, max_length=4000)
