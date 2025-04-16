from flask import Flask, request
import base64
import os
import re
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

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
        headers = msg["payload"].get("headers", [])

        to_emails = set()
        body_text = ""

        # Extract known fields
        for header in headers:
            name = header.get("name", "")
            value = header.get("value", "")
            if name in ["From", "To", "Cc"]:
                to_emails.update(re.findall(r'[\w\.-]+@[\w\.-]+', value))

        # Extract email body
        if "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part.get("mimeType") == "text/plain":
                    body_data = part["body"].get("data", "")
                    body_text = base64.urlsafe_b64decode(body_data + '===').decode("utf-8", errors="ignore")
        elif "body" in msg["payload"]:
            body_data = msg["payload"]["body"].get("data", "")
            body_text = base64.urlsafe_b64decode(body_data + '===').decode("utf-8", errors="ignore")

        # Add email addresses found in body
        body_emails = re.findall(r'[\w\.-]+@[\w\.-]+', body_text)
        to_emails.update(body_emails)

        # Remove known internal domains
        filtered_emails = [e for e in to_emails if not e.endswith(('algebrait.com', 'gmail.com'))]

        if not filtered_emails:
            continue

        # Compose the reply
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender_name = filtered_emails[0].split('@')[0].title()

        reply_text = f"Hello {sender_name},\n\nI recently received a job requirement from my employer, and I wanted to express my strong interest in this position. I'm open to relocating if necessary and look forward to the possibility of joining your team.\n\nPlease feel free to reach out to me at your earliest convenience to discuss this opportunity further. If required, I can also provide passport details as well.\n\nLooking forward to hearing from you soon.\nMy Employers details:\n\nSandy@algebrait.com , Rosy@algebrait.com \n\n7372796091  7372796092"

        message_body = f"To: {', '.join(filtered_emails)}\r\nSubject: Re: {subject}\r\n\r\n{reply_text}"
        raw_message = base64.urlsafe_b64encode(message_body.encode("utf-8")).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        service.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return "Filtered replies sent."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
