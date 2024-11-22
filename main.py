import time
import imaplib
import email
import re
import os
import requests
import html2text
import email.utils
from datetime import datetime, timezone, timedelta
from email.header import decode_header
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MAINTAINER_ID = os.getenv("MAINTAINER_ID")
CATCH_ALL_USER_ID = os.getenv("CATCH_ALL_USER_ID", MAINTAINER_ID)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))

USER_MAP = {}

for key, value in os.environ.items():
    if key.startswith("USER_MAP_"):
        email_address, discord_user_id = value.split(":")
        USER_MAP[email_address] = discord_user_id

missing_vars = []

if not IMAP_SERVER:
    missing_vars.append("IMAP_SERVER")
if not IMAP_USER:
    missing_vars.append("IMAP_USER")
if not IMAP_PASS:
    missing_vars.append("IMAP_PASS")
if not DISCORD_BOT_TOKEN:
    missing_vars.append("DISCORD_BOT_TOKEN")
if not MAINTAINER_ID:
    missing_vars.append("MAINTAINER_ID")

if missing_vars:
    raise ValueError(
        f"The following environment variables are required but missing: {', '.join(missing_vars)}"
    )


def log_message(level, message):
    levels = ["ERROR", "WARNING", "INFO", "DEBUG", "VERBOSE"]
    if levels.index(LOG_LEVEL.upper()) >= level:
        print(f"[{levels[level]}] {message}")


def log_error(message):
    log_message(0, message)


def log_warning(message):
    log_message(1, message)


def log_info(message):
    log_message(2, message)


def log_debug(message):
    log_message(3, message)


def log_verbose(message):
    log_message(4, message)


def send_discord_message(user_id, embed):
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    channel_response = requests.post(
        "https://discordapp.com/api/users/@me/channels",
        headers=headers,
        json={"recipient_id": user_id},
    )

    if channel_response.status_code != 200:
        log_error(f"Failed to create DM channel: {channel_response.text}")
        return False

    log_verbose(f"Created DM channel with {user_id}: {channel_response.json()}")
    log_debug(f"Created DM channel with {user_id}")

    channel_id = channel_response.json()["id"]

    message_response = requests.post(
        f"https://discordapp.com/api/channels/{channel_id}/messages",
        headers=headers,
        json={"embeds": [embed]},
    )

    if message_response.status_code != 200:
        log_error(f"Failed to send message: {message_response.text}")
        return False

    log_verbose(f"Sent message to {user_id}")
    log_verbose(f"Response from Discord:\n{message_response.json()}")
    log_debug(f"Sent message to {user_id}")

    return True


def create_discord_embed(subject, from_address, to_address, body, time):
    log_verbose(f"Creating embed for {to_address} with subject: {subject}")
    log_verbose(f"Subject: {subject}")
    log_verbose(f"From: {from_address}")
    log_verbose(f"To: {to_address}")
    log_verbose(f"Time: {time}")
    log_verbose(f"Body:\n{body}")
    log_debug(f"Creating embed for {to_address} with subject: {subject}")
    body_parts = {}
    multi_embed = False
    while len(body) > 4090:
        linebreak_index = body.rfind("\n", 0, 4090)
        if linebreak_index == -1:
            linebreak_index = body.rfind(" ", 0, 4090)
        body_parts[len(body_parts)] = body[:linebreak_index]
        body = body[linebreak_index + 1 :]
        multi_embed = True
        log_verbose(f"Splitting body into {len(body_parts)} part(s) for {to_address}")
    body_parts[len(body_parts)] = body
    log_verbose(f"Total parts: {len(body_parts)}")

    if multi_embed:
        embeds = []
        for i in body_parts:
            embed = {
                "title": f"(Part {i+1}/{len(body_parts)}) | {subject}",
                "color": 0x800000,
                "fields": [
                    {"name": "From", "value": from_address, "inline": True},
                    {"name": "To", "value": to_address, "inline": True},
                    {
                        "name": "Part",
                        "value": f"{i+1}/{len(body_parts)}",
                        "inline": True,
                    },
                    {
                        "name": "Note",
                        "value": f"Contact <@{MAINTAINER_ID}> if this message is unreadable.",
                        "inline": False,
                    },
                ],
                "description": body_parts[i],
                "footer": {"text": f"Email received at {time}"},
            }
            embeds.append(embed)
            log_verbose(
                f"Created embed part {i+1}/{len(body_parts)} for {to_address}:\n{embed}"
            )
        log_debug(f"Created {len(body_parts)} embeds for {to_address}")
        return embeds
    else:
        embed = {
            "title": subject,
            "color": 0x800000,
            "fields": [
                {"name": "From", "value": from_address, "inline": True},
                {"name": "To", "value": to_address, "inline": True},
                {
                    "name": "Note",
                    "value": f"Contact <@{MAINTAINER_ID}> if this message is unreadable.",
                    "inline": False,
                },
            ],
            "description": body,
            "footer": {"text": f"Email received at {time}"},
        }
        log_verbose(f"Created embed for {to_address}:\n{embed}")
        log_debug(f"Created embed for {to_address}")
        return embed


