import os
from twilio.rest import Client

def send_test_sms(to_phone: str, message: str):
    TWILIO_SID = os.getenv("TWILIO_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    if not all([TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("Twilio environment variables are not properly set.")
        return

    if not to_phone.startswith('+'):
        to_phone = '+' + to_phone

    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    try:
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        print(f"Test SMS sent: SID={sms.sid}, Status={sms.status}")
    except Exception as e:
        print(f"Failed to send test SMS: {e}")

if __name__ == "__main__":
    # Replace with your phone number to test
    test_phone_number = "+1234567890"
    test_message = "This is a test SMS from ShieldX backend."

    send_test_sms(test_phone_number, test_message)
