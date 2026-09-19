from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [('core', '0002_seed_courses')]

    operations = [
        migrations.AddField(
            model_name='lecture',
            name='vdocipher_video_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='VdoCipher video ID. The API secret is never stored here.',
                max_length=80,
                validators=[django.core.validators.RegexValidator(
                    message='Enter a valid VdoCipher video ID.',
                    regex='^[A-Za-z0-9_-]+$',
                )],
            ),
        ),
        migrations.RemoveField(model_name='lecture', name='youtube_url'),
    ]
