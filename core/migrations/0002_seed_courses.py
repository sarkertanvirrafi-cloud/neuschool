from django.db import migrations


def seed(apps, schema_editor):
    Faculty = apps.get_model('core', 'Faculty')
    Course = apps.get_model('core', 'Course')
    Section = apps.get_model('core', 'Section')
    Subsection = apps.get_model('core', 'Subsection')
    Lecture = apps.get_model('core', 'Lecture')

    faculty, _ = Faculty.objects.get_or_create(
        name='Faculty Name',
        defaults={
            'title': 'Faculty',
            'bio': 'Professional faculty bio will be added here later.',
            'specialization': 'Will be added here.',
            'experience': 'Will be added here.',
            'academic_profile': 'Will be added here.',
            'is_featured': True,
        },
    )

    course_data = [
        {
            'code': 'NS-C101',
            'title': 'Data Structure and Algorithm',
            'slug': 'data-structure-and-algorithm',
            'description': 'Build strong problem-solving ability with essential data structures and algorithms.',
            'duration_minutes': 1440,
            'static_banner': 'images/course-dsa.png',
            'banner_symbol': '',
            'sections': ['Foundations', 'Arrays and Lists', 'Stacks and Queues', 'Trees and Graphs'],
        },
        {
            'code': 'NS-C102',
            'title': 'Arabic Foundation',
            'slug': 'arabic-foundation',
            'description': 'A beginner-friendly path to core Arabic letters, pronunciation, and reading.',
            'duration_minutes': 1080,
            'banner_symbol': 'ا',
            'sections': ['Arabic Letters', 'Pronunciation', 'Harakat', 'Word Reading'],
        },
        {
            'code': 'NS-C103',
            'title': 'Quranic Arabic',
            'slug': 'quranic-arabic',
            'description': 'A structured course focused on Quranic Arabic words, patterns, and practical understanding.',
            'duration_minutes': 1320,
            'banner_symbol': 'ق',
            'sections': ['Core Vocabulary', 'Common Patterns', 'Basic Grammar', 'Selected Ayah Study'],
        },
        {
            'code': 'NS-C104',
            'title': 'Spoken Arabic',
            'slug': 'spoken-arabic',
            'description': 'Build confidence in everyday Arabic speaking and listening practice.',
            'duration_minutes': 960,
            'banner_symbol': 'ع',
            'sections': ['Daily Expressions', 'Listening Practice', 'Conversation Drills', 'Situational Practice'],
        },
    ]

    for data in course_data:
        sections = data.pop('sections')
        course, _ = Course.objects.get_or_create(
            code=data['code'],
            defaults={**data, 'faculty_id': faculty.id, 'is_published': True},
        )
        for idx, title in enumerate(sections, start=1):
            section, _ = Section.objects.get_or_create(course_id=course.id, order=idx, defaults={'title': title})
            subsection, _ = Subsection.objects.get_or_create(section_id=section.id, order=1, defaults={'title': f'{title} Basics'})
            Lecture.objects.get_or_create(
                section_id=section.id,
                order=1,
                defaults={
                    'subsection_id': subsection.id,
                    'title': f'{title} — Lecture 01',
                    'youtube_url': '',
                    'duration_minutes': 0,
                },
            )


def unseed(apps, schema_editor):
    Course = apps.get_model('core', 'Course')
    Faculty = apps.get_model('core', 'Faculty')
    Course.objects.filter(code__in=['NS-C101', 'NS-C102', 'NS-C103', 'NS-C104']).delete()
    Faculty.objects.filter(name='Faculty Name').delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]
    operations = [migrations.RunPython(seed, unseed)]
