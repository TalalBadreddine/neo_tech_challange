# Generated by Django 5.1.3 on 2024-11-08 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_transaction_partitioning'),
    ]

    operations = [
        migrations.CreateModel(
            name='ETLJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_name', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('records_processed', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='MaterializedViewRefresh',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('view_name', models.CharField(max_length=100)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('success', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('duration_seconds', models.FloatField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
    ]
