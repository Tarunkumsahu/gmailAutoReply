from flask import Flask, request
import base64
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

@app.route("/", methods=["GET"])
def gmail_auto_reply():
    creds = Credentials(
        None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"]
    )

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me", labelIds=["INBOX", "UNREAD"], maxResults=5
    ).execute()

    messages = results.get("messages", [])

    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()
        headers = msg["payload"]["headers"]
        sender = next((h["value"] for h in headers if h["name"] == "From"), None)
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

        if not sender or not any(domain in sender for domain in ["rosy@algebrait.com", "sandy@algebrait.com"]):
            continue

        full_body = base64.urlsafe_b64decode(msg["payload"].get("body", {}).get("data", "")).decode("utf-8", errors="ignore")

        # Check for external contact info
        external_email = None
        phone_number = None
        for line in full_body.splitlines():
            if "@" in line and not any(domain in line for domain in ["algebrait.com", "gmail.com"]):
                external_email = line.strip()
            if any(char.isdigit() for char in line) and not ("7372796091" in line or "7372796092" in line):
                phone_number = line.strip()

        if not external_email:
            continue

        # Compose reply
        name = external_email.split("@")[0]
        reply_text = (
            f"Hello {name},\n\n"
            "I hope you're doing well. I recently received a job requirement from my employer, and I wanted to express my strong interest in this position.\n"
            "I'm open to relocating if necessary and look forward to the possibility of joining your team.\n\n"
            "Please feel free to reach out to me at your earliest convenience to discuss this opportunity further. If required, I can also provide passport details as well.\n\n"
            "Looking forward to hearing from you soon.\n"
            "My Employers details: \n\n"
            "Sandy@algebrait.com , Rosy@algebrait.com \n\n"
            "7372796091  7372796092\n\n"
            "--\n\n"
            "Tarun Sahu\n"
            "P: 469-454-8473\n"
            "E: tarun.kum.sahu@gmail.com\n"
            "L: https://www.linkedin.com/in/tarun-sahu-716595243/"
        )

        # Compose MIME message
        message = MIMEMultipart()
        message["to"] = sender
        message["subject"] = f"Re: {subject}"
        message.attach(MIMEText(reply_text, "plain"))

        # TODO: Attach resume.pdf later

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        service.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return "Auto-replies sent."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
