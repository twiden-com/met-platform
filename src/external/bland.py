import requests
from src.config.settings import settings

BLAND_API_KEY = settings.bland_ai_key

def bland_start_interview(
        profile_id: str,
        course_name: str,

        interview_id: str,
        interview_topic: str,
        interview_max_duration: str,
        interview_questions: str,

        trainer_name: str,
        user_name: str, 
        phone_number: str, 
        ):

    if phone_number.startswith("+91"):
        phone_number = phone_number.replace("+91", "")
    elif phone_number.startswith("91") and len(phone_number) > 10:
        phone_number = phone_number[2:]

    phone_number = "+91" + phone_number
    phone_number = phone_number.strip()

    # Headers
    headers = {
        'Authorization': BLAND_API_KEY,
    }

    # Data
    data = {
        "phone_number": phone_number,
        "voice": "June",
        "wait_for_greeting": False,
        "record": True,
        "answered_by_enabled": True,
        "noise_cancellation": False,
        "interruption_threshold": 100,
        "block_interruptions": False,
        "max_duration": 3,
        "model": "base",
        "memory_id": "bec3c84b-346e-492d-a9dc-c245b30d7aa8",
        "language": "en-IN",
        "background_track": "none",
        "endpoint": "https://api.bland.ai",
        "voicemail_action": "hangup",
        "summary_prompt": "Asses his communication, knowledge, and overall scores out of 10",
        "isCallActive": False,
        "task": f'''
            You are conducting a skill assessment interview for {user_name}, 
            He/She is studying {course_name} in MedhaEduTech, Hyderabad's best IT education institute, trained by {trainer_name}
            Speak in a warm, professional, and engaging manner. 
            Use a conversational tone that builds rapport while maintaining credibility. 
            Show genuine interest in the student's potential.
            ---
            ## Opening
            "Hi! I'm calling on behalf of your trainer {trainer_name} from Medha EduTech for your interview on the topic - {interview_topic}. 
            This will take about {interview_max_duration} minutes
            and this will help us better assess you. Ready to start?"

            ## Questions (Ask in order)

            {interview_questions}

            ## Closing
            "Great talking to you. Based on our conversation, I will share the feedback in the portal after this call.

            Have a great day {user_name}. See you!"
            ---

            ## Key Behavioral Guidelines:
            - Keep responses concise and focused
            - Share course information clearly
            - Guide toward office visit
            - Keep conversations under 10 minutes
            - Collect required information naturally during conversation
            - Be helpful but not overly chatty
            - Wait for complete answers before moving on
            - If answer is too short, say "Can you tell me more about that?"
            - Keep a conversational, encouraging tone
            ''',
        # "first_sentence": f"\"Hi {user_name}, Hope you're doing well. This is an short mock interview call\"",
        "timezone": "Asia/Kolkata",
        "transfer_phone_number": "+917093370381",
        "webhook": "https://webhook.site/e4b575dc-ffc4-45d2-82d0-cc8bb88f32ba",
        "dispositions": [
            'canidate_performance_excellent', 
            'candidate_performance_good', 
            'candidate_performance_average',
            'candidate_performance_poor'
        ],
        "analysis_schema": {
            "performance_summary": "",
            "areas_of_improvement_summary": "",
            "strengths_of_candidate_summary": "",
            "weaknesses_of_candidate_summary": "",
            "communication_score_out_of_10": "",
            "knowledge_score_out_of_10": "",
            "overall_score_out_of_10": ""
        },
        "metadata": {
            "user_id": profile_id,
            "interview_id": interview_id
        }
    }

    # API request 
    response = requests.post('https://api.bland.ai/v1/calls', json=data, headers=headers)
    
    if response.status_code == 200:
        r = response.json()
        return r
    

def call_status(call_id: str):
    headers = {
        'Authorization': BLAND_API_KEY,
    }
    response = requests.get(f"https://api.bland.ai/v1/calls/{call_id}", headers=headers)
    if response.status_code == 200:
        response = response.json()
        return response