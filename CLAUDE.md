# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Growth Collective — a networking, coaching, and community platform for business owners. Full specification is in `growth-collective-spec.md`.

## Common Commands

```bash
# Run dev server
python manage.py runserver

# Run all tests
python manage.py test

# Run tests for a single app
python manage.py test apps.billing

# Run a single test
python manage.py test apps.billing.tests.test_views.WebhookViewTest

# Apply migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Django shell
python manage.py shell

# Collect static files (production)
python manage.py collectstatic --no-input
```

## Tech Stack

- **Backend:** Python 3.12+, Django 5.x, Gunicorn, Nginx/Caddy
- **Database:** PostgreSQL 16 (DigitalOcean Managed Databases)
- **Frontend:** Server-rendered Django templates, plain CSS, HTMX, optional Alpine.js — no build step, no node_modules
- **Background jobs:** `django-q2` (preferred over Celery to avoid Redis dependency)
- **Auth:** `django.contrib.auth` + `django-allauth` (email/password only, no social login)
- **Payments:** PayPal Subscriptions API via direct `requests` calls (no third-party wrapper)
- **Email:** Postmark or Resend via `django-anymail`
- **File storage:** DigitalOcean Spaces via `django-storages` (S3-compatible); signed URLs for premium assets
- **Settings:** `django-environ` for env-var config
- **Static files:** `whitenoise`

## Project Structure

```
growth_collective/
├── config/               # Django project settings (base.py, dev.py, prod.py), urls.py, wsgi.py
├── apps/
│   ├── accounts/         # Custom User model, profile, auth extensions
│   ├── billing/          # PayPal integration, subscription plans, webhook handling
│   ├── bookings/         # 1:1 coaching session bookings
│   ├── events/           # Webinars + formal training sessions
│   ├── brand_assets/     # Media kit downloads (subscriber-only)
│   ├── referrals/        # Internal + external dual referral system
│   ├── offers/           # The Collective Advantage members-only marketplace
│   ├── points/           # Points ledger and ranking calculations
│   ├── content/          # CMS pages
│   ├── notifications/    # Email sending and templates
│   └── core/             # Shared utilities, base templates, middleware
├── templates/
│   ├── base.html
│   ├── partials/         # HTMX fragment templates
│   └── emails/           # Transactional email templates
└── static/css/
    ├── tokens.css        # CSS variables (colours, spacing, typography)
    ├── base.css          # Element defaults
    ├── layout.css        # Page shell and grid
    ├── components.css    # Buttons, cards, forms, badges, tables, modals
    └── utilities.css     # Small helpers
```

## Architecture Patterns

**Subscription as access gate:** `subscription_status` on the user profile is the single source of truth for access control across every module. Use a decorator or mixin to enforce this consistently rather than ad-hoc checks in views.

**HTMX conventions:** `django-htmx` middleware adds `request.htmx`. Views return partial templates when `request.htmx` is true, full pages otherwise. All forms must work without JS — HTMX is progressive enhancement only.

**PayPal webhooks:** Handled by a dedicated view in `apps/billing/` with signature verification before any state changes. Never trust webhook payload without verification.

**Admin as CMS:** Django Admin is the primary content management interface (~70% of CMS needs). Avoid building custom admin UIs when `ModelAdmin` customisation suffices.

**Postgres features:** Use `JSONField`, `tstzrange` (via `django.contrib.postgres`), exclusion constraints, and partial unique indexes where appropriate — don't reach for application-level workarounds when the DB can enforce invariants natively.

## CSS Conventions

- Plain CSS only — no Tailwind, no SASS, no PostCSS
- BEM-ish naming: `.card`, `.card__title`, `.card--featured`
- All design tokens (colours, spacing, etc.) defined as CSS variables in `tokens.css`
- Single breakpoint at 768px for mobile
- Visual regression: `/dev/styleguide` renders every component in every state

## Environment

Config is loaded from `.env` (local only, never committed) via `django-environ`. Set `DJANGO_SETTINGS_MODULE` to `config.settings.dev` locally and `config.settings.prod` in production.


## To Do File

Plan out what you are going to do and create a to_do.txt where you should list out everything that needs to be done as a series of steps. As you complete these steps we will tick them off one by one. 

## Readibility is king

I like clean readible code over fancy stuff, keep the code readible for a human and as easy to understand as possible.
