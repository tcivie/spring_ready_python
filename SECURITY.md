# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

As this is a new project, only the latest 0.1.x release receives security updates.

## Reporting a Vulnerability

**Please do NOT open a public issue for security vulnerabilities.**

### How to Report

1. **Email**: Send details to the maintainer (check package metadata for contact)
2. **GitHub Security Advisory**: Use the "Security" tab → "Report a vulnerability"

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Affected versions
- Suggested fix (if you have one)

### What to Expect

- **Initial Response**: Within 7 days
- **Status Update**: Every 14 days until resolved
- **Fix Timeline**: Best effort, no guaranteed SLA
- **Credit**: You'll be credited in release notes (if desired)

### Important Notes

This is a small open-source project maintained by volunteers. Security issues will be addressed as quickly as possible, but response times may vary.

If you need an immediate fix, consider:
- Forking and applying your own patch
- Contributing a PR with the security fix
- Using dependency pinning to avoid affected versions

## Security Best Practices

When using spring-ready-python:

1. **Never hardcode credentials** - Use environment variables
2. **Use HTTPS for Eureka/Config Server** - Avoid plain HTTP in production
3. **Secure your Config Server** - Enable authentication
4. **Keep dependencies updated** - Run `pip list --outdated` regularly
5. **Review actuator endpoints** - Ensure they're not publicly exposed without authentication
6. **Use secrets management** - Kubernetes Secrets, AWS Secrets Manager, etc.

## Known Security Considerations

- **Actuator endpoints expose application info** - Secure them in production
- **Config Server credentials stored in environment** - Use proper secrets management
- **Eureka registration sends metadata** - Don't include sensitive data in metadata
- **Heartbeat thread runs in background** - Ensure proper shutdown handling

## Dependencies

This library has minimal dependencies:
- `fastapi` - Web framework (security is your responsibility)
- `requests` - HTTP client (ensure you're using latest version)

Optional dependencies:
- `spring-config-client-python` - Config Server client
- `prometheus-client` - Metrics client

Keep all dependencies updated to receive security patches.
