# Contributing

Thanks for helping improve NovelForge.

## Development Rules

- Keep runtime text language-neutral or backed by locale files.
- Keep DB-editable data translated when needed, but keep code logic based on stable keys.
- Run relevant validation before handoff.

## Validation

- Backend syntax: `python -m compileall -q backend/app`
- Frontend types: `npm --prefix frontend run typecheck`
