# Generated by Django 4.2.18 on 2025-03-10 18:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Landlord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.TextField()),
                ('landlord', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='properties', to='properties.landlord')),
            ],
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('whatsapp_number', models.CharField(max_length=20)),
                ('rent_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('start_of_payment_cycle', models.DateField()),
                ('bills_due_date', models.DateField()),
                ('last_rent_paid', models.DateField(blank=True, null=True)),
                ('last_bill_paid', models.DateField(blank=True, null=True)),
                ('payment_cycle_months', models.PositiveIntegerField(default=1)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenants', to='properties.property')),
            ],
        ),
    ]
