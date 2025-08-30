
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
import json
import re
import uuid
from enum import Enum

class TemplateTone(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    HYPE = "hype"

class TemplateCategory(Enum):
    JUDGES = "judges"
    SPONSORS = "sponsors"
    SCHOOLS = "schools"
    COLLEGE_CLUBS = "college-clubs"
    COMMUNITIES = "communities"
    PARTICIPANTS = "participants"
    MENTORS_SPEAKERS = "mentors-speakers"
    PRESS_MEDIA = "press-media"
    VOLUNTEERS_TASK_FORCE = "volunteers-task-force"
    POST_EVENT_GENERAL = "post-event-general"

@dataclass
class Template:
    id: str
    category: str
    name: str
    subject: str
    body: str
    tone: str = "formal"
    placeholders: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.validate()

        if not self.placeholders or not isinstance(self.placeholders, list):
            self.placeholders = self.extract_placeholders()
    
    def validate(self) -> None:
        errors = []
        
        if not self.id or not self.id.strip():
            errors.append("Template ID is required")
        
        if not self.category or not self.category.strip():
            errors.append("Category is required")
        
        if not self.name or not self.name.strip():
            errors.append("Template name is required")
        
        if not self.subject or not self.subject.strip():
            errors.append("Subject is required")
        
        if not self.body or not self.body.strip():
            errors.append("Body is required")
        
        valid_categories = [cat.value for cat in TemplateCategory]
        if self.category not in valid_categories:
            errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        
        valid_tones = [tone.value for tone in TemplateTone]
        if self.tone not in valid_tones:
            errors.append(f"Invalid tone. Must be one of: {', '.join(valid_tones)}")
        
        if len(self.subject) > 200:
            errors.append("Subject must be 200 characters or less")
        
        if len(self.body) > 10000:
            errors.append("Body must be 10,000 characters or less")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.name):
            errors.append("Template name can only contain letters, numbers, hyphens, and underscores")
        
        if errors:
            raise ValueError(f"Template validation failed: {'; '.join(errors)}")
    
    def extract_placeholders(self) -> List[str]:
        placeholder_pattern = r'\{([^}]+)\}'
        
        subject_placeholders = re.findall(placeholder_pattern, self.subject)
        body_placeholders = re.findall(placeholder_pattern, self.body)
        
        all_placeholders = list(set(subject_placeholders + body_placeholders))
        return sorted(all_placeholders)
    
    def get_missing_placeholders(self, provided_values: Dict[str, str]) -> List[str]:
        return [p for p in self.placeholders if p not in provided_values or not provided_values[p].strip()]
    
    def fill_placeholders(self, values: Dict[str, str]) -> 'Template':
        filled_subject = self.subject
        filled_body = self.body
        
        for placeholder, value in values.items():
            placeholder_pattern = f"{{{placeholder}}}"
            filled_subject = filled_subject.replace(placeholder_pattern, str(value))
            filled_body = filled_body.replace(placeholder_pattern, str(value))
        
        return Template(
            id=f"{self.id}_filled_{uuid.uuid4().hex[:8]}",
            category=self.category,
            name=f"{self.name}_filled",
            subject=filled_subject,
            body=filled_body,
            tone=self.tone,
            placeholders=[],
            created_at=self.created_at,
            updated_at=datetime.now()
        )
    
    def preview(self, max_body_length: int = 200) -> str:
        body_preview = self.body[:max_body_length]
        if len(self.body) > max_body_length:
            body_preview += "..."
        
        return f"**{self.name}** ({self.tone})\n**Subject:** {self.subject}\n**Body:** {body_preview}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'category': self.category,
            'name': self.name,
            'subject': self.subject,
            'body': self.body,
            'tone': self.tone,
            'placeholders': json.dumps(self.placeholders),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        placeholders_data = data.get('placeholders', '[]')
        try:
            if isinstance(placeholders_data, str):
                placeholders = json.loads(placeholders_data)
            elif isinstance(placeholders_data, list):
                placeholders = placeholders_data
            else:
                placeholders = []
        except (json.JSONDecodeError, TypeError, ValueError):
            placeholders = []

        return cls(
            id=data['id'],
            category=data['category'],
            name=data['name'],
            subject=data['subject'],
            body=data['body'],
            tone=data.get('tone', 'formal'),
            placeholders=placeholders,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    @classmethod
    def create_new(cls, category: str, name: str, subject: str, body: str, 
                   tone: str = "formal") -> 'Template':
        template_id = f"{category}_{name}_{uuid.uuid4().hex[:8]}"
        return cls(
            id=template_id,
            category=category,
            name=name,
            subject=subject,
            body=body,
            tone=tone
        )
    
    def clone(self, new_name: Optional[str] = None, new_tone: Optional[str] = None) -> 'Template':
        return Template(
            id=f"{self.category}_{new_name or self.name}_clone_{uuid.uuid4().hex[:8]}",
            category=self.category,
            name=new_name or f"{self.name}_copy",
            subject=self.subject,
            body=self.body,
            tone=new_tone or self.tone,
            placeholders=self.placeholders.copy(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def __str__(self) -> str:
        return f"Template({self.category}/{self.name}, {len(self.placeholders)} placeholders)"
    
    def __repr__(self) -> str:
        return (f"Template(id='{self.id}', category='{self.category}', "
                f"name='{self.name}', tone='{self.tone}', "
                f"placeholders={self.placeholders})")

@dataclass
class EmailLog:
    id: str
    template_id: str
    template_name: str
    recipient_email_hash: str
    recipient_name: str
    status: str
    error_message: Optional[str] = None
    sent_at: datetime = field(default_factory=datetime.now)
    sent_by: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'template_id': self.template_id,
            'template_name': self.template_name,
            'recipient_email_hash': self.recipient_email_hash,
            'recipient_name': self.recipient_name,
            'status': self.status,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat(),
            'sent_by': self.sent_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailLog':
        return cls(
            id=data['id'],
            template_id=data['template_id'],
            template_name=data['template_name'],
            recipient_email_hash=data['recipient_email_hash'],
            recipient_name=data['recipient_name'],
            status=data['status'],
            error_message=data.get('error_message'),
            sent_at=datetime.fromisoformat(data['sent_at']),
            sent_by=data.get('sent_by', 0)
        )