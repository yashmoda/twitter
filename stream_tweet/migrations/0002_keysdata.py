# Generated by Django 2.1 on 2018-10-10 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stream_tweet', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeysData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=256)),
                ('value', models.TextField()),
            ],
        ),
    ]