def decode_email_subject(subject):
    decoded_subject, encoding = decode_header(subject)[0]
    if isinstance(decoded_subject, bytes):
        byte_subject = decoded_subject.decode(encoding or "utf-8")
        log_verbose(f"Decoded subject: {byte_subject}")
        return byte_subject
    log_verbose(f"Decoded subject: {decoded_subject}")
    return decoded_subject


def check_for_naked_links(text_content):
    # First, save all existing markdown links
    markdown_links = {}
    markdown_pattern = r"\[([^\]]*)\]\(([^\)]+)\)"

    def save_markdown_link(match):
        placeholder = f"__MARKDOWN_LINK_{len(markdown_links)}__"
        markdown_links[placeholder] = match.group(0)
        log_verbose(f"Saved markdown link: {match.group(0)}")
        return placeholder

    # Replace all markdown links with placeholders
    text = re.sub(markdown_pattern, save_markdown_link, text_content)
    log_verbose(f"Saved {len(markdown_links)} markdown links:\n{markdown_links}")

    # Now process naked links
    def format_naked_link(m):
        url = m.group(0)
        domain = urlparse(url).netloc
        domain = re.sub(r"^www\.", "", domain)
        log_verbose(f"Found naked link: {url}")
        return f"( [Link to: {domain}]({url}) )"

    # Simple pattern to match URLs not in markdown format
    url_pattern = r"https?://[^\s)]+(?=[\s)]|$)"
    text = re.sub(url_pattern, format_naked_link, text)
    log_verbose(f"Replaced naked links with markdown:\n{text}")

    # Restore markdown links
    for placeholder, original in markdown_links.items():
        text = text.replace(placeholder, original)

    log_verbose(f"Restored {len(markdown_links)} markdown links:\n{text}")
    return text


def text_to_markdown_with_links(text_content):
    def repl(m):
        url = m.group(1)
        # Extract domain from URL
        domain = urlparse(url).netloc
        # Remove www. if present
        domain = re.sub(r"^www\.", "", domain)
        log_verbose(f"Found naked link: {url}")
        return f"( [Link to: {domain}]({url}) )"

    # Pattern matches: opening parenthesis, URL, single space, closing parenthesis
    pattern = r"\((https?://[^\s]+)\s\)"
    text = re.sub(pattern, repl, text_content)

    log_verbose(f"Replaced naked links with markdown:\n{text}")
    return text


def html_to_text_with_links(html_content):
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_tables = True
    h.wrap_links = False

    markdown = h.handle(html_content)

    def repl(m):
        url = m.group(1)
        # Extract domain from URL
        domain = urlparse(url).netloc
        # Remove www. if present
        domain = re.sub(r"^www\.", "", domain)
        log_verbose(f"Found naked link: {url}")
        return f"( [Link to: {domain}]({url}) )"

    # Pattern matches: opening bracket, closing bracket, open prrenthesis, URL, closing parenthesis
    pattern = r"\[\]\((https?://[^\)]+)\)"

    markdown = re.sub(pattern, repl, markdown)
    log_verbose(f"Replaced naked links with markdown:\n{markdown}")

    return markdown


