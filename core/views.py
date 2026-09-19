import json
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import (
    AnswerForm,
    CourseForm,
    LectureForm,
    LoginForm,
    MaterialForm,
    QuestionForm,
    SectionForm,
    SignUpForm,
    SubsectionForm,
)
from .models import Answer, Course, Enrollment, Faculty, Lecture, Material, Question, Section, Subsection, UserProfile
from .drm import DRMConfigurationError, DRMServiceError, create_upload_credentials, generate_playback
from .storage import upload_asset

logger = logging.getLogger(__name__)


def _staff_check(user):
    return user.is_authenticated and user.is_staff


def home(request):
    courses = Course.objects.filter(is_published=True).select_related('faculty')[:4]
    return render(request, 'home.html', {'courses': courses})


def courses(request):
    course_list = Course.objects.filter(is_published=True).select_related('faculty')
    return render(request, 'courses.html', {'courses': course_list})


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.select_related('faculty').prefetch_related('sections__subsections'),
        slug=slug,
        is_published=True,
    )
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    return render(request, 'course_detail.html', {'course': course, 'is_enrolled': is_enrolled})


@require_POST
@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    Enrollment.objects.get_or_create(user=request.user, course=course)
    messages.success(request, f'You are enrolled in {course.title}.')
    return redirect('course_learning', slug=course.slug)


def faculty_page(request):
    faculty = Faculty.objects.filter(is_featured=True).first() or Faculty.objects.first()
    return render(request, 'faculty.html', {'faculty': faculty})


def auth_page(request):
    if request.user.is_authenticated:
        course_slug = request.GET.get('course') or request.POST.get('course')
        if course_slug:
            course = get_object_or_404(Course, slug=course_slug, is_published=True)
            Enrollment.objects.get_or_create(user=request.user, course=course)
            return redirect('course_learning', slug=course.slug)
        return redirect('courses')

    mode = request.POST.get('mode') or request.GET.get('mode') or 'login'
    course_slug = request.GET.get('course') or request.POST.get('course') or ''
    login_form = LoginForm(prefix='login')
    signup_form = SignUpForm(prefix='signup')

    if request.method == 'POST' and mode == 'login':
        login_form = LoginForm(request.POST, prefix='login')
        if login_form.is_valid():
            email = login_form.cleaned_data['email'].strip().lower()
            password = login_form.cleaned_data['password']
            user_obj = User.objects.filter(email__iexact=email).first()
            user = authenticate(
                request,
                username=user_obj.username if user_obj else email,
                password=password,
            )
            if user:
                login(request, user)
                if course_slug:
                    course = get_object_or_404(Course, slug=course_slug, is_published=True)
                    Enrollment.objects.get_or_create(user=user, course=course)
                    return redirect('course_learning', slug=course.slug)
                return redirect('courses')
            login_form.add_error(None, 'Invalid email or password.')

    if request.method == 'POST' and mode == 'signup':
        signup_form = SignUpForm(request.POST, prefix='signup')
        if signup_form.is_valid():
            email = signup_form.cleaned_data['email']
            name = signup_form.cleaned_data['name'].strip()
            password = signup_form.cleaned_data['password']
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
            )
            UserProfile.objects.create(
                user=user,
                contact_info=signup_form.cleaned_data.get('contact_info', ''),
                motive=signup_form.cleaned_data.get('motive', ''),
            )
            login(request, user)
            if course_slug:
                course = get_object_or_404(Course, slug=course_slug, is_published=True)
                Enrollment.objects.get_or_create(user=user, course=course)
                return redirect('course_learning', slug=course.slug)
            return redirect('courses')

    return render(
        request,
        'auth.html',
        {
            'mode': mode,
            'course_slug': course_slug,
            'login_form': login_form,
            'signup_form': signup_form,
        },
    )


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def my_courses(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related('course', 'course__faculty')
        .order_by('-enrolled_at')
    )
    return render(request, 'my_courses.html', {'enrollments': enrollments})


