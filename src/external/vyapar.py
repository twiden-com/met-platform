import requests

def send_brochure(name: str,  phone_number: str, courses: str):
    # --- API configuration ---
    base_url = "https://vyaparautomation.com/api/v1/whatsapp/send/template"
    api_token = "10386|ZuIAj14oWZwLWZcMCwjGMqobJOIscRpJWVcIAnuN207547e5"
    phone_number_id = "566505076555546"
    template_id = "240498"

    # --- Build the query parameters ---
    params = {
        "apiToken": api_token,
        "phone_number_id": phone_number_id,
        "template_id": template_id,
        "templateVariable-leadname-1": name,
        "templateVariable-leadinterestedcourses-2": courses,
        "phone_number": phone_number
    }

    # --- Make the GET request ---
    try:
        response = requests.get(base_url, params=params, timeout=10)
        res =  response.json()
        if res['status'] == 1:
            return True
        else:
            return False
    except requests.RequestException as e:
        pass
