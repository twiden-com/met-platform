import aiohttp

headers = {'authToken': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJDLURCRTY0MEZEMDBEMjRGNSIsImlhdCI6MTc1MTk1NTQxMiwiZXhwIjoxOTA5NjM1NDEyfQ.2iQ_mlLRo19TZEu6cCXvj9QMNzcdQhEKwZ7QNrJFreK4FswenISgSKjtnhTWul2iYhh7pwB3_a6zceta6xccVg'}

async def send_otp(phone):
    url = f"https://cpaas.messagecentral.com/verification/v3/send?countryCode=91&customerId=C-DBE640FD00D24F5&flowType=SMS&mobileNumber={phone}"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            raise Exception(f"Send OTP Failed")
        
async def verify_otp(phone, verification_id, code):
    url = f"https://cpaas.messagecentral.com/verification/v3/validateOtp?countryCode=91&mobileNumber={phone}&verificationId={verification_id}&customerId=C-DBE640FD00D24F5&code={code}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
            raise Exception(f"Verify OTP Failed")
