# Growth Collective — Platform Specification

**Coaching, Events, Community & CMS — Complete Build Specification**

**Stack:** Django + PostgreSQL (DigitalOcean) + server-rendered templates + plain CSS + HTMX

---

## Overview

This document specifies the full Growth Collective platform — a networking, coaching, and community ecosystem for business owners. It defines every module required to build, launch, and operate the platform.

The platform combines the following systems into a single integrated product:

- 1:1 coaching session bookings
- Group events (webinars and formal training sessions)
- Subscriber brand asset access
- Dual referral and reputation system
- The Collective Advantage members-only offers marketplace
- Payments and subscription management (PayPal)
- Authentication (via Django's built-in system + django-allauth)
- Centralised CMS backend (built on Django Admin)

Each module is a Django app inside a single project. Subscription status is the single source of truth for access control across every module.

---

## Technology Stack

### Backend
- **Language:** Python 3.12+
- **Framework:** Django 5.x
- **WSGI server:** Gunicorn
- **Reverse proxy:** Nginx (or Caddy)
- **Background jobs:** Celery with Redis as broker, OR `django-q2` for a simpler single-process setup
- **Forms:** Django Forms + `django-crispy-forms` with a plain-CSS template pack
- **Logging:** Python `logging` with structured output
- **Settings:** `django-environ` for environment-variable driven config
- **Static files:** `whitenoise` for serving CSS/JS/images directly from Django

### Database
- **PostgreSQL 16** on **DigitalOcean Managed Databases**
- Lean on Postgres-native features: `JSONField`, `tstzrange` via `django.contrib.postgres`, exclusion constraints, partial unique indexes, materialised views

### Frontend
- **Server-rendered HTML** via Django templates
- **Plain CSS** with CSS variables (no Tailwind, no preprocessors)
- **HTMX** for partial page updates and snappy interactions
- **`django-htmx`** package for HTMX request detection helpers
- **No JavaScript build step**, no `node_modules`, no bundler
- Optional: **Alpine.js** for small client-side interactions (modals, dropdowns)

### Authentication
- **Django's built-in `django.contrib.auth`** as the foundation
- **`django-allauth`** for email verification, password reset, and signup flows
- Email + password (no social login required for v1)
- Server-side sessions via Django's session framework, stored in Postgres
- CSRF protection via Django's built-in middleware (automatic on all forms)
- Rate limiting on login/signup via `django-axes` or `django-ratelimit`

### Payments
- **PayPal** — Subscriptions API for recurring billing
- Direct integration via `requests` against the PayPal REST API (third-party Django PayPal libraries are thin wrappers and not worth the dependency)
- Webhooks handled by a dedicated Django view with signature verification
- Hosted PayPal checkout (keeps platform out of PCI scope)

### Email
- Transactional email via Postmark or Resend
- `django-anymail` provides a unified backend for both
- Templates rendered with Django's template engine

### File Storage
- **DigitalOcean Spaces** (S3-compatible object storage) for brand assets, offer images, content media
- `django-storages` with the S3 backend (Spaces is API-compatible with S3)
- Signed URLs for premium-only assets

### Hosting & Deployment
- **DigitalOcean App Platform** (simplest) OR **DigitalOcean Droplet** + Nginx + Gunicorn + systemd (more control, cheaper at scale)
- **DigitalOcean Managed PostgreSQL** for the database
- **DigitalOcean Spaces** for object storage
- **DigitalOcean Managed Redis** if using Celery (optional — `django-q2` avoids needing Redis at all)
- All infrastructure stays inside one DigitalOcean account, one bill, one network

### Recommended DigitalOcean Setup for v1

| Component | Service | Approx Monthly Cost |
|-----------|---------|---------------------|
| App | App Platform Basic OR Droplet | $6–12 |
| Database | Managed Postgres (1GB dev tier) | $15 |
| Object Storage | Spaces (250GB included) | $5 |y
| **Total** | | **~$25–50/month** |

### Project Structure

A single Django project with one app per business domain.

```
growth_collective/
├── manage.py
├── requirements.txt
├── .env                          # local only, never committed
├── config/                       # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py                 # if using Celery
├── apps/
│   ├── accounts/                 # custom User model, profile, auth extensions
│   ├── billing/                  # PayPal integration, plans, subscriptions
│   ├── bookings/                 # 1:1 coaching sessions
│   ├── events/                   # webinars + training sessions
│   ├── brand_assets/             # media kit downloads
│   ├── referrals/                # internal + external referral system
│   ├── offers/                   # The Collective Advantage marketplace
│   ├── points/                   # points ledger, ranking calculations
│   ├── content/                  # CMS pages
│   ├── notifications/            # email sending, templates
│   └── core/                     # shared utilities, base templates, middleware
├── templates/                    # project-level templates
│   ├── base.html
│   ├── partials/                 # HTMX fragment templates
│   └── emails/                   # transactional email templates
├── static/
│   └── css/
│       ├── reset.css
│       ├── tokens.css            # CSS variables
│       ├── base.css              # element defaults
│       ├── layout.css            # page shell, grid
│       ├── components.css        # buttons, cards, forms, badges, tables, modals
│       └── utilities.css         # small helpers
└── media/                        # local dev only; production uses Spaces
```

Each app has the standard Django layout: `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `migrations/`, plus a `templates/<app_name>/` directory.

### CSS Approach

- **Plain CSS only** — no Tailwind, no SASS, no PostCSS
- **CSS variables** (`tokens.css`) for all colours, spacing, typography, radii, shadows
- **BEM-ish naming**: `.card`, `.card__title`, `.card--featured`
- **Flexbox and Grid** for layout — no grid framework
- **One breakpoint at 768px** for mobile
- **Reset:** Josh Comeau's CSS Reset
- A `/dev/styleguide` URL renders every component in every state for visual regression checking

### HTMX Conventions

- HTMX loaded once in `base.html` via a single `<script>` tag
- `django-htmx` middleware adds `request.htmx` for detecting HTMX requests
- Views return partial templates instead of full pages when `request.htmx` is true
- Used for: claiming time slots, submitting referrals/offers without page reloads, filtering feeds, loading more results, updating dashboard widgets, monthly prompt completion
- Forms still work without JavaScript — HTMX is progressive enhancement

### Why Django for This Project

Django was designed for exactly this shape of application: multi-role, content-heavy, form-heavy, with a strong admin requirement. Specific wins:

- **Django Admin** provides ~70% of Module 8 (CMS) for free — no manual building of admin tables, filters, search, bulk actions
- **`django.contrib.auth` + `django-allauth`** provide most of Module 7 (Authentication) for free
- **Django ORM** handles the majority of queries without writing SQL; raw SQL is dropped in only for the tricky Postgres-native features
- **Django Forms** map cleanly to the form-heavy nature of this spec
- **Mature ecosystem** of well-maintained packages for every module's needs
- **Migration system** is automatic from model changes

---

# Module 1: Business Coaching Booking System

Build a web-based booking system for a business coaching service.

## Core Concept

- Users are enrolled in a monthly coaching plan
- Each user can book 1 coaching session per month
- There are a maximum of 3 coaches
- Sessions are conducted via Zoom or Google Meet, with automatic meeting link generation

## User Roles

### Admin
- Manage coaches (add/remove/edit)
- View all bookings
- Override bookings if needed
- View user plan status

### Coach
- Set availability (time slots by day/week)
- Define recurring availability (e.g., every Monday 9–12)
- View upcoming bookings
- Automatically receive meeting links for scheduled sessions

### Client (Coaching Plan Member)
- View available coaches and time slots
- Book 1 session per calendar month
- See upcoming/past sessions
- Receive confirmation + meeting link

## Booking Logic

Each client:
- Can only book 1 session per month
- Cannot double-book or exceed quota

System automatically:
- Resets booking eligibility each month
- Prevents booking if quota is used

Time slots:
- Created by coaches
- Cannot overlap (enforced via Postgres exclusion constraint on `tstzrange`)
- Automatically removed once booked

The "1 session per month" rule is enforced at the database level via a partial unique index on `(user_id, date_trunc('month', booked_at))`, defined in a Django migration as a `RunSQL` operation.

## Django Implementation Notes

- `apps/bookings/models.py`: `Coach`, `AvailabilitySlot`, `Booking`, `MonthlyUsage`
- Use `django.contrib.postgres.fields.DateTimeRangeField` for slot time ranges
- Add a Postgres exclusion constraint via a custom migration
- Booking creation goes through a service function that wraps the DB write in a transaction and validates the monthly quota

## Meeting Integration

Integrate with Zoom API OR Google Calendar + Google Meet (pick one for v1; Google Meet via Calendar API is simpler and free).

When a booking is made:
- Automatically generate a meeting link
- Send confirmation email to both client and coach (via Django's email backend / Anymail)
- Add event to both calendars

## Notifications

Email reminders:
- Immediately after booking
- 24 hours before session

Optional:
- SMS reminders
- In-app notifications

## Automation Rules

- **Monthly reset:** scheduled task (Celery beat or `django-q2` schedule) that runs on the 1st of every month and resets the `MonthlyUsage` counters
- **Cancellation policy:** if user cancels before X hours, slot becomes available again. Optionally allow rebooking within same month

## UI/UX Requirements

Simple dashboard for each role:
- **Clients:** "Book a Session" + calendar view
- **Coaches:** availability scheduler + bookings list

Calendar interface:
- Weekly/monthly view
- Real-time slot updates (HTMX polling)
- Mobile-friendly design

## Data Structure

- `User` (extended Django user with `role`, `subscription_type`, `subscription_status`)
- `Coach` (one-to-one with User)
- `AvailabilitySlot` (coach, time_range, status)
- `Booking` (user, coach, datetime, meeting_link, status)
- `MonthlyUsage` (user, month, sessions_used)

---

# Module 2: Webinars & Formal Training Sessions

Extend the platform to support two distinct event types: Webinars and Formal Training Sessions, with role-based access and automated eligibility.

## Objective

- Support two event categories
- Control access based on subscription level
- Maintain a webinar-style experience (group sessions)
- Keep logic clean and scalable alongside the existing 1:1 coaching booking system

## Event Types

### Webinars (Open Access)
- Available to all registered members
- No restriction based on subscription tier
- Group session format (multiple attendees)
- No booking limit per month
- Users can register/join freely and receive confirmation + meeting link

### Formal Training Sessions (Premium Only)
Only available to users on the Coaching Plan or Business Growth Plan.
- Same format as webinars (group session)
- Restricted access
- Optional cap on attendees
- Users must be authenticated and verified as premium subscribers before booking

## User Access Logic

Each user has a `subscription_type` field: `free`, `coaching`, or `business_growth`.

Access rules:
- **Webinars** → accessible to all users
- **Training Sessions** → accessible only if `subscription_type in ("coaching", "business_growth")` AND `subscription_status` is active

If a non-eligible user tries to register: show upgrade prompt and block booking.

Implemented as a Django decorator `@require_premium` and a `PremiumRequiredMixin` for class-based views.

## Event Management (Admin / Coach)

Extend event creation to include:
- `event_type`: `webinar` or `training_session`
- `access_level` (auto-derived or configurable): `all_members` or `premium_only`

Fields: Title, Description, Date & time, Duration, Host (coach FK), Max attendees (optional), Meeting link.

All event management happens in Django Admin for v1 — list views, filters, inline attendee management all come for free.

## Booking / Registration Flow

### For Webinars
1. User clicks "Register"
2. View confirms registration
3. Sends meeting link
4. Adds to attendee list

### For Training Sessions
1. User clicks "Register"
2. `@require_premium` decorator checks eligibility
3. If valid: confirms registration and sends meeting link
4. If not: redirects to upgrade page

## Notifications

For both event types:
- Confirmation email upon registration
- Reminder email 24 hours before
- Reminder email 1 hour before

Reminders scheduled as Celery tasks at registration time, OR as a single periodic task that scans for upcoming events.

## Data Model

### `Event`
- id
- title
- description
- datetime
- duration
- host (FK to User where role=coach)
- event_type (`webinar` | `training_session`)
- access_level (`all_members` | `premium_only`)
- max_attendees (nullable)
- meeting_link

### `EventAttendee`
- id
- event (FK)
- user (FK)
- status (`registered`, `attended`, `cancelled`)
- `unique_together = ("event", "user")` to prevent duplicate registrations

## Automation & Rules

- Prevent duplicate registrations per user per event (DB constraint)
- Enforce attendee limits in the registration view
- Automatically generate meeting links on event creation (signal on `Event.post_save`)
- Sync with calendar (optional but preferred)

## Frontend Updates

### User Dashboard
- Section: "Upcoming Events"
- Tabs: Webinars / Training Sessions (HTMX swaps the panel)
- Lock icon on premium-only sessions if user is not eligible

### Admin / Coach Dashboard
- Django Admin handles event CRUD
- Custom coach dashboard view for coaches to see only their hosted events

## Optional Enhancements

- Waitlist for full training sessions
- Replay access (premium-only for training sessions)
- Attendance tracking
- Analytics (registrations vs attendance)

## Constraints

- Must integrate cleanly with existing booking system
- Must not interfere with 1:1 coaching session limits
- Keep logic modular and reusable

---

# Module 3: Subscriber Brand Assets / Media Kit

Extend the dashboard to include a "Brand Assets" or "Media Kit" section where subscribed users can access and download the company logo for use in emails, signatures, and marketing materials.

## Objective

Create a secure, subscription-based area where eligible users can:
- View the official Growth Collective logo
- Download it in multiple formats
- Access simple usage guidance

## Access Control

Only users with active subscriptions can access this section: `coaching` or `business_growth`.

```
IF subscription_type in ("coaching", "business_growth") AND subscription_status active
  → grant access
ELSE
  → hide section OR show upgrade prompt
```

Implemented via the `@require_premium` decorator on the brand assets view.

## Frontend (Dashboard UI)

### Logo Preview
- Display primary logo (high resolution)
- Optional variations:
  - Light version (for dark backgrounds)
  - Dark version (for light backgrounds)
  - Icon-only (styled "G")

### Download Options
Provide buttons for:
- PNG (transparent background)
- SVG (vector format)
- JPEG (for simple use)

Each download is a one-click signed URL.

### Quick Use Instructions
- "Use PNG for email signatures"
- "Use SVG for websites and scaling"
- "Do not stretch or alter colours"

## File Storage

- Store logo assets in **DigitalOcean Spaces** via `django-storages`
- Use **signed URLs** with short expiry (e.g. 5 minutes) for downloads
- The view generates signed URLs server-side and only returns them to authorised users

## Backend Logic

- Verify user subscription on every page load (no cached access)
- Only generate signed URLs if user is authorised
- Optionally track download count and last accessed date in a `BrandAssetDownload` model

---

# Module 4: Dual Referral & Reputation System

Extend the platform to include a two-part referral system: member-to-member referrals (internal lead sharing) and new member referrals (external growth). The system incentivises consistent monthly participation using points, rankings, and visibility boosts.

## Objective

Create a gamified ecosystem where:
- Members actively refer business to each other
- Members invite new users to the platform
- Contributions are tracked monthly
- A points + ranking system increases visibility and trust

## System 1: Internal Referrals (Member → Member)

Members submit business opportunities for other members.

### Section Naming

Use a strong, branded name instead of "referrals":
- "Opportunity Exchange"
- "Deal Flow"
- "Growth Exchange"
- **"Member Deal Board"** ← recommended (feels premium + clear)

### Features

#### Submit Referral
Form fields:
- Referral title
- Description
- Industry/type
- Ideal recipient (optional)
- Value estimate (optional)
- Contact method

Built as a standard Django ModelForm.

#### Shared Feed
- All referrals appear in a live feed
- Members can view, claim interest, comment or connect
- Filtering and pagination via HTMX

#### Attribution
Track who submitted the referral and who engaged/claimed it. Optionally mark as "successful" or "converted".

### Points (Internal Referrals)
- **+10 points** → submitting a referral
- **+5 points** → engaging with a referral
- **+20 points** → successful referral (optional/manual approval)

Awarded via a `points.services.award_points(user, action_type)` function called from the referral views.

## System 2: External Referrals (New Member Growth)

Encourage users to invite new members into the platform.

### Personal Referral Link
Each user gets a unique referral URL. Track clicks, signups, and conversions (paid plans).

Implemented as a signed token in the URL, intercepted by a middleware that drops a cookie with the referrer's user ID. On signup, the cookie is read and stored against the new user.

### Invite Flow
Simple UI: "Invite a Member". Enter email OR copy link. Send branded email invite via Anymail.

### Conversion Tracking
When a referred user signs up: attribute to referring member. Bonus if they upgrade to paid (triggered from the billing webhook handler).

### Points (External Referrals)
- **+15 points** → referral signup
- **+50 points** → referral becomes paying member

## Monthly Prompt System (Critical)

Create a recurring monthly nudge system.

**Trigger:** 1st of every month OR user login if not completed.

### Prompt 1 (Internal Referral)
> "Who can you send business to this month?"

CTA: Submit a referral

### Prompt 2 (External Referral)
> "Who do you know that should be in the Growth Collective?"

CTA: Invite a new member

### UX
Show as modal popup OR dashboard card. Track completion in a `MonthlyPromptCompletion` model:
- "Referral submitted this month ✓"
- "Invite sent this month ✓"

## Points + Ranking System

Reward active contributors and increase their visibility.

### Leaderboard
Display top contributors (monthly + all-time).

Categories:
- "Top Connectors" (internal referrals)
- "Top Growth Partners" (new members)

### Ranking Logic
Each user has total points, monthly points, and a rank tier.

Example tiers:
- **Bronze** (0–50)
- **Silver** (51–150)
- **Gold** (151–300)
- **Elite** (300+)

Leaderboard data is calculated via a Postgres materialised view, refreshed on schedule by a background job. Django queries the view via a `managed=False` model.

### Visibility Boost
Higher-ranked users:
- Appear higher in member directory
- Appear higher in suggested connections
- Get "Featured Member" badge

## Data Model Additions

### `Referral` (Internal)
- id
- submitted_by (FK to User)
- title
- description
- status
- claimed_by (FK to User, nullable)

### `ExternalReferral`
- id
- referrer (FK to User)
- referred_email
- signup_status
- conversion_status

### `PointsLedger`
- user (FK)
- action_type
- points
- date

### `UserRanking`
- user (FK, OneToOne)
- total_points
- monthly_points
- tier

## Frontend Sections

### Dashboard Additions
- "Member Deal Board" (referrals feed)
- "Invite & Earn" section
- Monthly prompts widget
- Points + rank display

### Profile Enhancements
Show: rank tier, points, referral stats, badge system (Top Connector, etc.)

## Automation Rules

- Reset monthly progress tracking on the 1st of each month (not total points)
- Prevent spam submissions (limit per day, enforced in view + DB)
- Validate referral quality (optional admin moderation via Django Admin)

## Final Intent

Drive real business between members, encourage consistent monthly engagement, turn top contributors into visible leaders, create a self-reinforcing growth loop.

---

# Module 5: The Collective Advantage (Members-Only Offers)

Extend the platform to include a premium members-only offers marketplace called **"The Collective Advantage."**

This feature is both:
- A private member benefit system inside the dashboard
- A publicly marketed feature on the main website to drive conversions

## Objective

Create a high-value, exclusive marketplace where members can:
- Promote services or products to other members
- Offer exclusive member-only rates, bonuses, or privileges
- Generate internal business and collaboration opportunities

This must be positioned as a **premium membership advantage**, not a discount marketplace.

## Public Website Requirement (Important)

"The Collective Advantage" must be prominently featured on the main public marketing website as a key selling point.

### Public-Facing Positioning

Highlight as a core membership benefit. Market as:
- "Access to an exclusive member business marketplace"
- "Unlock The Collective Advantage"
- "Where members trade value, services, and opportunities"

### Where It Appears Publicly
- Homepage (feature section)
- Pricing page (under membership benefits)
- Sales landing pages
- Onboarding flow

Public messaging should emphasise: exclusivity, business growth opportunities, member-to-member value exchange, high-quality network access.

## Core Concept

Inside the platform, "The Collective Advantage" is a curated marketplace where:
- Members post exclusive offers for other members
- Offers include preferential rates or added value
- Members discover and engage with trusted providers
- Activity feeds into points and ranking systems

## Access Control

Available to: `coaching`, `business_growth`.

Rules:
- All eligible members can view offers
- Only eligible members can create offers
- Ineligible users see upgrade prompt and cannot access or post

## Frontend (Dashboard Integration)

**Section name:** The Collective Advantage

### Featured Offers
Curated/high-performing offers. Prioritise high engagement, high-ranked members, and verified providers.

### Offers Feed
Clean, premium card layout. Each offer includes:
- Business name
- Offer title
- Description
- Member-exclusive benefit (discount, bonus, upgrade, etc.)

CTAs: "View Offer", "Claim Benefit", "Contact Provider".

### Filters
- Industry category
- Newest
- Most popular
- Expiring soon

(Filters use HTMX to update the feed without full page reload.)

## Create Offer Flow

Members can submit offers via Django ModelForm with:
- Offer title
- Description
- Standard price (optional)
- Member-exclusive price or benefit
- Category
- Contact link / booking page
- Expiry date (optional)
- Optional image (uploaded to DigitalOcean Spaces)

## Engagement + Points System Integration

- **+10 points** → posting an offer
- **+5 points** → engaging with an offer
- **+15 points** → successful engagement or conversion (if tracked)

Points feed into the member ranking system, visibility on the platform, and featured placement eligibility.

## Reputation & Visibility

High-performing members appear higher in the offer feed (ordering joins on `UserRanking`), can be featured in "Top Contributors", and gain increased visibility across the platform.

## Monthly Prompt System (Add to Existing Automation)

Recurring monthly prompt:
> "Do you have a member-exclusive offer to share this month in The Collective Advantage?"

CTA: "Post an Offer"

## Data Model

### `Offer`
- id
- user (FK)
- title
- description
- standard_price
- member_benefit
- category
- contact_link
- expiry_date
- status
- image (ImageField → Spaces)

### `OfferEngagement`
- user (FK)
- offer (FK)
- action_type (`view`, `click`, `engage`, `convert`)
- created_at

## Automation Rules

- Auto-expire offers past end date (scheduled task)
- Limit active offers per user to prevent spam (enforced in form `clean()` method)
- Optional moderation/approval workflow via Django Admin
- Track engagement metrics for ranking influence

## Optional Enhancements

- "Offer of the Month" spotlight
- Verified member badge for trusted providers
- Bundled offers between members
- Analytics dashboard for offer performance

## Positioning Rules

Always position The Collective Advantage as: **exclusive, high-value, trusted network access**. Not a discount marketplace.

Avoid language like: cheap, deals site, Groupon-like wording.

## Strategic Intent

Increase membership conversion from the public site, drive internal revenue between members, strengthen community stickiness, and create a self-sustaining value exchange ecosystem.

---

# Module 6: Payments & Subscription Management (PayPal)

Extend the platform to include a full payments and subscription management system that handles billing, plan upgrades/downgrades, failed payments, and the relationship between subscription status and platform access.

This module is the revenue engine. Every access rule already defined in the platform (`subscription_type in ("coaching", "business_growth")`) depends on this system being the source of truth.

## Objective

- Convert free users into paying members
- Manage recurring monthly subscriptions
- Enforce access control based on real-time payment status
- Handle failed payments, cancellations, and plan changes gracefully
- Integrate cleanly with the existing booking, events, offers, and referral systems

## Subscription Plans

Three tiers, matching the existing `subscription_type` field on the User model.

### Free
- R0 / month
- Access to webinars only
- Cannot book coaching sessions
- Cannot access training sessions, brand assets, offers marketplace, or referral rewards

### Coaching Plan
- Monthly recurring fee (set in admin)
- 1 coaching session per month
- Access to training sessions
- Access to brand assets
- Full access to The Collective Advantage
- Full referral system participation

### Business Growth Plan
- Higher monthly recurring fee
- Everything in Coaching Plan
- Priority booking access (optional)
- Featured placement eligibility
- Any additional premium benefits defined by admin

Plan pricing is editable from Django Admin without code changes.

## PayPal Integration

The platform uses **PayPal Subscriptions API** for recurring billing.

### Required PayPal Setup
- PayPal Business account
- REST API credentials (Client ID + Secret) — stored as environment variables
- Two **Product** records in PayPal (Coaching Plan, Business Growth Plan)
- A **Billing Plan** for each product, with monthly billing cycle and ZAR (or chosen) currency
- Webhook endpoint registered with PayPal pointing at `/billing/paypal/webhook/`

### Required Capabilities
- Recurring subscriptions (monthly billing) via PayPal Subscriptions API
- Hosted PayPal checkout (keeps platform out of PCI scope entirely)
- Webhooks for payment events
- Subscription suspend/activate/cancel via API
- Refunds (admin-initiated via PayPal API)
- Currency: default ZAR

### Why PayPal Hosted Checkout
- Platform never touches card data
- PCI compliance is PayPal's problem
- Fewer compliance and security obligations
- Works internationally out of the box

### Implementation Approach

A `paypal_client.py` module wraps PayPal REST API calls using `requests`. Don't reach for third-party Django PayPal libraries — they're thin wrappers and PayPal's API is straightforward enough to call directly.

## Subscription Lifecycle

### 1. Signup & Initial Payment

1. User selects plan on pricing page
2. Django view creates a PayPal Subscription via the API and receives an approval URL
3. User is redirected to PayPal hosted checkout
4. User approves the subscription on PayPal
5. PayPal redirects user back to the platform return URL
6. PayPal sends `BILLING.SUBSCRIPTION.ACTIVATED` webhook
7. On webhook receipt, the platform:
   - Creates `Subscription` record
   - Sets `user.subscription_type` to chosen plan
   - Sets `user.subscription_status` to `active`
   - Grants immediate platform access
   - Sends welcome email + receipt

**Important:** Do not grant access on the return URL alone. Wait for the webhook. The return URL can be spoofed; the webhook is signature-verified and authoritative.

### 2. Recurring Billing

PayPal handles the monthly charge automatically. On each cycle:
- PayPal attempts to charge the user
- On success: PayPal sends `PAYMENT.SALE.COMPLETED` → platform extends subscription period and sends receipt
- On failure: PayPal sends `BILLING.SUBSCRIPTION.PAYMENT.FAILED` → platform triggers failed payment flow

### 3. Failed Payment Handling

This is critical and often overlooked.

When `BILLING.SUBSCRIPTION.PAYMENT.FAILED` is received:
- Set `subscription_status` to `past_due`
- User retains access for a grace period (recommended: 3 days)
- Send email immediately: "Payment failed, please update your PayPal payment method"
- PayPal automatically retries based on its retry schedule

If PayPal sends `BILLING.SUBSCRIPTION.SUSPENDED` (after retries fail):
- Set `subscription_status` to `suspended`
- Restrict access to free-tier features only
- Existing bookings: keep upcoming sessions within 7 days, cancel anything beyond
- Send final notice email with reactivation link

If `BILLING.SUBSCRIPTION.CANCELLED` is received:
- Set `subscription_status` to `cancelled`
- Full downgrade to free tier

### 4. Plan Upgrades

PayPal's Subscriptions API supports plan revision (`/v1/billing/subscriptions/{id}/revise`).

When user upgrades (e.g. Coaching → Business Growth):
- Call PayPal revise endpoint with new plan ID
- PayPal handles proration according to the plan's prorate setting
- Update `subscription_type` instantly on confirmation
- Unlock new features in real time
- Send confirmation + updated receipt

### 5. Plan Downgrades

When user downgrades:
- Schedule the plan change for the end of current billing period (do not revise immediately)
- No immediate charge or refund
- User keeps current-tier access until then
- Send confirmation email
- A scheduled task executes the PayPal revise call on the renewal date

### 6. Cancellation

User cancels subscription:
- Call PayPal `/v1/billing/subscriptions/{id}/cancel`
- Subscription remains active until end of paid period (PayPal honours this)
- Set `subscription_status` to `cancelling`
- On `BILLING.SUBSCRIPTION.CANCELLED` webhook: downgrade to free, set status to `cancelled`
- Allow reactivation with one click before period ends (creates a new subscription)
- Send cancellation confirmation + optional exit survey

## Access Control Rules (Critical)

The platform must check `subscription_status` AND `subscription_type` on every gated action, not just `subscription_type` alone.

A user can only access premium features if:

```
subscription_type in ("coaching", "business_growth")
AND
subscription_status in ("active", "cancelling", "past_due")
```

Suspended and cancelled users are treated as free, regardless of their previous `subscription_type`.

This check is implemented as:
- A Django decorator: `@require_premium`
- A class-based view mixin: `PremiumRequiredMixin`
- A method on User: `user.has_premium_access()`

### Impact on Existing Modules

#### Bookings (1:1 coaching)
If a user has an upcoming session and their subscription becomes `suspended` or `cancelled`, sessions within 7 days are honoured; later sessions are auto-cancelled with email notification to both client and coach. Handled by a webhook handler that queries upcoming bookings and cancels per the rule.

#### Training Sessions
Eligibility checked at registration time AND again 1 hour before the session (via scheduled task). If the user's status changed, they're removed from the attendee list and notified.

#### Brand Assets
Access checked on every page load. No cached access.

#### The Collective Advantage
Existing offers from a now-cancelled user are auto-hidden via a manager filter, not deleted (in case they reactivate).

#### Referral System
Cancelled users keep historical points but cannot earn new ones until reactivated.

## Data Model

### `Plan`
- id
- name (Coaching / Business Growth)
- price_monthly
- currency
- features (JSONField, used for display)
- paypal_plan_id (PayPal billing plan ID)
- is_active

### `Subscription`
- id
- user (FK)
- plan (FK)
- provider (`paypal`)
- provider_subscription_id (PayPal subscription ID)
- status (`active`, `past_due`, `suspended`, `cancelling`, `cancelled`)
- current_period_start
- current_period_end
- cancel_at_period_end (boolean)
- created_at
- updated_at

### `Payment` (Ledger)
- id
- user (FK)
- subscription (FK)
- amount
- currency
- status (`succeeded`, `failed`, `refunded`)
- provider_payment_id (PayPal capture/transaction ID)
- description
- created_at

### `WebhookEvent`
- id
- provider (`paypal`)
- event_type
- event_id (unique — used for idempotency)
- payload (JSONField)
- processed (boolean)
- received_at

## Email Notifications

Required transactional emails:
- Welcome + first receipt
- Monthly receipt on successful renewal
- Payment failed (immediate)
- Suspension notice
- Cancellation confirmation
- Reactivation confirmation
- Plan change confirmation

## Frontend Requirements

### Member Dashboard — Billing Section
- Current plan and price
- Next billing date
- "Manage on PayPal" link (PayPal hosts the payment method UI)
- "Change plan" button (upgrade/downgrade)
- "Cancel subscription" button
- Billing history / downloadable receipts

### Public Pricing Page
- Three plan cards with features
- Clear CTA per plan
- Honest comparison table
- FAQ section addressing cancellation, refunds, plan changes

### Checkout Flow
- Click plan → server creates PayPal subscription → redirect to PayPal hosted checkout → user approves → return URL → wait for webhook → access granted
- Show "confirming your subscription..." spinner on return URL until webhook arrives (HTMX polling against a status endpoint)

## Admin Requirements (Django Admin)

Django Admin handles most of this for free. Custom admin actions and list filters:
- View all subscriptions with filters (status, plan, signup date)
- Manually change a user's plan (with reason logged)
- Manually extend access (e.g. comp a month for a VIP)
- Issue refunds via admin action (calls PayPal API)
- View payment history per user

Custom admin dashboard view for revenue:
- MRR (monthly recurring revenue)
- Active subscribers per plan
- Churn rate
- Failed payment rate
- New signups this month

- Edit plan pricing and features (via Django Admin model editing)
- Pause new signups for a plan if needed (via `is_active` flag)

All admin payment actions logged in Django Admin's `LogEntry` plus a custom audit log.

## Webhook Handling

PayPal sends webhooks for every billing event. The webhook view must:
- **Verify webhook signatures** using PayPal's verification API (security-critical, non-negotiable)
- Log every event to `WebhookEvent`
- Process events idempotently using PayPal's event ID as the unique key
- Acknowledge with HTTP 200 quickly, then process via a background task

### Handle at minimum:
- `BILLING.SUBSCRIPTION.ACTIVATED` → activate subscription, grant access
- `BILLING.SUBSCRIPTION.UPDATED` → sync state
- `BILLING.SUBSCRIPTION.CANCELLED` → downgrade user
- `BILLING.SUBSCRIPTION.SUSPENDED` → suspend access
- `BILLING.SUBSCRIPTION.PAYMENT.FAILED` → trigger failed payment flow
- `PAYMENT.SALE.COMPLETED` → record successful payment, extend period, send receipt
- `PAYMENT.SALE.REFUNDED` → record refund, downgrade if necessary

## Security & Compliance

- **Never store raw card data.** PayPal hosted checkout means we never see it
- **PCI compliance:** Using PayPal hosted checkout keeps the platform fully out of PCI-DSS scope
- **POPIA compliance (South Africa):** Document what billing data is stored, why, and for how long. Provide users a way to request their billing data and account deletion (Django Admin export action)
- **Webhook signature verification** on every incoming PayPal webhook
- **HTTPS only** for all payment-related pages — enforced by `SECURE_SSL_REDIRECT` and Nginx
- PayPal credentials stored as environment variables via `django-environ`
- Use PayPal sandbox environment for all development and testing
- CSRF exemption on the webhook endpoint (it's an external POST, not a user form)

## Testing Requirements

Before launch, test in PayPal sandbox:
- Successful signup and first charge
- Successful monthly renewal (sandbox accelerates billing cycles for testing)
- Failed payment → retry → recovery
- Failed payment → suspension → reactivation
- Upgrade with proration
- Downgrade at period end
- Cancellation and reactivation before period end
- Refund flow
- Webhook replay (idempotency)
- Webhook signature verification (positive and negative)
- Access revocation timing on each gated feature

Use `pytest` + `pytest-django` for tests, with a separate test database.

## Optional Enhancements (Phase 2)

- Annual billing with discount (separate PayPal billing plans)
- Promo codes / coupons
- Free trial period (e.g. 14 days — supported via PayPal trial billing cycles)
- Referral discounts (tie into existing referral system)
- Multi-currency support
- Invoice generation for businesses requiring formal tax invoices

## Constraints & Principles

- Source of truth for access is `subscription_status`, not just `subscription_type`
- Never grant access based on cached or stale data — always check current status
- Never delete a user record on cancellation — only downgrade
- All money movement must be logged immutably in the `Payment` ledger
- Webhooks are authoritative, return URLs are not
- Wrap PayPal calls in a service module so a second provider could be added later if needed

## Strategic Intent

- Make paying as frictionless as possible
- Make cancelling honest and easy
- Recover failed payments automatically wherever possible
- Give admins full visibility into revenue health
- Be the unambiguous source of truth for who can access what

---

# Module 7: Authentication System

Authentication is built on Django's `django.contrib.auth` extended with `django-allauth`. Most of the heavy lifting is provided by these two packages — this module documents the configuration and any custom additions.

## Objective

A secure, self-hosted email + password authentication system that integrates cleanly with the rest of the Django application and supports the role-based access control required by every other module.

## Core Requirements

- Email + password signup
- Email verification (mandatory before premium features)
- Login with session cookies
- Password reset via email
- Logout
- Role-based access control (`Member`, `Coach`, `Admin`, `SuperAdmin`)
- Subscription-based access control (`require_premium`)
- Rate limiting on sensitive endpoints
- CSRF protection on all state-changing forms (automatic in Django)

## Technical Approach

### Foundation
- `django.contrib.auth` provides: User model, sessions, password hashing (PBKDF2 by default), permissions, groups
- `django-allauth` provides: signup flows, email verification, password reset, account management
- Custom User model defined in `apps.accounts.models.User` (extends `AbstractUser`) with extra fields for subscription state and role

### Custom User Model

```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ("member", "Member"),
        ("coach", "Coach"),
        ("admin", "Admin"),
        ("super_admin", "Super Admin"),
    ]
    SUBSCRIPTION_TYPES = [
        ("free", "Free"),
        ("coaching", "Coaching"),
        ("business_growth", "Business Growth"),
    ]
    SUBSCRIPTION_STATUSES = [
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("suspended", "Suspended"),
        ("cancelling", "Cancelling"),
        ("cancelled", "Cancelled"),
        ("none", "None"),
    ]

    email = EmailField(unique=True)
    role = CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    subscription_type = CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default="free")
    subscription_status = CharField(max_length=20, choices=SUBSCRIPTION_STATUSES, default="none")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def has_premium_access(self):
        return (
            self.subscription_type in ("coaching", "business_growth")
            and self.subscription_status in ("active", "cancelling", "past_due")
        )
