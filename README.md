# NeuSchool — Django + Neon PostgreSQL + VdoCipher DRM

Production-oriented full-stack educational platform built with Django. It is structured for Vercel deployment, Neon PostgreSQL, VdoCipher DRM video delivery, and Cloudinary for course banners/material files.

## Included

- Premium NeuSchool frontend
- Django authentication and password hashing
- Sign up: name, email, password, optional contact info, optional community motive
- Course catalog, details, enrollment, and My Courses
- Faculty page
- Section / subsection / lecture / material structure
- Enrolled-user course learning area
- Course Q/A where enrolled users can ask and answer
- Admin Q/A response workflow
- Custom staff dashboard: CREATE / MANAGE / VIEW courses
- Secure browser-to-VdoCipher video upload from the staff dashboard
- VdoCipher DRM playback using short-lived server-generated OTP + playbackInfo
- Viewer-specific moving watermark
- Optional VdoCipher domain whitelist
- Internal user ID sent to VdoCipher for viewer analytics (not email/phone)
- PostgreSQL through `DATABASE_URL` (Neon-ready)
- WhiteNoise static assets
- Cloudinary-ready course banners/material uploads
- Vercel build-time migrations

## Important DRM architecture

Video files are **not uploaded through Django/Vercel**. The staff browser asks Django for temporary VdoCipher upload credentials, then uploads the large video file directly to VdoCipher. This avoids sending large video files through a serverless function.

Playback is also access-controlled:

1. User logs in.
2. NeuSchool confirms the user is enrolled in the course.
3. Django requests a short-lived playback OTP from VdoCipher using the server-only API secret.
4. Browser receives only the short-lived player URL.
5. VdoCipher serves encrypted DRM playback.

The VdoCipher API secret is never included in frontend JavaScript.

> DRM substantially improves protection against direct downloads and casual sharing, but no web DRM can guarantee that content can never be captured by every possible external method.

Official VdoCipher references:
- Playback OTP: https://www.vdocipher.com/docs/server/playbackauth/otp/
- Player embed: https://www.vdocipher.com/docs/player/v2/
- Browser upload: https://www.vdocipher.com/docs/server/upload/browser/
- Upload credentials: https://www.vdocipher.com/docs/server/upload/credentials/
- Viewer analytics: https://www.vdocipher.com/docs/server/playbackauth/viewer/
- Watermark/annotation: https://www.vdocipher.com/docs/server/playbackauth/anno/

## 1. Local setup

Python 3.12+ is expected.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create local configuration:

```bash
cp .env.example .env
```

For a quick local UI test, you can leave `DATABASE_URL` empty/removed and Django will use SQLite. DRM playback/upload requires a valid VdoCipher API secret.

Run migrations:

```bash
python manage.py migrate
```

Create an admin:

```bash
python manage.py createsuperuser
```

Run:

```bash
python manage.py runserver
```

## 2. Neon PostgreSQL

Create a Neon project and copy the **pooled PostgreSQL connection string**. Set it as:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

The Django settings automatically switch from local SQLite to PostgreSQL whenever `DATABASE_URL` is present.

## 3. VdoCipher DRM setup

Create/configure a VdoCipher account and get the API Secret from its API settings.

Set:

```env
VDOCIPHER_API_SECRET=your-server-only-api-secret
VDOCIPHER_FOLDER_ID=
VDOCIPHER_OTP_TTL=300
VDOCIPHER_WATERMARK_ENABLED=1
```

After your production domain is final, optionally restrict playback:

```env
VDOCIPHER_ALLOWED_DOMAIN=neuschool\.com
```

Do not put `VDOCIPHER_API_SECRET` in HTML, JavaScript, GitHub, or any public variable.

### Staff video upload

Open:

```text
/staff/courses/manage/
```

Load a course. Use **UPLOAD DRM LECTURE**. The browser uploads the selected file directly to VdoCipher and NeuSchool stores the returned `videoId` in PostgreSQL.

You can also use **ATTACH EXISTING VDOCIPHER VIDEO** if a video is already uploaded in VdoCipher.

VdoCipher may need processing time after upload before playback becomes available.

## 4. Cloudinary

VdoCipher stores the videos. Cloudinary is only used here for course banners/material file uploads.

Set:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

For Vercel production, configure Cloudinary if you want file uploads through the provided forms; the Vercel function filesystem is not intended as permanent application storage.

## 5. Vercel deployment

Vercel detects Django from `manage.py`. This project also defines its Python version in `.python-version` and dependencies in `pyproject.toml` / `requirements.txt`.

The `[tool.vercel.scripts]` build hook runs:

```bash
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py bootstrap_admin
```

### Required Vercel environment variables

```env
DJANGO_SECRET_KEY=<long-random-secret>
DATABASE_URL=<Neon pooled PostgreSQL URL>
VDOCIPHER_API_SECRET=<VdoCipher secret>
DJANGO_ALLOWED_HOSTS=.vercel.app,yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://yourdomain.com
```

Recommended:

```env
CLOUDINARY_URL=<Cloudinary URL>
VDOCIPHER_ALLOWED_DOMAIN=yourdomain\.com
VDOCIPHER_OTP_TTL=300
VDOCIPHER_WATERMARK_ENABLED=1
SITE_ADDRESS=<your address>
SITE_CONTACT=<your contact information>
```

Optional automatic first admin:

```env
ADMIN_NAME=NeuSchool Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=<strong-password>
```

Before deployment you can validate important variables locally:

```bash
python manage.py verify_production
```

### Neon preview deployments

If you use Vercel Preview Deployments, use an isolated Neon branch/database for preview deployments before allowing automatic migrations. Do not point uncontrolled previews at the same production database.

## 6. Main routes

```text
/                         Home
/courses/                  Courses
/courses/<slug>/           Course details
/my-courses/               Enrolled courses
/learn/<slug>/             Enrolled learning area
/faculty/                  Faculty
/auth/                     Login / Sign up
/staff/                    Custom admin dashboard
/staff/courses/create/     Create course
/staff/courses/manage/     Sections / DRM videos / materials
/staff/courses/view/       Courses + enrollment numbers
/staff/qa/                 Q/A notifications and answers
/django-admin/             Django administration
```

## 7. Production notes

- Keep `DJANGO_DEBUG=0` in production.
- Use HTTPS; Vercel provides HTTPS for deployments/custom domains.
- Keep all API/database secrets in Vercel Environment Variables.
- Use a unique strong `DJANGO_SECRET_KEY`.
- Use a strong admin password.
- VdoCipher playback tokens are generated only after NeuSchool authorization.
- The moving watermark uses the logged-in user's display name and internal NeuSchool user ID; the VdoCipher analytics `userId` uses only the internal numeric ID.
- Configure `VDOCIPHER_ALLOWED_DOMAIN` after your final domain is known.
- Use Neon backups/branching appropriate to your production requirements.