def check_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(IMAP_USER, IMAP_PASS)
    mail.select("inbox")
    log_verbose(f"Connected to {IMAP_SERVER} as {IMAP_USER}")

    log_debug("Checking for unread emails...")
    _, search_data = mail.search(None, "UNSEEN")
    for num in search_data[0].split():
        _, data = mail.fetch(num, "(RFC822)")
        _, bytes_data = data[0]

        email_message = email.message_from_bytes(bytes_data)
        subject = decode_email_subject(email_message["subject"])
        from_addr = email.utils.parseaddr(email_message["from"])[1]
        to_addr = email.utils.parseaddr(email_message["to"])[1]
        received_time = email.utils.parsedate_tz(email_message["Date"])
        dt = datetime(
            *received_time[:6],
            tzinfo=timezone(timedelta(seconds=received_time[9] or 0)),
        )
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S %Z")

        log_debug(
            f"Processing email from {from_addr} to {to_addr} with subject: {subject}"
        )
        log_debug(f"Received at: {formatted_time}")
        log_info(f"Processing email with subject: {subject}")

        body = ""
        if email_message.is_multipart():
            log_verbose(
                f"Email from {from_addr} to {to_addr} with subject: {subject} is multipart"
            )
            log_debug(f"Email parts: {len(email_message.get_payload())}")
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    text_content = part.get_payload(decode=True).decode()
                    log_verbose(f"Found text part:\n{text_content}")
                    body += text_to_markdown_with_links(text_content)
                    log_verbose(f"Added text part to body:\n{body}")
                    break
                elif part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode()
                    log_verbose(f"Found HTML part:\n{html_content}")
                    body += html_to_text_with_links(html_content)
                    log_verbose(f"Added HTML part to body:\n{body}")
                    break
        else:
            log_verbose(
                f"Email from {from_addr} to {to_addr} with subject: {subject} is not multipart"
            )
            log_debug("Email is not multipart")
            if email_message.get_content_type() == "text/plain":
                text_content = email_message.get_payload(decode=True).decode()
                log_verbose(f"Found text part:\n{text_content}")
                body = text_to_markdown_with_links(text_content)
                log_verbose(f"Added text part to body:\n{body}")
            elif email_message.get_content_type() == "text/html":
                html_content = email_message.get_payload(decode=True).decode()
                log_verbose(f"Found HTML part:\n{html_content}")
                body = html_to_text_with_links(html_content)
                log_verbose(f"Added HTML part to body:\n{body}")

        body = body.strip()
        log_verbose(f"Simplified body:\n{body}")
        body = check_for_naked_links(body)
        log_verbose(f"Final body:\n{body}")
        discord_user_id = USER_MAP.get(to_addr, CATCH_ALL_USER_ID)
        log_debug(
            f"To address {to_addr} mapped to Discord user ID: {discord_user_id} ({to_addr})"
        )
        discord_embed = create_discord_embed(
            subject, from_addr, to_addr, body, formatted_time
        )
        log_verbose(
            f"Created embed for {to_addr} mapped to Discord user ID: {discord_user_id} ({to_addr})"
        )
        log_verbose(f"Embed:\n{discord_embed}")

        if isinstance(discord_embed, list):
            all_sent = True
            for embed in discord_embed:
                part = discord_embed.index(embed) + 1
                if send_discord_message(discord_user_id, embed):
                    log_debug(
                        f"Sent part {part} of email to {discord_user_id} ({to_addr}) with subject: {subject}"
                    )
                else:
                    log_error(
                        f"Failed to send part {part} of email to {discord_user_id} ({to_addr}) with subject: {subject}"
                    )
                    all_sent = False
            if all_sent:
                mail.store(num, "+FLAGS", "\\Seen")
                log_info(
                    f"Sent embed to {discord_user_id} ({to_addr}) with subject: {subject}"
                )
            else:
                mail.store(num, "-FLAGS", "\\Seen")
                log_info(
                    f"Reset email to unread for {discord_user_id} ({to_addr}) with subject: {subject}"
                )
        else:
            if send_discord_message(discord_user_id, discord_embed):
                log_info(
                    f"Sent embed to {discord_user_id} ({to_addr}) with subject: {subject}"
                )
                mail.store(num, "+FLAGS", "\\Seen")
            else:
                log_error(
                    f"Failed to send email to {discord_user_id} ({to_addr}) with subject: {subject}"
                )
                mail.store(num, "-FLAGS", "\\Seen")
                log_info(
                    f"Reset email to unread for {discord_user_id} ({to_addr}) with subject: {subject}"
                )

    mail.close()
    log_verbose("Logging out...")
    mail.logout()
    log_verbose("Logged out")
    log_debug("Checking for unread emails complete")


if __name__ == "__main__":
    log_info("Starting mailcord...")
    while True:
        try:
            check_emails()
        except Exception as e:
            log_error(f"An error occurred: {str(e)}")
        time.sleep(POLL_INTERVAL)
