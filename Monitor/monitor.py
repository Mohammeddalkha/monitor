import requests
from twilio.rest import Client
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== ENTER YOUR TWILIO CREDENTIALS HERE ==================
TWILIO_ACCOUNT_SID = "ACc1478a277b5cec22c01f25fdef4cf41a"  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = "c36830414c6f8d5bc8c70ac19d8f8662"     # Replace with your Twilio Auth Token
TWILIO_PHONE_NUMBER = "+18454078544"                       # Replace with your Twilio phone number

# ================== ENTER PHONE NUMBERS HERE ==================
YOUR_PHONE_NUMBER = "+918300521700"                        # Replace with your personal phone number
OTHER_PERSON_PHONE_NUMBER = "+919865147897"                # Replace with the other person's phone number

# URL to monitor
URL_TO_MONITOR = 'https://youtube.com'

# Headers to bypass WAF
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def wait_for_call_status(client, call_sid, timeout=60):
    """Waits for and returns the final status of a call."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        call = client.calls(call_sid).fetch()
        if call.status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
            return call.status
        time.sleep(2)
    return 'no-answer'

def send_call_notification(phone_number):
    """Sends a call notification using Twilio API when the monitored website is down with 502."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Make first call
        first_call = client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            twiml="<Response><Say>The monitored website is down with status code 502. Please check immediately.</Say></Response>"
        )
        print(f"First call initiated to {phone_number} with SID: {first_call.sid}")
        
        # Wait for call status
        call_status = wait_for_call_status(client, first_call.sid)
        print(f"First call status: {call_status}")
        
        # Make second call ONLY if first call was not answered
        if call_status == 'no-answer':
            print(f"First call was not answered. Attempting second call...")
            time.sleep(30)  # Wait 30 seconds before second attempt
            
            second_call = client.calls.create(
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                twiml="<Response><Say>This is a second attempt. The monitored website is down with status code 502. Please check immediately.</Say></Response>"
            )
            print(f"Second call initiated to {phone_number} with SID: {second_call.sid}")
            
            # Wait for second call status
            second_status = wait_for_call_status(client, second_call.sid)
            print(f"Second call status: {second_status}")
        else:
            print(f"First call was {call_status}. No second call needed.")
            
    except Exception as e:
        print(f"ERROR: Unable to send call notification to {phone_number}. Exception: {e}")

def check_url(url):
    """Checks the status of a given URL. Sends a call notification only if the URL returns a 502 error."""
    try:
        response = requests.get(url, timeout=10, verify=False, headers=HEADERS)

        if response.status_code == 502:
            print(f"ALERT: {url} is down with status code 502")
            send_call_notification(YOUR_PHONE_NUMBER)
            send_call_notification(OTHER_PERSON_PHONE_NUMBER)
        elif response.status_code == 403:
            print(f"WAF Blocked Request! Received 403 Forbidden. Checking response content for hidden 502...")
            if "502 Bad Gateway" in response.text:
                print(f"Detected 502 in response body despite WAF returning 403.")
                send_call_notification(YOUR_PHONE_NUMBER)
                send_call_notification(OTHER_PERSON_PHONE_NUMBER)
            else:
                print(f"Site is blocked by WAF. No action needed.")
        else:
            print(f"SUCCESS: {url} is up with status code {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Unable to reach {url}. Exception: {e}")

if __name__ == "__main__":
    print(f"Monitoring URL: {URL_TO_MONITOR}")
    check_url(URL_TO_MONITOR)
