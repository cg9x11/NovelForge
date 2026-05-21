---
description: NovelForge engineering rules for elegant architecture, low coupling, and maintainability
globs:
  - "backend/**/*.py"
  - "frontend/src/renderer/src/**/*.{ts,vue}"
  - "docs/**/*.md"
alwaysApply: true
---

# NovelForge Engineering Rule

## 0) Goal

All development should prioritize long-term maintainability:

1. Low coupling with clear module boundaries.
2. High cohesion with single responsibility.
3. Verifiable changes with validation loops.
4. Evolvable design without one-off hardcoding.

Do not introduce hardcoded or implicit behavior only to make something work quickly.

## 1) Architecture And Decoupling

### 1.1 Prefer Event-Driven Integration

- Cross-domain behavior, such as triggering workflows after saving cards, should use publish/subscribe events first.
- Do not chain downstream modules directly from business entry points when an event boundary is appropriate.

### 1.2 Prefer Plugin Registration

- Extensible capabilities, including initializers, workflow nodes, and event handlers, must register through decorators.
- New capabilities need two steps: define with the decorator, then import from the relevant `__init__.py` so registration runs.

### 1.3 Centralize Configuration

- Mutable parameters must live in the configuration system: environment variables plus config objects.
- Do not hardcode URLs, switches, thresholds, model names, timeouts, or retry counts in business code.

## 2) Service And API Rules

### 2.1 Single Responsibility

- One service should own one domain.
- Split complex behavior into small services plus an orchestration layer. Avoid god services.

### 2.2 Dependency Injection

- Inject `Session`, config, and dependency objects through parameters.
- Do not create and retain hidden global dependency instances inside functions.

### 2.3 Single API Contract Source

- Backend schemas are the single source of truth for API types.
- Frontend types should come from OpenAPI generation via `npm run gen:types`.
- Do not keep handwritten duplicate API types long term.
- API endpoints must declare clear response models so contracts can be generated.

## 3) Workflow Rules

### 3.1 Verified Code Change Loop

Workflow code changes must follow this loop:

1. Generate code or patch.
2. Parse.
3. Validate.
4. Apply only after validation passes.

Do not skip validation before persisting workflow code.

### 3.2 Visual Editing Safety

- Visual editors must preserve raw schema and unknown fields unless intentionally removed.
- UI helpers should not rewrite workflow semantics without parser and validator coverage.

## 4) Frontend Rules

- User-visible text belongs in locale files unless it is dynamic data from DB or user content.
- Keep legacy DB value compatibility through stable keys and mapping helpers.
- Avoid adding new language-specific hardcoded labels in components.

## 5) Backend Rules

- Seed data should use stable keys and locale-backed display names where practical.
- DB-editable content may be Vietnamese data, but code logic must not depend on translated display text.
- Migrations must preserve existing data and support legacy aliases when display values changed.

## 6) Validation

Before handoff, run the narrowest useful checks first, then broader checks when ready:

- Backend syntax: `python -m compileall -q backend/app`
- Frontend types: `npm --prefix frontend run typecheck`
- Script syntax where changed: `node --check <script>`
