import time
import logging
import serial
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self, twilio_account_sid: str, twilio_auth_token: str, twilio_phone_number: str, gsm_port: str = 'COM3'):
        """
        Initialize SMS service with Twilio and GSM modem configurations
        
        Args:
            twilio_account_sid (str): Twilio account SID
            twilio_auth_token (str): Twilio auth token
            twilio_phone_number (str): Twilio phone number to send from
            gsm_port (str): GSM modem port (default: 'COM3' for Windows)
        """
        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.twilio_phone_number = twilio_phone_number
        self.gsm_port = gsm_port
        self.gsm_modem = None
        
    def send_via_twilio(self, phone_number: str, message: str) -> bool:
        """
        Send SMS using Twilio API (requires internet connection)
        
        Args:
            phone_number (str): Recipient phone number
            message (str): Message content
            
        Returns:
            bool: True if successful, raises exception otherwise
        """
        try:
            # Format phone number if needed
            if not phone_number.startswith('+'):
                phone_number = f"+{phone_number}"
                
            # Send message via Twilio
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            logger.info(f"Message sent successfully via Twilio to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message via Twilio: {str(e)}")
            raise
    
    def send_via_gsm(self, phone_number: str, message: str) -> bool:
        """
        Send SMS using GSM modem (works offline)
        
        Args:
            phone_number (str): Recipient phone number
            message (str): Message content
            
        Returns:
            bool: True if successful, raises exception otherwise
        """
        try:
            # Format phone number if needed
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]  # Remove '+' for GSM modem
                
            # Format message (GSM modems have character limitations)
            formatted_message = message.replace('\n', ' ')
            
            # Initialize GSM modem connection
            self.gsm_modem = serial.Serial(self.gsm_port, 9600, timeout=5)
            
            # Initialize modem
            self.gsm_modem.write(b'AT\r')
            time.sleep(0.5)
            self.gsm_modem.write(b'AT+CMGF=1\r')  # Set to text mode
            time.sleep(0.5)
            
            # Send SMS using GSM modem
            self.gsm_modem.write(f'AT+CMGS="{phone_number}"\r'.encode())
            time.sleep(0.5)
            self.gsm_modem.write(formatted_message.encode() + b'\x1A')
            time.sleep(1)
            
            logger.info(f"Message sent successfully via GSM to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message via GSM: {str(e)}")
            raise
        finally:
            if self.gsm_modem:
                self.gsm_modem.close()
                self.gsm_modem = None