@login_required
def course_learning(request, slug):
    course = get_object_or_404(
        Course.objects.select_related('faculty').prefetch_related(
            'sections__subsections',
            'sections__lectures__materials',
            'sections__lectures__subsection',
        ),
        slug=slug,
        is_published=True,
    )
    if not request.user.is_staff and not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'Please enroll before opening this course.')
        return redirect('course_detail', slug=course.slug)

    question_form = QuestionForm(course=course)
    answer_form = AnswerForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ask':
            question_form = QuestionForm(request.POST, course=course)
            if question_form.is_valid():
                Question.objects.create(
                    course=course,
                    lecture=question_form.cleaned_data.get('lecture'),
                    asked_by=request.user,
                    body=question_form.cleaned_data['body'],
                )
                messages.success(request, 'Your question has been posted.')
                return redirect('course_learning', slug=course.slug)
        elif action == 'answer':
            answer_form = AnswerForm(request.POST)
            if answer_form.is_valid():
                question = get_object_or_404(Question, pk=answer_form.cleaned_data['question_id'], course=course)
                Answer.objects.create(
                    question=question,
                    author=request.user,
                    body=answer_form.cleaned_data['body'],
                    is_admin_answer=request.user.is_staff,
                )
                messages.success(request, 'Your answer has been posted.')
                return redirect('course_learning', slug=course.slug)

    questions = (
        Question.objects.filter(course=course)
        .select_related('asked_by', 'lecture')
        .prefetch_related('answers__author')
    )
    return render(
        request,
        'course_learning.html',
        {
            'course': course,
            'question_form': question_form,
            'answer_form': answer_form,
            'questions': questions,
        },
    )


@user_passes_test(_staff_check, login_url='/auth/')
def staff_dashboard(request):
    total_courses = Course.objects.count()
    total_users = User.objects.filter(is_staff=False).count()
    unanswered = Question.objects.annotate(
        admin_answer_count=Count('answers', filter=Q(answers__is_admin_answer=True))
    ).filter(admin_answer_count=0).count()
    return render(
        request,
        'staff/dashboard.html',
        {
            'staff_section': 'courses',
            'total_courses': total_courses,
            'total_users': total_users,
            'unanswered': unanswered,
        },
    )


@user_passes_test(_staff_check, login_url='/auth/')
def staff_course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        banner_file = form.cleaned_data.get('banner_file')
        if banner_file:
            course.banner_url = upload_asset(banner_file, folder='neuschool/course-banners', resource_type='image')
        course.save()
        messages.success(request, 'Course created. Add sections, lectures, and materials now.')
        return redirect(f"{reverse('staff_course_manage')}?q={course.code}")
    return render(request, 'staff/course_create.html', {'form': form, 'staff_section': 'courses'})


@user_passes_test(_staff_check, login_url='/auth/')
def staff_course_manage(request):
    query = (request.GET.get('q') or request.POST.get('course_lookup') or '').strip()
    course = None
    if query:
        course = Course.objects.filter(Q(code__iexact=query) | Q(title__iexact=query)).first()
        if not course:
            course = Course.objects.filter(Q(code__icontains=query) | Q(title__icontains=query)).first()

    section_form = SectionForm(prefix='section')
    subsection_form = SubsectionForm(prefix='subsection', course=course)
    lecture_form = LectureForm(prefix='lecture', course=course)
    material_form = MaterialForm(prefix='material', course=course)

    if request.method == 'POST':
        if not course:
            messages.error(request, 'Load a course by Course ID or title first.')
        else:
            action = request.POST.get('action')
            if action == 'add_section':
                section_form = SectionForm(request.POST, prefix='section')
                if section_form.is_valid():
                    section = section_form.save(commit=False)
                    section.course = course
                    section.save()
                    messages.success(request, 'Section added.')
                    return redirect(f"{reverse('staff_course_manage')}?q={course.code}")
            elif action == 'add_subsection':
                subsection_form = SubsectionForm(request.POST, prefix='subsection', course=course)
                if subsection_form.is_valid():
                    subsection_form.save()
                    messages.success(request, 'Subsection added.')
                    return redirect(f"{reverse('staff_course_manage')}?q={course.code}")
            elif action == 'add_lecture':
                lecture_form = LectureForm(request.POST, prefix='lecture', course=course)
                if lecture_form.is_valid():
                    lecture_form.save()
                    messages.success(request, 'Lecture added.')
                    return redirect(f"{reverse('staff_course_manage')}?q={course.code}")
            elif action == 'add_material':
                material_form = MaterialForm(request.POST, request.FILES, prefix='material', course=course)
                if material_form.is_valid():
                    url = material_form.cleaned_data.get('material_url')
                    upload = material_form.cleaned_data.get('material_file')
                    if upload:
                        url = upload_asset(upload, folder='neuschool/materials', resource_type='raw')
                    Material.objects.create(
                        lecture=material_form.cleaned_data['lecture'],
                        title=material_form.cleaned_data['title'],
                        file_url=url,
                    )
                    messages.success(request, 'Material added.')
                    return redirect(f"{reverse('staff_course_manage')}?q={course.code}")

    if course:
        course = Course.objects.prefetch_related(
            'sections__subsections',
            'sections__lectures__materials',
            'sections__lectures__subsection',
        ).get(pk=course.pk)

    return render(
        request,
        'staff/course_manage.html',
        {
            'staff_section': 'courses',
            'query': query,
            'course': course,
            'section_form': section_form,
            'subsection_form': subsection_form,
            'lecture_form': lecture_form,
            'material_form': material_form,
        },
    )


