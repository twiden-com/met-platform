import requests

headers = {'authToken': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJDLURCRTY0MEZEMDBEMjRGNSIsImlhdCI6MTc1MTk1NTQxMiwiZXhwIjoxOTA5NjM1NDEyfQ.2iQ_mlLRo19TZEu6cCXvj9QMNzcdQhEKwZ7QNrJFreK4FswenISgSKjtnhTWul2iYhh7pwB3_a6zceta6xccVg'}

def send_otp(country_code:str, phone: str):
    url = f"https://cpaas.messagecentral.com/verification/v3/send?countryCode={country_code}&customerId=C-DBE640FD00D24F5&flowType=SMS&mobileNumber={phone}"
    response = requests.request("POST", url, headers=headers, data={})
    return response

def verify_otp(country_code, phone, verification_id, code):
    url = f"https://cpaas.messagecentral.com/verification/v3/validateOtp?countryCode={country_code}&mobileNumber={phone}&verificationId={verification_id}&customerId=C-DBE640FD00D24F5&code={code}"
    response = requests.request("GET", url, headers=headers, data={})
    return response