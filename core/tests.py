from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Course, Enrollment, Lecture, Section


class NeuSchoolSmokeTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            code='TEST-101',
            title='Test Course',
            description='Test description',
            duration_minutes=60,
            is_published=True,
        )
        self.section = Section.objects.create(course=self.course, title='Section', order=1)
        self.lecture = Lecture.objects.create(
            section=self.section,
            title='Secure Lecture',
            vdocipher_video_id='abc123securevideo',
        )
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='strong-pass-123',
        )

    def test_courses_page(self):
        response = self.client.get(reverse('courses'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')

    def test_enrollment(self):
        self.client.login(username='user@example.com', password='strong-pass-123')
        response = self.client.post(reverse('enroll_course', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())

    def test_drm_playback_requires_enrollment(self):
        self.client.login(username='user@example.com', password='strong-pass-123')
        response = self.client.post(reverse('drm_lecture_playback', kwargs={'lecture_id': self.lecture.id}))
        self.assertEqual(response.status_code, 403)

    @patch('core.views.generate_playback')
    def test_drm_playback_for_enrolled_user(self, generate_playback):
        Enrollment.objects.create(user=self.user, course=self.course)
        generate_playback.return_value = {
            'otp': 'short-lived-otp',
            'playbackInfo': 'playback-info',
            'playerUrl': 'https://player.vdocipher.com/v2/?otp=x&playbackInfo=y',
        }
        self.client.login(username='user@example.com', password='strong-pass-123')
        response = self.client.post(reverse('drm_lecture_playback', kwargs={'lecture_id': self.lecture.id}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('player.vdocipher.com', response.json()['player_url'])
        generate_playback.assert_called_once_with(self.lecture.vdocipher_video_id, self.user)

    @patch('core.views.create_upload_credentials')
    def test_drm_upload_credentials_staff_only(self, create_upload_credentials):
        staff = User.objects.create_user('staff@example.com', password='strong-pass-123', is_staff=True)
        create_upload_credentials.return_value = {
            'videoId': 'newvideo123',
            'clientPayload': {'uploadLink': 'https://example.invalid/upload', 'policy': 'p'},
        }
        self.client.login(username='staff@example.com', password='strong-pass-123')
        response = self.client.post(
            reverse('staff_drm_upload_credentials'),
            data='{"title":"Lecture 1"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['videoId'], 'newvideo123')
