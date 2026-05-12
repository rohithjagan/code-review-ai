# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, **please do not open a public issue**.  
Instead, send a detailed report to [your-email@example.com] **privately**.

We will acknowledge your email within 48 hours, and will send a more detailed response within 5 working days indicating the next steps in handling your report.

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | ✅ Yes            |
| < 1.0   | ❌ No             |

## Security Measures

- All GitHub webhook payloads are verified using HMAC-SHA256.
- Authentication to GitHub API uses short-lived installation tokens.
- Private keys are stored as environment secrets / secret files, never committed.
- The app does not store raw source code persistently.
- Dependencies are pinned for reproducible builds.

## Past Vulnerabilities

None reported yet.