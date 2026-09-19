from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses, name='courses'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('learn/<slug:slug>/', views.course_learning, name='course_learning'),
    path('faculty/', views.faculty_page, name='faculty'),
    path('auth/', views.auth_page, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('drm/lectures/<int:lecture_id>/play/', views.drm_lecture_playback, name='drm_lecture_playback'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/courses/create/', views.staff_course_create, name='staff_course_create'),
    path('staff/courses/manage/', views.staff_course_manage, name='staff_course_manage'),
    path('staff/courses/view/', views.staff_course_view, name='staff_course_view'),
    path('staff/drm/upload-credentials/', views.staff_drm_upload_credentials, name='staff_drm_upload_credentials'),
    path('staff/drm/finalize-upload/', views.staff_drm_finalize_upload, name='staff_drm_finalize_upload'),
    path('staff/qa/', views.staff_qa, name='staff_qa'),
]