@user_passes_test(_staff_check, login_url='/auth/')
def staff_course_view(request):
    course_list = Course.objects.select_related('faculty').annotate(user_count=Count('enrollments'))
    total_users = User.objects.filter(is_staff=False).count()
    return render(request, 'staff/course_view.html', {'courses': course_list, 'total_users': total_users, 'staff_section': 'courses'})


@user_passes_test(_staff_check, login_url='/auth/')
def staff_qa(request):
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            question = get_object_or_404(Question, pk=form.cleaned_data['question_id'])
            Answer.objects.create(
                question=question,
                author=request.user,
                body=form.cleaned_data['body'],
                is_admin_answer=True,
            )
            question.is_resolved = True
            question.save(update_fields=['is_resolved'])
            messages.success(request, 'Admin answer posted.')
            return redirect('staff_qa')

    course_list = list(Course.objects.annotate(question_count=Count('questions', distinct=True)))
    for course in course_list:
        course.unanswered_count = course.questions.annotate(
            admin_answer_count=Count('answers', filter=Q(answers__is_admin_answer=True))
        ).filter(admin_answer_count=0).count()
    questions = Question.objects.select_related('course', 'lecture', 'asked_by').prefetch_related('answers__author')[:100]
    return render(request, 'staff/qa.html', {'courses': course_list, 'questions': questions, 'staff_section': 'qa'})


@login_required
@require_POST
@never_cache
def drm_lecture_playback(request, lecture_id):
    """Return short-lived VdoCipher playback data after access verification."""
    lecture = get_object_or_404(
        Lecture.objects.select_related('section__course'),
        pk=lecture_id,
    )
    course = lecture.section.course
    if not course.is_published and not request.user.is_staff:
        return JsonResponse({'error': 'Course is not available.'}, status=404)
    if not request.user.is_staff and not Enrollment.objects.filter(user=request.user, course=course).exists():
        return JsonResponse({'error': 'Enrollment required.'}, status=403)
    if not lecture.vdocipher_video_id:
        return JsonResponse({'error': 'Secure video has not been attached yet.'}, status=404)

    try:
        playback = generate_playback(lecture.vdocipher_video_id, request.user)
    except DRMConfigurationError:
        logger.exception('VdoCipher is not configured.')
        return JsonResponse({'error': 'Secure video is not configured by the administrator.'}, status=503)
    except DRMServiceError as exc:
        return JsonResponse({'error': str(exc)}, status=502)

    response = JsonResponse({
        'player_url': playback['playerUrl'],
        'lecture_id': lecture.pk,
        'title': lecture.title,
    })
    response['Cache-Control'] = 'no-store, private'
    response['Pragma'] = 'no-cache'
    return response


@user_passes_test(_staff_check, login_url='/auth/')
@require_POST
@never_cache
def staff_drm_upload_credentials(request):
    """Create temporary VdoCipher browser-upload credentials for staff."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    title = (payload.get('title') or '').strip()
    if not title:
        return JsonResponse({'error': 'Lecture title is required.'}, status=400)
    try:
        result = create_upload_credentials(title)
    except DRMConfigurationError:
        logger.exception('VdoCipher is not configured.')
        return JsonResponse({'error': 'VDOCIPHER_API_SECRET is not configured.'}, status=503)
    except DRMServiceError as exc:
        return JsonResponse({'error': str(exc)}, status=502)

    response = JsonResponse(result)
    response['Cache-Control'] = 'no-store, private'
    return response


@user_passes_test(_staff_check, login_url='/auth/')
@require_POST
def staff_drm_finalize_upload(request):
    """Create the lecture after the browser has uploaded the video to VdoCipher."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    video_id = (payload.get('video_id') or '').strip()
    title = (payload.get('title') or '').strip()
    try:
        section_id = int(payload.get('section_id'))
        subsection_id = int(payload['subsection_id']) if payload.get('subsection_id') else None
        duration_minutes = max(0, int(payload.get('duration_minutes') or 0))
        order = max(1, int(payload.get('order') or 1))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid lecture metadata.'}, status=400)

    if not video_id or not title:
        return JsonResponse({'error': 'Video ID and lecture title are required.'}, status=400)

    section = get_object_or_404(Section, pk=section_id)
    subsection = None
    if subsection_id:
        subsection = get_object_or_404(Subsection, pk=subsection_id, section=section)

    lecture = Lecture(
        section=section,
        subsection=subsection,
        title=title[:240],
        vdocipher_video_id=video_id[:80],
        duration_minutes=duration_minutes,
        order=order,
    )
    lecture.full_clean()
    lecture.save()
    return JsonResponse({
        'ok': True,
        'lecture_id': lecture.pk,
        'course_code': section.course.code,
        'redirect': f"{reverse('staff_course_manage')}?q={section.course.code}",
    })
