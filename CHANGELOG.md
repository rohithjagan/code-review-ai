# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-05-12

### Added
- GitHub webhook listener with payload signature verification
- AI code review using Google Gemini (security, architecture, performance, maintainability, bug)
- Automatic posting of inline review comments on pull requests
- SQLite database to store review history
- Live dashboard with category/severity charts, trend line, and recent reviews table
- Background threading for non-blocking webhook processing
- Deployment configuration for Render (Procfile, Gunicorn)
- Project documentation (README, LICENSE, Contribution guidelines)

### Known Issues
- No support for large monorepos (files truncated at 5000 chars for AI context)
- Cold start delay (~30-50s) on Render's free tier
- No cross-file dependency analysis yet