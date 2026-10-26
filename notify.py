"""Email the parent when something worth celebrating happens (e.g. a treat is earned).

Settings come from environment variables so the password never lands in git. On the server they
live in /etc/autumnmath.env, loaded by the autumnmath service:

    NOTIFY_EMAIL_TO=you@example.com
    SMTP_USER=you@gmail.com
    SMTP_PASSWORD=your 16-letter Gmail app password
    # optional: SMTP_HOST (default smtp.gmail.com), SMTP_PORT (default 587)

If they are not set, nothing is sent.
"""
import os
import smtplib
import threading
from email.message import EmailMessage


def is_configured() -> bool:
    return all(os.environ.get(key) for key in ("NOTIFY_EMAIL_TO", "SMTP_USER", "SMTP_PASSWORD"))


def send_email(subject: str, body: str) -> bool:
    if not is_configured():
        return False
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ["SMTP_USER"]
    message["To"] = os.environ["NOTIFY_EMAIL_TO"]
    message.set_content(body)
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", 587))
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(message)
    return True


def send_in_background(subject: str, body: str):
    """Send without making the kid's game wait; a failure is logged, never raised."""
    def worker():
        try:
            send_email(subject, body)
        except Exception as error:  # network or login trouble must not break the game
            print(f"notify: could not send email {subject!r}: {error}", flush=True)

    if is_configured():
        threading.Thread(target=worker, daemon=True).start()
