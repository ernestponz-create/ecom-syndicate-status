# The Ecom Syndicate status page

Public status page: https://ernestponz-create.github.io/ecom-syndicate-status/

Free uptime checks on GitHub Actions about every 15 minutes (`monitors.json`, `scripts/check.py`).
When a service fails two checks in a row, an issue labelled `status` opens; it closes itself when the service recovers.
Private addresses and keys are stored as repository secrets only; this repo contains no secrets.
