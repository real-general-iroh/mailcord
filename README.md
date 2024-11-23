# Mailcord

**Mailcord** is a GPLv3-licensed Python application that bridges your IMAP email inbox with Discord, forwarding emails as rich embeds to Discord users. It is configurable, lightweight, and designed for ease of deployment with Docker or Docker Compose.

## Features
- Fetches unseen emails from any IMAP-compatible server (e.g., Gmail).
- Forwards emails to Discord users as rich embeds.
- Supports detailed logging with adjustable verbosity levels.
- Configurable polling interval for checking new emails.
- Integrates seamlessly with email routing services (e.g., Cloudflare Email Routing).
- Supports optional user mapping to route emails from specific addresses or domains to Discord users.

## Images

![Example Short Email Embed](https://i.postimg.cc/ZRYqyTfZ/image.png "Short Email Embed")

![Example Long Email Embed With Two Parts](https://i.postimg.cc/fLHRc6Fd/image.png "Two Part Email Embed")

## Known Limitations
1. **Garbage In, Garbage Out**: If an email is poorly formatted or just plain horrible, it will look equally terrible in the Discord embed. This is why the `MAINTAINER_ID` is required—to include a note pointing users to someone who can fix or interpret the mess.

   Example:
   - `Note: Contact <@123456789012345678> if this message is unreadable.`

   The maintainer becomes the lifeline for users confused by ugly email embeds.

2. **No Magic Fix for Content**: While Mailcord attempts to process HTML and plain-text emails into clean Markdown, exceptionally messy emails (e.g., those with excessive inline styles or malformed HTML) might still render awkwardly.

3. **Polling Only**: Mailcord relies on IMAP polling because IMAP doesn’t support true push notifications. Blame the protocol, not me! While the polling interval can be adjusted to mitigate delays, IMAP just isn’t built for real-time email updates.

## Integration with Cloudflare Email Routing
Mailcord works seamlessly with **Cloudflare Email Routing** (or similar services), which allows you to use custom email addresses (e.g., `you@yourdomain.com`) and route them to your Gmail or IMAP inbox. This setup is perfect if you want to forward emails from your custom domain to specific Discord users.

### Example Setup
1. **Configure Email Routing**:
   - Set up Cloudflare Email Routing to forward `@yourdomain` emails to your Gmail or other IMAP inbox.
   - For example:
     - `alice@yourdomain.com` → `your-email@gmail.com`
     - `support@yourdomain.com` → `your-email@gmail.com`

2. **Define `USER_MAP`**:
   - Use `USER_MAP` environment variables to specify which email addresses route to specific Discord users:
     ```env
     USER_MAP_alice=alice@yourdomain.com:123456789012345678
     USER_MAP_support=support@yourdomain.com:987654321098765432
     ```
   - Any email not explicitly mapped will be sent to the `CATCH_ALL_USER_ID`.

3. **CATCH_ALL Behavior**:
   - If no `USER_MAP` is specified for an email, the message is forwarded to the `CATCH_ALL_USER_ID` (defaulting to `MAINTAINER_ID` if not set).

## Environment Variables
Set the following environment variables to configure Mailcord:

| Variable               | Description                                                                       | Required | Default |
|------------------------|-----------------------------------------------------------------------------------|----------|---------|
| `IMAP_SERVER`          | IMAP server address (e.g., `imap.gmail.com`).                                     | Yes      |         |
| `IMAP_USER`            | Your IMAP account username/email address.                                         | Yes      |         |
| `IMAP_PASS`            | Your IMAP account password or app-specific password.                              | Yes      |         |
| `DISCORD_BOT_TOKEN`    | Token for your Discord bot.                                                       | Yes      |         |
| `MAINTAINER_ID`        | Discord user ID of the maintainer for troubleshooting notes.                      | Yes      |         |
| `CATCH_ALL_USER_ID`    | Default Discord user ID for unmatched emails.                                     | No       | `MAINTAINER_ID` |
| `USER_MAP_*`           | Maps email addresses to Discord user IDs (`USER_MAP_user=<email>:<discord_id>`).  | No       |         |
| `LOG_LEVEL`            | Logging verbosity (`ERROR`, `WARNING`, `INFO`, `DEBUG`, `VERBOSE`).               | No       | `INFO`  |
| `POLL_INTERVAL`        | Interval in seconds to check for new emails.                                      | No       | `60`    |

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

## Usage
### Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables (e.g., using `.env`).
3. Run the application:
   ```bash
   python main.py
   ```

### Running with Docker
1. Build the Docker image:
   ```bash
   docker build -t mailcord .
   ```
2. Run the container:
   ```bash
   docker run -d --env-file .env mailcord
   ```

### Running with Docker Compose
Create a `docker-compose.yml` file:
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

Run the service:
```bash
docker-compose up -d
```

### Running from Docker Hub
Pull the image directly from Docker Hub and run it:
```bash
docker pull realgeneraliroh/mailcord:latest
docker run -d --env-file .env realgeneraliroh/mailcord
```

## Development
### Logging Levels
Control the verbosity of logs with the `LOG_LEVEL` environment variable. Supported levels:
- `ERROR`: Logs critical errors only.
- `WARNING`: Logs warnings and errors.
- `INFO`: Logs general application activity (default).
- `DEBUG`: Logs detailed internal operations.
- `VERBOSE`: Logs everything, including fine-grained details for debugging.

### Debugging
Set `LOG_LEVEL=DEBUG` or `VERBOSE` in your `.env` file to enable more detailed logging during development or troubleshooting.

## License
Mailcord is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file for details.