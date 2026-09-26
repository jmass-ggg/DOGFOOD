---
name: dogfood-frontend
description: Build or refine DogFood participant, organizer, admin, judge, results, and project-gallery UI with clear hackathon workflows and polished product UX. Use for frontend pages, components, forms, dashboards, responsive design, and UX improvements.
---

# DogFood Frontend

Follow the repository's existing frontend stack and design system.

Do not replace a working frontend framework just to match a preference.

If starting from scratch, a practical default is:

- React
- TypeScript
- Tailwind CSS

## Product Style

Aim for a polished modern hackathon/SaaS product.

Avoid:

- excessive gradients
- excessive glassmorphism
- random decorative cards
- giant empty hero sections
- fake AI-looking visual clutter
- inconsistent spacing
- excessive animations

Prefer:

- strong hierarchy
- clear typography
- useful whitespace
- intentional color
- excellent forms
- clear status indicators
- restrained motion
- accessible controls

## Primary Flows

Optimize these first:

Participant:
Hackathon → Join → Team → Submit → Confirmation

Team Leader:
Dashboard → Team → Project → Edit/Submit

Judge:
Assigned Projects → Project → Rubric → Submit Score

Organizer:
Dashboard → Setup → Participants → Judges → Judging → Results

Public:
Hackathon → Results → Project Gallery

## Forms

For submission/team/settings forms:

- show required fields
- validate inline
- preserve useful entered state where possible
- show server errors clearly
- disable duplicate submission actions while pending
- provide explicit success state

Do not depend only on client validation.

## Judge UI

Judge interface must be blind.

Never display:

- team name
- participant names
- participant avatars
- emails
- social profiles

Do not fetch these fields into judge-facing state.

Judge workspace should emphasize:

- project content
- media/demo
- criterion rubric
- score controls
- comments
- completion state

## Organizer/Admin UI

Clearly separate:

Organizer-only configuration

from:

Admin operational tools.

Do not show actions the current role cannot perform unless the product
intentionally shows a disabled explanatory state.

## State Quality

Every important page should handle:

- loading
- empty
- error
- success
- unauthorized
- deadline closed

## Responsive Quality

Check at minimum:

- desktop
- tablet-ish width
- mobile

Do not let tables become unusable on mobile; use responsive cards or
horizontal overflow intentionally.

## Accessibility

Use semantic controls, labels, keyboard access, visible focus states, and
reasonable contrast.