```

**Important:** Define this custom user model at the very start of the project, before the first migration. Changing it later is painful.

### Password Hashing
- Django's default PBKDF2 hasher is fine
- Optionally upgrade to `argon2` by installing `argon2-cffi` and adding it to `PASSWORD_HASHERS`

### Sessions
- Django's default session framework, backed by Postgres
- Sessions stored via the database backend (`django.contrib.sessions.backends.db`)
- Cookies: `Secure`, `HttpOnly`, `SameSite=Lax`
- Session expiry: 30 days, sliding (`SESSION_SAVE_EVERY_REQUEST = True`)

### Email Verification
- Provided by `django-allauth` with `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`
- Users must verify before accessing premium features (enforced in the `require_premium` check)
- Resend verification flow comes free with allauth

### Password Reset
- Provided by `django-allauth` out of the box
- Single-use tokens with expiry handled automatically
- Email templates customised in `templates/account/email/`

### Rate Limiting
- `django-axes` for login attempt limiting (5 attempts per 15 minutes, lockout per IP+username)
- `django-ratelimit` for signup and password reset endpoints
- Implementation: middleware-based, no custom code required

### CSRF Protection
- Django's `CsrfViewMiddleware` is enabled by default
- All forms automatically include `{% csrf_token %}`
- HTMX requests include the CSRF token via `hx-headers` set in `base.html`

## Permissions & Access Control

### Role-Based
- Use Django Groups for `Coach`, `Admin`, `Super Admin`
- Or check `user.role` directly via decorators
- Custom decorator `@require_role("admin")` and mixin `RoleRequiredMixin`

### Subscription-Based
- Decorator `@require_premium`
- Mixin `PremiumRequiredMixin` for class-based views
- Method `user.has_premium_access()` for template-level checks

### Django Admin Access
- Admin and Super Admin roles map to Django's `is_staff` and `is_superuser` flags
- Coaches do NOT get Django Admin access — they use a custom coach dashboard

## Frontend

Pages required (mostly provided by allauth, customised with our templates):
- `/accounts/signup/` — email + password form
- `/accounts/login/` — email + password form with "forgot password" link
- `/accounts/confirm-email/<key>/` — verification landing page
- `/accounts/password/reset/` — email entry form
- `/accounts/password/reset/key/<key>/` — new password form
- `/accounts/logout/` — POST endpoint
- `/account/` — custom view: change password, change email, view sessions, log out other sessions

All pages are server-rendered Django templates with the same look as the rest of the app (override allauth's templates in `templates/account/`).

## Security Checklist

- PBKDF2 (default) or Argon2 for passwords
- Session cookies: `Secure`, `HttpOnly`, `SameSite=Lax`
- HTTPS enforced in production via `SECURE_SSL_REDIRECT = True`
- HSTS enabled
- CSRF tokens on all forms (automatic)
- Rate limiting on login (django-axes), signup, password reset (django-ratelimit)
- Generic error messages on login (allauth handles this)
- Email verification required for premium features
- Password reset invalidates active sessions for that user
- Audit log entry for: signup, login, logout, password change, email change, role change

---

# Module 8: CMS Backend (Django Admin + Custom Views)

Build the centralised CMS backend system on top of Django Admin, extending it with custom admin views where needed.

This CMS is the single source of truth for all platform activity and data management.

## Why Django Admin

Django Admin provides roughly 70% of what this module needs out of the box:
- List views with filters, search, pagination, ordering
- Create / edit / delete forms generated from models
- Bulk actions
- Permissions and groups
- Audit logging via `LogEntry`
- Inline editing of related models
- Customisable per-model

The remaining 30% (analytics dashboard, gamification controls, content editing, custom workflows) is built as custom Django Admin views and templates, OR as separate admin-only apps mounted under `/admin-tools/`.

## Core Objective

Enable administrators to:
- Manage all platform data without code
- Control scheduling and availability
- Moderate community-generated content
- Monitor engagement, referrals, and revenue-driving activity
- Maintain system automation rules

## CMS User Roles

### Super Admin
- `is_superuser = True`
- Full access to everything
- Can modify system rules, pricing, and permissions

### Admin
- `is_staff = True`, member of "Admin" group
- Manage users, content, events, referrals, offers
- View analytics and activity

### Coach
- `is_staff = False`
- No Django Admin access
- Has a separate coach dashboard at `/coach/` showing only their bookings and availability

### Member
- No CMS access (only platform access)

## CMS Modules

### 1. User & Subscription Management

Provided by Django Admin on the User model with custom ModelAdmin:
- List view with filters: subscription_type, subscription_status, role, signup date
- Search by email, name
- Inline display of subscription, recent bookings, points
- Custom admin actions: suspend user, reactivate, change tier, send password reset
- View user activity history: bookings, referrals, points, engagement (linked from user detail page)

### 2. Scheduling System (Core Module)

#### 1:1 Coaching Sessions
- Django Admin for `Coach`, `AvailabilitySlot`, `Booking`
- Custom calendar view at `/admin-tools/scheduling/` showing all bookings and slots
- Admin actions: cancel booking, reassign coach, force-create booking
- Auto-generate Zoom/Google Meet links on booking creation

#### Group Events
- Django Admin for `Event` with inline `EventAttendee` editing
- Filter by event_type, access_level, host, date
- Bulk actions: cancel event, send reminder to all attendees

### 3. Referral System Management

#### Internal Referrals (Member → Member)
- Django Admin for `Referral`
- Filter by status, submitter, claimer
- Bulk action: mark as featured, mark as successful

#### External Referrals
- Django Admin for `ExternalReferral`
- Filter by signup_status, conversion_status

Admin controls:
- Moderate or remove spam referrals (delete action)
- Adjust points manually via `PointsLedger` admin

### 4. The Collective Advantage (Offers CMS)

- Django Admin for `Offer`
- Filter by status, category, expiry
- Bulk actions: feature offer, expire offer, approve offer
- Inline view of `OfferEngagement` per offer

### 5. Points & Ranking System

- Django Admin for `PointsLedger` and `UserRanking`
- Custom admin view at `/admin-tools/leaderboard/` showing live leaderboard
- Manual points adjustment via PointsLedger create form
- Recalculate rankings action (triggers a job)
- Tier configuration via a settings model or environment variable

### 6. Content Management

For pages like the homepage, pricing page, blog, and onboarding content:

**Option A (recommended for v1):** Use **Wagtail** as a sub-app for content management. Wagtail is a Django CMS built on top of Django that provides rich-text editing, page hierarchies, draft/publish workflows, version history, and a much better content editor than vanilla Django Admin. It runs in the same project, shares the same database and auth, and is the standard answer for "Django + content management."

**Option B (lighter):** Build a simple `ContentPage` model with a JSONField for blocks, edited via Django Admin with a third-party rich-text widget (`django-tinymce` or `django-ckeditor`). Less polished but no extra framework.

For Growth Collective, **Wagtail is probably worth the small extra setup cost** because the spec mentions homepage sections, landing pages, pricing pages, blog/articles, feature descriptions, and onboarding content — that's enough content to justify a real CMS.

### 7. Analytics Dashboard

Custom admin view at `/admin-tools/analytics/` showing:
- Active users
- Monthly bookings
- Referral activity
- Offer engagement
- Revenue / conversion tracking
- Top members by points

Includes graphs, trends over time, filter by month / cohort.

Charts rendered with Chart.js loaded only on the analytics page (one `<script>` tag, no build step).

### 8. Automation Engine

Scheduled tasks run via Celery beat OR `django-q2` schedules:
- Monthly reset of referral prompts
- Monthly reminders for referrals and offers
- Auto-expiry of events and offers
- Auto-ranking recalculation
- Notification triggers (booking confirmations, reminders, engagement alerts)

All schedules defined in code and visible in Django Admin via `django-celery-beat` or `django-q2`'s admin integration.

## Data Model Summary

Django models across all apps:
- `accounts.User` (custom)
- `accounts.UserProfile` (optional)
- `billing.Plan`
- `billing.Subscription`
- `billing.Payment`
- `billing.WebhookEvent`
- `bookings.Coach`
- `bookings.AvailabilitySlot`
- `bookings.Booking`
- `bookings.MonthlyUsage`
- `events.Event`
- `events.EventAttendee`
- `brand_assets.BrandAsset`
- `brand_assets.BrandAssetDownload` (optional)
- `referrals.Referral`
- `referrals.ExternalReferral`
- `referrals.MonthlyPromptCompletion`
- `offers.Offer`
- `offers.OfferEngagement`
- `points.PointsLedger`
- `points.UserRanking`
- `content.ContentPage` (or Wagtail Page subclasses)
- `notifications.NotificationLog`
- `core.AuditLog`

## UI Requirements (Admin Dashboard)

- Django Admin's default UI, lightly customised with a project name and colour
- Custom landing page at `/admin/` showing key metrics
- Sidebar navigation (default Django Admin layout)
- Bulk actions enabled on every relevant model
- Search and filters configured per model

## Technical Expectations

- Uses Django's built-in admin permissions and groups
- Audit logs via Django's `LogEntry` plus a custom `AuditLog` model for actions Django Admin doesn't track natively (e.g. PayPal refunds)
- Same Django project, no separate service
- Admin routes mounted under `/admin/` (Django Admin) and `/admin-tools/` (custom views)

## Key Design Principle

This CMS is the operational control centre for the entire Growth Collective platform, enabling:
- Full lifecycle management of members
- Automated community growth systems
- Centralised control of scheduling and engagement
- Minimal manual overhead once configured

By leaning on Django Admin and Wagtail, the build cost is dramatically lower than a custom-built CMS while providing more functionality.

## Final Outcome

A single CMS that allows the business to run coaching bookings, group events, the referral engine, the member marketplace, content + marketing pages, and the ranking + gamification system — all from one Django project, served by the same Gunicorn process that serves the member-facing site.

---

# Suggested Build Order

The spec is large but the build is sequential. This order minimises rework and gets a working product into testable shape as fast as possible.

1. **Foundation:** Django project setup, custom User model, base settings (dev/prod), DigitalOcean Postgres connection, base.html, plain CSS tokens and reset, HTMX loaded
2. **Authentication (Module 7):** Install and configure `django-allauth`, customise templates, add role/subscription fields to User, write `require_premium` decorator
3. **User dashboard shell:** Logged-in landing page, navigation, account settings
4. **Bookings (Module 1):** Coach availability, slot creation, client booking flow, monthly quota enforcement, Google Meet integration, Django Admin for managing it
5. **Payments (Module 6):** PayPal integration, Plan/Subscription models, webhook handler, access control. **Required before premium features.**
6. **Events (Module 2):** Webinars and training sessions, registration flow, gated by subscription
7. **Brand Assets (Module 3):** Quick win — DigitalOcean Spaces upload, signed URLs, gated download view
8. **Referral system (Module 4):** Internal + external referrals, points ledger, leaderboard materialised view
9. **The Collective Advantage (Module 5):** Offers marketplace, feed, filters
10. **CMS polish (Module 8):** Custom admin views, analytics dashboard, Wagtail integration for content pages
11. **Polish:** Notifications, monthly prompts, automation jobs, styleguide page

Each step ships a working Django project that can be deployed to DigitalOcean App Platform (or a Droplet) and tested before moving on.

---

# Deployment Notes (DigitalOcean)

## Production Setup

### App
- Either DigitalOcean App Platform (simpler, auto-deploys from Git) or a Droplet running Ubuntu 24.04 with Nginx + Gunicorn + systemd
- For a solo build, App Platform is the better starting point — switch to a Droplet later if you need more control or lower cost
- Static files served by `whitenoise` (no separate static file host needed)
- Media files (uploads) served from DigitalOcean Spaces via `django-storages`

### Database
- DigitalOcean Managed PostgreSQL
- Start with the basic dev tier ($15/month, 1GB RAM)
- Daily backups included
- Connect via the connection string in `DATABASE_URL` environment variable
- Use trusted sources / firewall to restrict access to your app only

### Object Storage
- DigitalOcean Spaces bucket (S3-compatible)
- Configure `django-storages` with the S3 backend pointing at the Spaces endpoint
- Use signed URLs for premium-only assets (brand kit), public URLs for offer images

### Background Jobs
- For v1 with `django-q2`: runs as a separate process on the same Droplet/App, no Redis required
- For Celery: add DigitalOcean Managed Redis ($15/month), run a worker process and a beat process

### Email
- Postmark or Resend via `django-anymail`
- Transactional only (no marketing email from this system)
- Configure SPF, DKIM, and DMARC for the sending domain

### Environment Variables (via `django-environ`)
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `SPACES_ACCESS_KEY`, `SPACES_SECRET_KEY`, `SPACES_BUCKET_NAME`, `SPACES_ENDPOINT_URL`
- `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`, `PAYPAL_MODE` (sandbox/live)
- `EMAIL_BACKEND_API_KEY`
- `REDIS_URL` (if using Celery)

### HTTPS
- App Platform provides HTTPS automatically
- On a Droplet: Caddy is the easiest option (auto-configures Let's Encrypt) or Nginx + Certbot

### Monitoring
- DigitalOcean's built-in monitoring for CPU, memory, disk
- Sentry (free tier) for error tracking
- Django's `LOGGING` configured to write structured logs to stdout, captured by App Platform / journald

---

*End of specification.*
