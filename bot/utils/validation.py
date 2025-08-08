import re

def validate_name(name):
    if not 2 <= len(name) <= 100:
        raise ValueError("Name must be between 2-100 characters")
    if not re.match(r"^[\w\s.'-]+$", name):
        raise ValueError("Invalid characters in name")
    return name

def validate_skills(skills):
    if not skills:
        return ""
    if len(skills) > 500:
        raise ValueError("Skills text too long (max 500 characters)")
    return skills

def validate_interests(interests):
    if not interests:
        return ""
    if len(interests) > 500:
        raise ValueError("Interests text too long (max 500 characters)")
    return interests