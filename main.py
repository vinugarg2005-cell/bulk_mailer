import os
import random
import smtplib
import ssl
import time
import pandas as pd

from email.message import EmailMessage
from config import EMAIL, APP_PASSWORD, RESUME_PATH

# =========================
# SETTINGS
# =========================

MIN_DELAY = 45
MAX_DELAY = 120
DAILY_LIMIT = 40

# =========================
# LOAD RECRUITER DATA
# =========================

recruiters = pd.read_csv("recruiters.csv")

# Normalize column names
recruiters.columns = recruiters.columns.str.strip().str.lower()



if os.path.exists("sent_log.csv") and os.path.getsize("sent_log.csv") > 0:

    sent_df = pd.read_csv("sent_log.csv")
    sent_df.columns = sent_df.columns.str.strip().str.lower()

    if "email" in sent_df.columns:
        sent_emails = set(sent_df["email"])
    else:
        sent_emails = set()

else:
    sent_emails = set()

# =========================
# LOAD EMAIL TEMPLATES
# =========================

templates = []

for file in os.listdir("templates"):

    path = os.path.join("templates", file)

    if file.endswith(".txt"):

        with open(path, "r", encoding="utf-8") as f:
            templates.append(f.read())

# =========================
# CHECK RESUME
# =========================

if not os.path.exists(RESUME_PATH):
    print(f"Resume file not found: {RESUME_PATH}")
    exit()

if os.path.getsize(RESUME_PATH) == 0:
    print("Resume PDF is empty.")
    exit()

# =========================
# START SENDING
# =========================

count = 0

for index, row in recruiters.iterrows():

    if count >= DAILY_LIMIT:
        print("Daily limit reached.")
        break

    try:

        # =========================
        # GET DATA SAFELY
        # =========================

        name = str(row.get("name", "")).strip()
        receiver_email = str(row.get("email", "")).strip()
        company = str(row.get("company", "")).strip()

        # Skip invalid rows
        if not receiver_email or receiver_email == "nan":
            continue

        if receiver_email in sent_emails:
            print(f"Skipping duplicate: {receiver_email}")
            continue

        # =========================
        # LOAD RANDOM TEMPLATE
        # =========================

        template = random.choice(templates)

        email_content = template.format(
            name=name if name else "Hiring Team",
            company=company if company else "your company"
        )

        lines = email_content.split("\n")

        subject_line = lines[0].replace("Subject: ", "").strip()

        body = "\n".join(lines[1:])

        # =========================
        # CREATE EMAIL
        # =========================

        msg = EmailMessage()

        msg["From"] = EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject_line

        msg.set_content(body)

        # =========================
        # ATTACH RESUME
        # =========================

        with open(RESUME_PATH, "rb") as f:

            file_data = f.read()
            file_name = os.path.basename(RESUME_PATH)

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="pdf",
            filename=file_name
        )

        # =========================
        # NEW SMTP CONNECTION
        # =========================

        context = ssl.create_default_context()

        server = smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            context=context
        )

        server.login(EMAIL, APP_PASSWORD)

        # =========================
        # SEND EMAIL
        # =========================

        server.send_message(msg)

        server.quit()

        print(f"Sent to {receiver_email}")

        # =========================
        # SAVE LOG
        # =========================

        log_df = pd.DataFrame([
            {
                "name": name,
                "email": receiver_email,
                "company": company
            }
        ])

        if os.path.exists("sent_log.csv"):

            log_df.to_csv(
                "sent_log.csv",
                mode="a",
                header=False,
                index=False
            )

        else:

            log_df.to_csv(
                "sent_log.csv",
                index=False
            )

        count += 1

        # =========================
        # RANDOM DELAY
        # =========================

        delay = random.randint(MIN_DELAY, MAX_DELAY)

        print(f"Waiting {delay} seconds...\n")

        time.sleep(delay)

    except Exception as e:

        print(f"Failed for {receiver_email}")
        print(e)
        print()

print("Done sending emails.")