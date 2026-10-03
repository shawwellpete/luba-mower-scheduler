# Publication privacy

These files are generic configuration examples, not exports of a running Home Assistant installation.

Do not commit:

- `.storage`, `secrets.yaml`, `.env`, databases, logs, diagnostics or backup files;
- credentials, access tokens, webhook secrets or account identifiers;
- real mower serials, tracker suffixes, HA user IDs or notification-device names;
- home coordinates, map geometry, property screenshots or recorded mowing sessions;
- private hostnames, IP addresses, email addresses or local workspace paths.

Use `mower`, `mower_2` and generic lawn names. Maps should centre on their configured tracker rather than saved household coordinates. Test data must be synthetic. Review every staged file and the commit author's email before pushing; a GitHub noreply address avoids publishing a private email.

The validation script catches common accidental exports and unexpected entity names. It complements a review of the exact diff; it cannot prove the absence of all sensitive data. The existing public project/author links in the README are intentional.
