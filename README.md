# Jamaican High Commission Appointment Availability Checker

The `scraper.py` script retrieves available appointment slots for both Passport and Citizenship services offered by the Jamaican High Commission in the United Kingdom. It does so by interacting with the [YouCanBook.me API](https://ycbm.stoplight.io/docs/youcanbookme-api), creating an intent, obtaining an availability key, and then fetching appointment slots for several months in advance. The script can also send an email with the resulting availability information.

A companion component, `citizenship_notifier.py`, compares freshly scraped Citizenship appointments with a saved record of previously known appointment timestamps. If any new slots are detected, it sends a dedicated email alert for Citizenship appointments and updates the stored timestamps, ensuring only newly introduced slots trigger notifications.

---

## Table of Contents

1. [Features](#features)  
2. [Requirements](#requirements)  
3. [Setup Instructions](#setup-instructions)  
4. [How It Works](#how-it-works)  
5. [Environment Variables](#environment-variables)  
6. [Usage](#usage)
7. [Automation](#automation)
8. [References](#references)
9. [Notes](#notes)

---

## Features

- Creates an "intent" on the YouCanBook.me API to begin an availability search.  
- Requests an availability key for each month and retrieves time slots.  
- Loops through the current and next five months, collecting all available appointment slots.  
- Sends a summary via email if desired.

---

## Requirements

- Python 3.7 or higher  
- [requests](https://pypi.org/project/requests/)  
- [python-dotenv](https://pypi.org/project/python-dotenv/)  
- [python-dateutil](https://pypi.org/project/python-dateutil/)

Install requirements in your environment:
```bash
pip install requests python-dotenv python-dateutil
```

---

## Setup Instructions

- Clone or download the script onto your local machine.
- Create a .env file in the same directory as the script.
- Set up a Google app-specific password to allow sending emails programmatically. The standard Google password often fails with less-secure app restrictions. A Google app-specific password can be created through your [Google Account's App Passwords page](https://myaccount.google.com/apppasswords).

---

## How It Works

1. Environment Variables and Credentials
    The script starts by loading environment variables from the .env file, which contain your email credentials and the destination email for sending availability updates.

2. Creating an Intent
    The script calls the YouCanBook.me intents endpoint for each subdomain (e.g., jhcukconsular and jhcukconsular-3) to generate an intent_id.

3. Fetching the Availability Key
    Each intent_id is used to get an availability_key for a specific month, starting from a given date (current date by default).

4. Retrieving Slots
    Once the script has an availability_key, it fetches appointment slots for that month. It repeats this process for five consecutive months.

5. Formatting Results
    Appointment data is parsed to produce a readable summary of month labels and time slots.

6. Sending Email
    The script can optionally send an email containing the summarized results using Gmail SMTP.

---

## Environment Variables

Create a file named .env in the same folder as the script, containing three variables:

```
EMAIL=your_email@gmail.com
PASSWORD=xxxx xxxx xxxx xxxx
DESTINATION_EMAIL=recipient@example.com
TEMPLATE_PATH=/path/to/email_template.txt
CITIZENSHIP_APT_PATH=/path/to/citizenship_appointment_data.txt
```

- EMAIL: Sender's email address (Gmail)
- PASSWORD: Google app-specific password (16 characters in blocks of  4 separated by spaces)
- DESTINATION_EMAIL: Recipient’s email address
- TEMPLATE_PATH: File path to `email_template.txt`
- CITIZENSHIP_APT_PATH: File path to `citizenship_appointment_data.txt`, a local persistent store of citizenship appointment timestamps which is updated everytime new citizenship appointments are found. This file's contents is read by `citizenship_notifier.py` to conditionally send emails based on whether new citizenship appointment slots are available.

---

## Usage

1. Set up your .env file with valid credentials.
2. Run the script from the command line:

```bash
python3 scraper.py
```

The script will print information to the console and can optionally send an email with results if the relevant lines are uncommented.

---

## Automation
Cron Job Setup (macOS)

To automate this script to run every hour on a Mac, follow these steps:
- Identify the Python interpreter path in the virtual environment.
- Activate the virtual environment:

`source /path/to/venv/bin/activate`

Then run:

`which python`

Copy the output path, for example:

`/Users/YourName/Projects/venv/bin/python`

Edit your crontab.
Open the crontab editor:

`crontab -e`

Add a new cron job entry.
For a script you want to run every hour at minute 0:

`0 * * * * /Users/YourName/Projects/venv/bin/python /Users/YourName/Projects/scraper.py`
`0 * * * * /Users/YourName/Projects/venv/bin/python /Users/YourName/Projects/citizenship_notifier.py`

0 * * * * will trigger the job at the top of every hour.
Adjust paths to match where the script and virtual environment are stored.

Save the crontab.
When you exit the editor, cron will automatically register the new job.

---

## References

- [YouCanBook.me API Documentation](https://ycbm.stoplight.io/docs/youcanbookme-api)
- [Google App Passwords Setup](https://myaccount.google.com/apppasswords)
- [Passport Appointment Booking Page - Jamaican High Commission, UK](https://jhcukconsular.youcanbook.me/)
- [Citizenship Appointment Booking Page - Jamaican High Commission, UK](https://jhcukconsular-3.youcanbook.me/)
- [Jamaican High Commission United Kingdom Official Website](https://www.jhcuk.org/)

---

## Notes

- Intents can be used to create multiple availability keys.
- Once an availability key is used to fetch appointment slots, it typically expires within 2–3 minutes.
- To refresh availability, generate a new availability key by calling the API with a valid intent again.