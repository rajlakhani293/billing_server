from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CountryMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True)),
                ('country_code', models.CharField(max_length=10, unique=True, null=True, blank=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'db_table': 'country_master',
                'verbose_name': 'Country',
                'verbose_name_plural': 'Countries',
            },
        ),
        migrations.CreateModel(
            name='StateMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('country', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='core.countrymaster')),
            ],
            options={
                'db_table': 'state_master',
                'verbose_name': 'State',
                'verbose_name_plural': 'States',
            },
        ),
        migrations.CreateModel(
            name='CityMaster',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.statemaster')),
            ],
            options={
                'db_table': 'city_master',
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
            },
        ),
    ]
