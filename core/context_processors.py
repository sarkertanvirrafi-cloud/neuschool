from django.conf import settings


def site_context(request):
    return {
        'SITE_ADDRESS': settings.SITE_ADDRESS,
        'SITE_CONTACT': settings.SITE_CONTACT,
    }
