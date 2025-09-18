import requests
from src.config.settings import settings

headers= {'authToken': settings.message_central_header_key}

def send_otp(country_code:str, phone: str):
    url = f"https://cpaas.messagecentral.com/verification/v3/send?countryCode={country_code}&customerId={settings.message_central_customer_id}&flowType=SMS&mobileNumber={phone}"
    response = requests.request("POST", url, headers=headers, data={})
    return response

def verify_otp(country_code, phone, verification_id, code):
    url = f"https://cpaas.messagecentral.com/verification/v3/validateOtp?countryCode={country_code}&mobileNumber={phone}&verificationId={verification_id}&customerId={settings.message_central_customer_id}&code={code}"
    response = requests.request("GET", url, headers=headers, data={})
    return response