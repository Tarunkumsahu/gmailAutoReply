from flask import Flask, request
import base64
import os
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
        headers = msg["payload"]["headers"]
        sender = next((h["value"] for h in headers if h["name"] == "From"), None)
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

        if not sender:
            continue

        name = sender.split("<")[0].strip()
        reply_text = f"Hello {name},\n\nThank you for reaching out. I will get back to you shortly.\n\nRegards,\nTarun"
        message_body = f"To: {sender}\r\nSubject: Re: {subject}\r\n\r\n{reply_text}"
        raw_message = base64.urlsafe_b64encode(message_body.encode("utf-8")).decode("utf-8")

        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        service.users().messages().modify(
            userId="me",
            id=message["id"],
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    return "Auto-replies sent."

# ✅ FIX for Cloud Run: Bind to the expected port
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
