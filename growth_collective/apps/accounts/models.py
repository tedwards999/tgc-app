import secrets
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('coach', 'Coach'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    ]
    INDUSTRY_CHOICES = [
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
    ]
    SUBSCRIPTION_TYPES = [
        ('free', 'Free'),
        ('entry', 'Entry'),
        ('coaching', 'Coaching'),
        ('executive', 'Executive'),
    ]
    SUBSCRIPTION_STATUSES = [
        ('none', 'None'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('suspended', 'Suspended'),
        ('cancelling', 'Cancelling'),
        ('cancelled', 'Cancelled'),
    ]

    objects = UserManager()

    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default='free')
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUSES, default='none')

    company_name = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=30, choices=INDUSTRY_CHOICES, blank=True)
    bio = models.CharField(max_length=140, blank=True)

    referral_token = models.CharField(max_length=64, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals_made'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'accounts_user'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return f'{parts[0][0]}{parts[-1][0]}'.upper()
        return self.full_name[:2].upper()

    def has_premium_access(self):
        """
        Single source of truth for premium access.
        Checks subscription_type AND subscription_status.
        """
        return (
            self.subscription_type in ('entry', 'coaching', 'executive')
            and self.subscription_status in ('active', 'cancelling', 'past_due')
        )

    def save(self, *args, **kwargs):
        if not self.referral_token:
            self.referral_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
