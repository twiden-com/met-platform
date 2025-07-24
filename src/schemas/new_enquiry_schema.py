from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import json

class StudentEnquiryRequest(BaseModel):
    verified_phone: str = Field(..., description="Verified phone number")
    verification_id: Optional[str] = None
    student_name: str = Field(..., min_length=2, max_length=100)
    additional_people: Optional[int] = Field(default=0, ge=0, le=10)
    country: Optional[str] = Field(default="India", max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    place: Optional[str] = Field(None, max_length=100)
    purpose: Optional[str] = None
    college_name: Optional[str] = Field(None, max_length=200)
    passout_year: Optional[int] = Field(None, ge=1990, le=2030)
    degree: Optional[str] = None
    lead_source: Optional[str] = None
    mode: Optional[str] = None
    slot_preference: Optional[str] = None
    counselled_by: Optional[str] = None
    urgency: Optional[str] = None
    interested_courses: List[str] = Field(..., min_length=1)
    comments: Optional[str] = Field(None, max_length=1000)
    send_brochure: Optional[bool] = Field(default=False)

    @field_validator('student_name')
    @classmethod
    def validate_student_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Student name is required')
        return v.strip().title()

    @field_validator('verified_phone')
    @classmethod
    def validate_phone(cls, v):
        if not v or '-' not in v:
            raise ValueError('Invalid phone number format')
        return v.strip()

    @field_validator('state', 'place', 'college_name', 'comments')
    @classmethod
    def clean_string_fields(cls, v):
        return v.strip() if v else None

    @field_validator('interested_courses')
    @classmethod
    def validate_courses(cls, v):
        if not v:
            raise ValueError('At least one course must be selected')
        valid_courses = [
            'data_science_ai', 'python_fullstack_ai', 'digital_marketing_ai',
            'cybersecurity', 'java_fullstack_ai', 'data_analytics_ai',
            'generative_ai', 'video_editing_graphic_design', 'multi_cloud_devops'
        ]
        for course in v:
            if course not in valid_courses:
                raise ValueError(f'Invalid course: {course}')
        return v

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        if v is None:
            return v
        valid_options = ['job_placement', 'career_switch', 'skill_upgrade', 'knowledge_enhancement', 
                        'entrepreneurship', 'certification', 'fresher_training', 'other']
        if v not in valid_options:
            raise ValueError(f'Invalid purpose: {v}')
        return v

    @field_validator('degree')
    @classmethod
    def validate_degree(cls, v):
        if v is None:
            return v
        valid_options = ['below_10th', '10th_completed', '12th_pursuing', '12th_completed',
                        'diploma_pursuing', 'diploma_completed', 'btech_pursuing', 'btech_completed',
                        'bsc_pursuing', 'bsc_completed', 'bcom_pursuing', 'bcom_completed',
                        'ba_pursuing', 'ba_completed', 'other_ug_pursuing', 'other_ug_completed',
                        'mtech_pursuing', 'mtech_completed', 'msc_pursuing', 'msc_completed',
                        'mba_pursuing', 'mba_completed', 'other_pg_pursuing', 'other_pg_completed',
                        'working_professional', 'career_gap', 'other']
        if v not in valid_options:
            raise ValueError(f'Invalid degree: {v}')
        return v

    @field_validator('lead_source')
    @classmethod
    def validate_lead_source(cls, v):
        if v is None:
            return v
        valid_options = ['marketing_ravi', 'marketing_ashok', 'google_maps', 'social_media',
                        'referral', 'direct_walkin', 'website', 'google_ads', 'other']
        if v not in valid_options:
            raise ValueError(f'Invalid lead_source: {v}')
        return v

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        if v is None:
            return v
        valid_options = ['online', 'offline', 'hybrid']
        if v not in valid_options:
            raise ValueError(f'Invalid mode: {v}')
        return v

    @field_validator('slot_preference')
    @classmethod
    def validate_slot_preference(cls, v):
        if v is None:
            return v
        valid_options = ['6am-8am', '8am-11am', '11am-1pm', '1pm-3pm', '3pm-5pm',
                        '5pm-7pm', '7pm-9pm', '9pm-11pm', 'flexible']
        if v not in valid_options:
            raise ValueError(f'Invalid slot_preference: {v}')
        return v

    @field_validator('counselled_by')
    @classmethod
    def validate_counselled_by(cls, v):
        if v is None:
            return v
        valid_options = ['not_yet', 'ushmika', 'pallavi', 'taniath', 'other']
        if v not in valid_options:
            raise ValueError(f'Invalid counselled_by: {v}')
        return v

    @field_validator('urgency')
    @classmethod
    def validate_urgency(cls, v):
        if v is None:
            return v
        valid_options = ['immediately', 'one_week', '2_3_weeks', 'one_month', 'two_months']
        if v not in valid_options:
            raise ValueError(f'Invalid urgency: {v}')
        return v

    def to_db_dict(self, counsellor_id: Optional[str] = None) -> dict:
        """Convert to database format"""
        return {
            "email": self.verified_phone + '@met.com',
            "phone_number": self.verified_phone,
            "verification_id": self.verification_id,
            "student_name": self.student_name,
            "additional_people": self.additional_people,
            "country": self.country,
            "state": self.state,
            "place": self.place,
            "purpose": self.purpose,
            "college_name": self.college_name,
            "passout_year": self.passout_year,
            "degree": self.degree,
            "lead_source": self.lead_source,
            "mode": self.mode,
            "slot_preference": self.slot_preference,
            "counselled_by": self.counselled_by,
            "urgency": self.urgency,
            "interested_courses": json.dumps(self.interested_courses),
            "comments": self.comments,
            "send_brochure": self.send_brochure,
            "created_by": counsellor_id,
            # "is_verified": 1,
            "is_active": 1,
            "role": "student"
        }