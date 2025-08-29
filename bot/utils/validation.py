import re
import html

# Pre-compile regex patterns for better performance and security
NAME_PATTERN = re.compile(r"^[\w\s.'-]+$", re.UNICODE)
SKILLS_INTERESTS_PATTERN = re.compile(r"^[\w\s,.-]+$", re.UNICODE)

def validate_name(name):
    """Validate and sanitize name input."""
    if not isinstance(name, str):
        raise ValueError("Name must be a string")

    name = name.strip()

    if not 2 <= len(name) <= 100:
        raise ValueError("Name must be between 2-100 characters")

    if not NAME_PATTERN.match(name):
        raise ValueError("Name contains invalid characters. Only letters, numbers, spaces, hyphens, apostrophes, and periods are allowed")

    # Basic XSS protection
    name = html.escape(name)

    return name

def validate_skills(skills):
    """Validate and sanitize skills input."""
    if not isinstance(skills, str):
        raise ValueError("Skills must be a string")

    skills = skills.strip()

    if not skills:
        return ""

    if len(skills) > 500:
        raise ValueError("Skills text too long (max 500 characters)")

    # Check for potentially dangerous patterns
    if '<' in skills or '>' in skills or 'javascript:' in skills.lower():
        raise ValueError("Skills contain invalid characters")

    if not SKILLS_INTERESTS_PATTERN.match(skills):
        raise ValueError("Skills contain invalid characters. Only letters, numbers, spaces, commas, hyphens, and periods are allowed")

    # Basic XSS protection
    skills = html.escape(skills)

    return skills

def validate_interests(interests):
    """Validate and sanitize interests input."""
    if not isinstance(interests, str):
        raise ValueError("Interests must be a string")

    interests = interests.strip()

    if not interests:
        return ""

    if len(interests) > 500:
        raise ValueError("Interests text too long (max 500 characters)")

    # Check for potentially dangerous patterns
    if '<' in interests or '>' in interests or 'javascript:' in interests.lower():
        raise ValueError("Interests contain invalid characters")

    if not SKILLS_INTERESTS_PATTERN.match(interests):
        raise ValueError("Interests contain invalid characters. Only letters, numbers, spaces, commas, hyphens, and periods are allowed")

    # Basic XSS protection
    interests = html.escape(interests)

    return interests

def sanitize_input(text, max_length=1000):
    """General input sanitization function."""
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    text = text.strip()

    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    # Remove potentially dangerous HTML/script content
    text = html.escape(text)

    # Remove null bytes and other control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

    return text