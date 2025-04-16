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
        msg = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
        headers = msg["payload"]["headers"]
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        
        if "wwtarunsahu@gmail.com" not in sender:
            continue  # Ignore messages not from your testing sender

        # Extract the body
        parts = msg["payload"].get("parts", [])
        body = ""
        for part in parts:
            if part.get("mimeType") == "text/plain":
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                break

        # Find target email addresses in the body
        matches = re.findall(r'[\w\.-]+@[\w\.-]+', body)
        target_emails = [
            email for email in matches 
            if not email.endswith("@gmail.com") and not email.endswith("@algebrait.com")
        ]
        if not target_emails:
            continue

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "Regarding Your Job Posting")
        reply_text = (
            "Hello,\n\n"
            "I am very interested in the Java Developer with Webflux role you shared. "
            "I’ve attached my resume and am available to discuss this opportunity further.\n\n"
            "Please let me know if you need passport or work authorization details.\n\n"
            "Best,\nTarun"
        )

        message_body = f"To: {', '.join(target_emails)}\r\nSubject: Re: {subject}\r\n\r\n{reply_text}"
        raw_message = base64.urlsafe_b64encode(message_body.encode("utf-8")).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        service.users().messages().modify(
            userId="me", id=message["id"], body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return "Filtered replies sent."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
