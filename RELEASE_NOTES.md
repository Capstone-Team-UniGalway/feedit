# Email Configuration with MailerSend Integration

## Overview
This release implements MailerSend SMTP integration for the Feedit application, providing reliable email delivery for both development and production environments.

## Features
- **Dual Email Backend Configuration**: 
  - Console backend for development (emails displayed in terminal)
  - SMTP backend for production (emails sent via MailerSend)
- **Environment-based Configuration**: Email settings automatically switch based on the `DJANGO_ENV` environment variable
- **Secure Credential Management**: SMTP credentials stored in environment variables
- **Improved Email Templates**: Updated site information for better email content

## Technical Details

### Email Backend Configuration
- Added MailerSend SMTP settings to Django configuration
- Set up environment variable support for all email settings
- Configured default sender email as `noreply@feedit.online`

### Environment Variables
Added the following environment variables:
- `EMAIL_HOST`: SMTP server hostname (default: smtp.mailersend.net)
- `EMAIL_PORT`: SMTP server port (default: 587)
- `EMAIL_USE_TLS`: Whether to use TLS (default: True)
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password
- `DEFAULT_FROM_EMAIL`: Default sender email address

### Django Sites Framework
- Updated site information for better email templates
- Set site name to "Feedit" and domain to match deployment environment

## Testing
- Verified email sending in development mode (console backend)
- Verified email sending in production mode (SMTP backend)
- Tested password reset functionality
- Tested email verification functionality

## Usage
- In development: Emails are displayed in the console
- In production: Emails are sent via MailerSend SMTP

## Configuration
To switch between environments:
- Development: Set `DJANGO_ENV=development` in .env
- Production: Set `DJANGO_ENV=production` in .env or as an environment variable
