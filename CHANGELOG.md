# Changelog

## 2.1.0 — 2026-10-03

- Confirm mower activity before recording a start or advancing the weekly schedule.
- Serialize task dispatch and keep hourly retries on blocked or unconfirmed starts.
- Recover stale next-times after downtime and preserve future manual choices.
- Separate manual blocks from rain/night restrictions; handle missing rain data explicitly.
- Detect missing task entities while idle and attempt one schedule synchronization.
- Add persistent rolling session history, case-insensitive lawn summaries and last-lawn sensors.
- Add optional single- and two-mower dashboards with a larger history launcher and popup details.
- Match activity-card heights and disable misleading GPS-history joins.
- Document the Luba 3 coverage limitation; this update does not claim a coverage-data fix.
- Publish only generic examples, with automated checks and no installation snapshots.

## June 2026 rewrite — 2026-06-02

- Replaced area-based start commands with saved-task buttons.
- Published a generic single-mower, three-lawn example and built-in-card dashboard.
- Latest commit before 2.1.0: `e7a3a09`.

The older `v1.1` tag predates the June rewrite.
