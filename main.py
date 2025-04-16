from flask import Flask
import base64
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import re

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

    # Get unread messages
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX", "UNREAD"], maxResults=1
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return "No unread messages."

    msg_id = messages[0]["id"]
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    headers = msg["payload"]["headers"]

    sender = next((h["value"] for h in headers if h["name"] == "From"), None)
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    to = next((h["value"] for h in headers if h["name"] == "To"), "")
    cc = next((h["value"] for h in headers if h["name"] == "Cc"), "")

    # Combine recipients and filter only non-gmail/non-algebrait addresses
    raw_recipients = [sender] + re.split(r',\s*', to) + re.split(r',\s*', cc)
    filtered_recipients = [
        r for r in raw_recipients if not re.search(r'(@gmail\.com|@algebrait\.com)', r, re.I)
    ]
    unique_emails = list(set([re.search(r'[\w\.-]+@[\w\.-]+', r).group() for r in filtered_recipients if re.search(r'@', r)]))

    if not unique_emails:
        return "No filtered recipients to reply to."

    # Email content
    reply_text = """Hello,

I hope you're doing well. I recently received a job requirement from my employer, and I wanted to express my strong interest in this position. I'm open to relocating if necessary and look forward to the possibility of joining your team.

Please feel free to reach out to me at your earliest convenience to discuss this opportunity further. If required, I can also provide passport details.

Looking forward to hearing from you soon.

My Employer's contacts:
sandy@algebrait.com, rosy@algebrait.com
7372796091, 7372796092

Regards,  
Tarun Sahu  
P: 469-454-8473  
E: tarun.kum.sahu@gmail.com  
L: https://www.linkedin.com/in/tarun-sahu-716595243/
"""

    to_header = ', '.join(unique_emails)
    message_body = f"To: {to_header}\r\nSubject: Re: {subject}\r\n\r\n{reply_text}"
    raw_message = base64.urlsafe_b64encode(message_body.encode("utf-8")).decode("utf-8")

    # Send the email
    service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

    # Mark the original message as read
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()

    return f"Replied to {to_header}."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
