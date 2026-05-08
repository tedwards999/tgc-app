from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_subscription_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='company_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='user',
            name='industry',
            field=models.CharField(
                blank=True,
                max_length=30,
                choices=[
                    ('accountancy_finance', 'Accountancy & Finance'),
                    ('construction_property', 'Construction & Property'),
                    ('creative_design', 'Creative & Design'),
                    ('education_training', 'Education & Training'),
                    ('food_hospitality', 'Food & Hospitality'),
                    ('health_wellness', 'Health & Wellness'),
                    ('legal_professional', 'Legal & Professional Services'),
                    ('manufacturing', 'Manufacturing'),
                    ('marketing_pr', 'Marketing & PR'),
                    ('retail_ecommerce', 'Retail & E-commerce'),
                    ('technology_software', 'Technology & Software'),
                    ('transport_logistics', 'Transport & Logistics'),
                    ('other', 'Other'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.CharField(blank=True, max_length=140),
        ),
    ]
