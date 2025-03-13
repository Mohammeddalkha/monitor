import requests
import os
import time
from datetime import datetime
from twilio.rest import Client
import mysql.connector
import urllib3
import pytz
from pytz import timezone


# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== Twilio Credentials ==================
TWILIO_ACCOUNT_SID = "ACc1478a277b5cec22c01f25fdef4cf41a"  
TWILIO_AUTH_TOKEN = "c36830414c6f8d5bc8c70ac19d8f8662"    
TWILIO_PHONE_NUMBER = "+18454078544"    

RECIPIENTS = {
    "+918300521700": "DALHA",
    "+919876543210": "USER2"  # Add other recipients if needed
}

# ================== URLs to Monitor ==================
URLS_TO_MONITOR = [
    'https://fcrm.myfundbox.com',
    'https://httpstat.us/502'  # Add multiple URLs
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ================== MySQL Database Setup ==================
DB_CONFIG = {
    'host': 'ballast.proxy.rlwy.net',
    'user': 'root',
    'password': 'RnHgTWEWcuvjvlQHTKSEzYqLGGFtDUSS',
    'database': 'railway',
    'port': 32373
}

def get_db_connection():
    """Establish connection with MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Initialize database table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            url VARCHAR(255),
            status VARCHAR(10),
            call_initiated VARCHAR(10),
            recipient VARCHAR(50)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()



IST = timezone('Asia/Kolkata')

def log_to_db(url, status, call_initiated, recipient):
    """Log monitoring events to MySQL database in IST."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert timestamp to IST and store in 24-hour format
    timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")  

    query = "INSERT INTO monitor_log (timestamp, url, status, call_initiated, recipient) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (timestamp, url, status, call_initiated, recipient))

    conn.commit()
    cursor.close()
    conn.close()


def wait_for_call_status(client, call_sid, timeout=60):
    """Wait for call status."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        call = client.calls(call_sid).fetch()
        if call.status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
            return call.status
        time.sleep(2)
    return 'no-answer'

def send_call_notification(phone_number, url):
    """Send call notification when site is down."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = f"The monitored website {url} is down with status code 502. Please check immediately."
        
        first_call = client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml=f"<Response><Say>{message}</Say></Response>"
        )
        print(f"Call initiated to {phone_number}, Call SID: {first_call.sid}")

        call_status = wait_for_call_status(client, first_call.sid)
        print(f"First call status: {call_status}")

        if call_status == 'no-answer':
            print(f"First call not answered. Attempting second call...")
            time.sleep(30)
            
            second_call = client.calls.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                twiml=f"<Response><Say>{message}</Say></Response>"
            )
            print(f"Second call initiated to {phone_number}, Call SID: {second_call.sid}")

            second_status = wait_for_call_status(client, second_call.sid)
            print(f"Second call status: {second_status}")

        return call_status not in ['failed', 'canceled']

    except Exception as e:
        print(f"ERROR: Unable to send call notification to {phone_number}. Exception: {e}")
        return False

def check_url(url):
    """Check the status of a given URL."""
    try:
        response = requests.get(url, timeout=10, verify=False, headers=HEADERS)
        status_code = response.status_code

        if status_code == 502:
            print(f"ALERT: {url} is DOWN (502 Bad Gateway)")

            for phone, recipient in RECIPIENTS.items():
                call_sent = send_call_notification(phone, url)
                if call_sent:
                    log_to_db(url, "DOWN", "YES", recipient)

        elif status_code == 403:
            print(f"WARNING: {url} returned 403 Forbidden. Checking response for hidden 502...")
            if "502 Bad Gateway" in response.text:
                print(f"Detected 502 in response body despite 403 Forbidden.")
                
                for phone, recipient in RECIPIENTS.items():
                    call_sent = send_call_notification(phone, url)
                    if call_sent:
                        log_to_db(url, "DOWN", "YES", recipient)
            else:
                print(f"Site is blocked by WAF. No action needed.")

        else:
            print(f"✅ {url} is UP (Status Code: {status_code})")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Unable to reach {url}. Exception: {e}")

if __name__ == "__main__":
    init_db()
    for url in URLS_TO_MONITOR:
        check_url(url)  # Fixed variable name
