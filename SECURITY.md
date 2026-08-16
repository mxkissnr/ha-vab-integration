# Security Policy

## Supported Versions

Only the **latest release** receives security fixes. Please update before reporting.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please open a **[private security advisory](https://github.com/mxkissnr/ha-vab-integration/security/advisories/new)** on GitHub and include:

- A clear description of the vulnerability
- Steps to reproduce
- Potential impact

I will acknowledge your report within **7 days** and aim to release a fix within **30 days** depending on severity.

## Scope

This integration runs locally on your Home Assistant instance and communicates only with
one external public API (no authentication required):

- `bahnland-bayern.de/efa/` — EFA departure monitor

No credentials or personal data are stored. The primary attack surface is the JSON parsing of API responses.

Out of scope: vulnerabilities in Home Assistant itself or the upstream APIs.
