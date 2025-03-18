from scraper import (
    get_env,
    fetch_intent,
    fetch_available_slots,
    extract_readable_data,
    fill_email_text,
    get_passport_apt_text,
    send_email
)
import os
from constants import CITIZENSHIP_SUBDOMAIN

def load_previous_citizenship_appointments():
    if os.path.exists(CITIZENSHIP_APT_PATH):
        with open(CITIZENSHIP_APT_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        return set(str(line) for line in lines if line.strip().isdigit())
    return set()

def save_citizenship_appointments(appointments):
    with open(CITIZENSHIP_APT_PATH, "w", encoding="utf-8") as f:
        for apt_ts in sorted(appointments):
            f.write(f"{apt_ts}\n")

def get_citizenship_appointment_timestamps(monthly_slots):
    result = set()
    for item in monthly_slots:
        for slot in item['slots']:
            result.add(slot['startsAt'])
    return result

def notify_new_citizenship_appointments(citizenship_text):
    subject = "New Citizenship Appointments Available"
    
    passport_text = get_passport_apt_text()
    email_text = fill_email_text(TEMPLATE_PATH, passport_text, citizenship_text)

    # print(email_text)
    send_email(subject, email_text)

def main():
    global EMAIL, PASSWORD, DESTINATION_EMAIL, TEMPLATE_PATH, CITIZENSHIP_APT_PATH
    EMAIL, PASSWORD, DESTINATION_EMAIL, TEMPLATE_PATH, CITIZENSHIP_APT_PATH = get_env()

    citizenship_intent_id = fetch_intent(CITIZENSHIP_SUBDOMAIN)
    citizenship_slots = fetch_available_slots(citizenship_intent_id)
    citizenship_text = extract_readable_data(citizenship_slots)

    old_timestamps = load_previous_citizenship_appointments()
    new_timestamps = get_citizenship_appointment_timestamps(citizenship_slots)
    difference = new_timestamps - old_timestamps

    if difference:
        notify_new_citizenship_appointments(citizenship_text)
        save_citizenship_appointments(new_timestamps)
    else:
        print("No new citizenship appointments found.")

if __name__ == "__main__":
    main()
