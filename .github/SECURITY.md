# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Security Model

**Important**: This integration relies primarily on **Home Assistant's security model**. Camera Snapshot Processor is a lightweight image processing layer that:

- Does not store credentials (Home Assistant does)
- Does not handle authentication (Home Assistant does)
- Does not expose additional network endpoints
- Simply processes images from cameras already configured in Home Assistant

The main security is provided by Home Assistant itself. This integration is as secure as your Home Assistant installation.

## Reporting a Vulnerability

This is an open source hobby project maintained in spare time. If you find a security issue:

1. **For critical issues**: Use [GitHub Security Advisory](https://github.com/Patras3/camera-snapshot-processor/security/advisories/new)
2. **For non-critical issues**: Regular [GitHub Issues](https://github.com/Patras3/camera-snapshot-processor/issues) are fine

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### Response Timeline

This is a hobby project, so:
- **Response**: Best effort, when time allows
- **Fixes**: Will be included in next scheduled release
- **Critical CVEs**: May warrant immediate patch release if severe

We use automated tools (pip-audit, CodeQL, Dependabot) to catch known vulnerabilities, but fixes are released on a regular schedule rather than emergency basis (unless critical).

## Automated Security Scanning

While this is a hobby project, we still care about security:

- **pip-audit**: Daily scans for known CVEs in dependencies
- **CodeQL**: Automated code analysis
- **Dependabot**: Automatic PR for dependency updates

These tools catch issues automatically, but fixes are released on a normal schedule.

## Security Through Design

### Minimal Attack Surface

- **Only one dependency**: Pillow (Python Imaging Library)
- No network listeners, no external services
- No custom authentication or credential storage
- Runs entirely within Home Assistant's security context

### Home Assistant Integration

This integration inherits Home Assistant's security:
- **Authentication**: Handled by Home Assistant
- **Credential Storage**: Home Assistant's encrypted database
- **Template Execution**: Home Assistant's sandboxed template engine
- **Network Security**: Home Assistant's web server and SSL

### What We Do

- ✅ Redact credentials from debug logs
- ✅ Validate user inputs
- ✅ Use minimal dependencies
- ✅ Automated CVE scanning

### What Home Assistant Does

- 🔐 User authentication
- 🔐 Credential encryption
- 🔐 Template sandboxing
- 🔐 HTTPS/SSL
- 🔐 Access control

## Best Practices for Users

**Most important**: Keep Home Assistant updated!

Other tips:
- Use strong camera passwords
- Enable HTTPS on Home Assistant
- Don't share RTSP URLs publicly
- Review templates before adding them

## Known Design Choices

- **Stream URLs forwarded as-is**: Required for streaming to work
- **Credentials in logs**: Automatically sanitized (shown as `***:***@`)
- **Minimal validation**: Relies on Home Assistant's validation
- **No caching**: Always fresh images, no stale data

## Contact

Found a bug or have a security concern?
- [GitHub Issues](https://github.com/Patras3/camera-snapshot-processor/issues)
- [GitHub Discussions](https://github.com/Patras3/camera-snapshot-processor/discussions)

Remember: This is a hobby project maintained in spare time. Be patient and kind! 😊
