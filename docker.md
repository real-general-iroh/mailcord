# Mailcord

**GitHub Repository**: [github.com/real-general-iroh/mailcord](https://github.com/real-general-iroh/mailcord)

**Mailcord** is a lightweight Python application designed to forward emails from your IMAP inbox to Discord as rich embeds. It integrates seamlessly with services like **Cloudflare Email Routing** and is configurable via environment variables, making it easy to deploy with Docker or Docker Compose.

## Features
- Fetches unseen emails from any IMAP-compatible server (e.g., Gmail).
- Forwards emails as Discord embeds to specific users or a default catch-all user.
- Supports logging with adjustable verbosity (`ERROR`, `WARNING`, `INFO`, `DEBUG`, `VERBOSE`).
- Configurable polling interval for checking new emails.
- Optional integration with **Cloudflare Email Routing** for custom domain support.
- Flexible user mapping to route specific email addresses to Discord IDs.

## Images

![Example Short Email Embed](https://i.postimg.cc/ZRYqyTfZ/image.png "Short Email Embed")

![Example Long Email Embed With Two Parts](https://i.postimg.cc/fLHRc6Fd/image.png "Two Part Email Embed")

## Requirements
- An IMAP-compatible email account (e.g., Gmail).
- A Discord bot token.
- Docker or Docker Compose for deployment.

## Environment Variables
| Variable               | Description                                                               | Required | Default        |
|------------------------|---------------------------------------------------------------------------|----------|----------------|
| `IMAP_SERVER`          | IMAP server address (e.g., `imap.gmail.com`).                            | Yes      |                |
| `IMAP_USER`            | IMAP username/email.                                                     | Yes      |                |
| `IMAP_PASS`            | IMAP password or app-specific password.                                  | Yes      |                |
| `DISCORD_BOT_TOKEN`    | Discord bot token.                                                       | Yes      |                |
| `MAINTAINER_ID`        | Discord user ID for troubleshooting notes.                               | Yes      |                |
| `CATCH_ALL_USER_ID`    | Default Discord user ID for unmatched emails.                            | No       | `MAINTAINER_ID`|
| `USER_MAP_*`           | Maps email addresses to Discord IDs (`USER_MAP_user=email:discord_id`).  | No       |                |
| `LOG_LEVEL`            | Logging verbosity (`ERROR`, `WARNING`, `INFO`, `DEBUG`, `VERBOSE`).      | No       | `INFO`         |
| `POLL_INTERVAL`        | Interval (in seconds) to poll for new emails.                            | No       | `60`           |

### Example `.env` File
```env
IMAP_SERVER=imap.gmail.com
IMAP_USER=bob@gmail.com
IMAP_PASS=your-app-password
DISCORD_BOT_TOKEN=12345678901234567890
MAINTAINER_ID=12345678901234567890
CATCH_ALL_USER_ID=12345678901234567890
USER_MAP_alice=alice@example.com:12345678901234567890
LOG_LEVEL=INFO
POLL_INTERVAL=60
```

## Deployment

### Docker Compose
```yaml
services:
    mailcord:
        restart: unless-stopped
        image: realgeneraliroh/mailcord:latest
        container_name: mailcord
        environment:
            - POLL_INTERVAL=60
            - IMAP_SERVER=imap.gmail.com
            - IMAP_USER=bob@gmail.com
            - IMAP_PASS=your-app-password
            - DISCORD_BOT_TOKEN=12345678901234567890
            - MAINTAINER_ID=12345678901234567890
            - CATCH_ALL_USER_ID=12345678901234567890
            - LOG_LEVEL=INFO
            - USER_MAP_alice=alice@example.com:12345678901234567890
```

Run:
```bash
docker-compose up -d
```

### Direct Docker Run
```bash
docker run -d --env-file .env realgeneraliroh/mailcord:latest
```

## Known Limitations
1. **Email Formatting**: Poorly formatted emails will render poorly in embeds. This is why `MAINTAINER_ID` is required for troubleshooting notes in embeds. 
2. **Polling, Not Push**: Relies on IMAP polling because IMAP doesn't support real-time push notifications.
