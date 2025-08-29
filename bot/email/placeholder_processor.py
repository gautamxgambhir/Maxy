
import logging
import re
from typing import List, Dict, Set, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

class PlaceholderType(Enum):
    BASIC = "basic"
    FORMATTED = "formatted"
    CONDITIONAL = "conditional"

class PlaceholderProcessor:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.standard_placeholders = {
            'name': 'Recipient name',
            'event_name': 'Event or hackathon name',
            'date': 'Event date',
            'deadline': 'Registration or submission deadline',
            'location': 'Event location',
            'prize_pool': 'Prize pool amount',
            'contact_email': 'Contact email address',
            'website': 'Event website URL',
            'organization': 'Organization name',
            'time': 'Event time',
            'duration': 'Event duration',
            'theme': 'Event theme',
            'sponsors': 'List of sponsors',
            'judges': 'List of judges',
            'tracks': 'Competition tracks',
            'requirements': 'Participation requirements',
            'benefits': 'Benefits or perks',
            'social_media': 'Social media handles'
        }
        
        self.placeholder_pattern = re.compile(r'\{([^}]+)\}')
        
        self.advanced_pattern = re.compile(r'\{([^}:]+)(?::([^}]+))?\}')
    
    def extract_placeholders(self, template: str) -> List[str]:
        try:
            matches = self.placeholder_pattern.findall(template)
            unique_placeholders = list(set(matches))
            return sorted(unique_placeholders)
        except Exception as e:
            self.logger.error(f"Failed to extract placeholders: {str(e)}")
            return []
    
    def extract_placeholders_with_context(self, template: str) -> List[Dict[str, Any]]:
        try:
            placeholders = []
            for match in self.advanced_pattern.finditer(template):
                placeholder_name = match.group(1).strip()
                formatting = match.group(2) if match.group(2) else None
                
                placeholders.append({
                    'name': placeholder_name,
                    'full_match': match.group(0),
                    'formatting': formatting,
                    'start_pos': match.start(),
                    'end_pos': match.end(),
                    'description': self.standard_placeholders.get(placeholder_name, 'Custom placeholder')
                })
            
            return placeholders
        except Exception as e:
            self.logger.error(f"Failed to extract placeholders with context: {str(e)}")
            return []
    
    def validate_placeholders(self, placeholders: List[str], 
                            provided_values: Dict[str, str]) -> List[str]:
        try:
            missing = []
            for placeholder in placeholders:
                if placeholder not in provided_values:
                    missing.append(placeholder)
                elif not provided_values[placeholder] or not str(provided_values[placeholder]).strip():
                    missing.append(placeholder)
            return missing
        except Exception as e:
            self.logger.error(f"Failed to validate placeholders: {str(e)}")
            return placeholders
    
    def fill_placeholders(self, template: str, values: Dict[str, str]) -> str:
        try:
            result = template
            
            for match in self.advanced_pattern.finditer(template):
                placeholder_name = match.group(1).strip()
                formatting = match.group(2) if match.group(2) else None
                full_placeholder = match.group(0)
                
                if placeholder_name in values:
                    replacement_value = str(values[placeholder_name])
                    
                    if formatting:
                        replacement_value = self._apply_formatting(replacement_value, formatting)
                    
                    result = result.replace(full_placeholder, replacement_value)
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to fill placeholders: {str(e)}")
            return template
    
    def _apply_formatting(self, value: str, formatting: str) -> str:
        try:
            format_lower = formatting.lower().strip()
            
            if format_lower == 'upper':
                return value.upper()
            elif format_lower == 'lower':
                return value.lower()
            elif format_lower == 'title':
                return value.title()
            elif format_lower == 'capitalize':
                return value.capitalize()
            elif format_lower.startswith('date:'):
                date_format = format_lower.replace('date:', '').strip()
                return self._format_date(value, date_format)
            elif format_lower.startswith('currency'):
                return self._format_currency(value)
            elif format_lower.startswith('truncate:'):
                length = int(format_lower.replace('truncate:', '').strip())
                return value[:length] + ('...' if len(value) > length else '')
            else:
                self.logger.warning(f"Unknown formatting option: {formatting}")
                return value
        except Exception as e:
            self.logger.error(f"Failed to apply formatting '{formatting}': {str(e)}")
            return value
    
    def _format_date(self, value: str, date_format: str) -> str:
        try:
            if isinstance(value, str):
                date_formats = [
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                    '%Y-%m-%d %H:%M:%S',
                    '%B %d, %Y',
                    '%b %d, %Y'
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    if date_format == 'yyyy-mm-dd':
                        return parsed_date.strftime('%Y-%m-%d')
                    elif date_format == 'mm/dd/yyyy':
                        return parsed_date.strftime('%m/%d/%Y')
                    elif date_format == 'month dd, yyyy':
                        return parsed_date.strftime('%B %d, %Y')
                    elif date_format == 'mon dd, yyyy':
                        return parsed_date.strftime('%b %d, %Y')
                    else:
                        return parsed_date.strftime(date_format)
            
            return value
        except Exception as e:
            self.logger.error(f"Failed to format date: {str(e)}")
            return value
    
    def _format_currency(self, value: str) -> str:
        try:
            if value.replace(',', '').replace('$', '').replace('.', '').isdigit():
                amount = float(value.replace(',', '').replace('$', ''))
                return f"${amount:,.2f}"
            return value
        except Exception as e:
            self.logger.error(f"Failed to format currency: {str(e)}")
            return value
    
    def get_placeholder_suggestions(self, partial: str) -> List[Dict[str, str]]:
        try:
            partial_lower = partial.lower()
            suggestions = []
            
            for placeholder, description in self.standard_placeholders.items():
                if placeholder.lower().startswith(partial_lower):
                    suggestions.append({
                        'name': placeholder,
                        'description': description,
                        'example': f'{{{placeholder}}}'
                    })
            
            return sorted(suggestions, key=lambda x: x['name'])[:10]
        except Exception as e:
            self.logger.error(f"Failed to get placeholder suggestions: {str(e)}")
            return []
    
    def validate_template_syntax(self, template: str) -> Tuple[bool, List[str]]:
        errors = []
        
        try:
            open_braces = template.count('{')
            close_braces = template.count('}')
            
            if open_braces != close_braces:
                errors.append(f"Unmatched braces: {open_braces} opening, {close_braces} closing")
            
            if '{}' in template:
                errors.append("Empty placeholders found: {}")
            
            nested_pattern = re.compile(r'\{[^}]*\{[^}]*\}[^}]*\}')
            if nested_pattern.search(template):
                errors.append("Nested placeholders are not supported")
            
            placeholders = self.extract_placeholders(template)
            for placeholder in placeholders:
                if not re.match(r'^[a-zA-Z0-9_-]+$', placeholder):
                    errors.append(f"Invalid placeholder name: '{placeholder}' (use only letters, numbers, hyphens, underscores)")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Failed to validate template syntax: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def preview_filled_template(self, template: str, values: Dict[str, str], 
                               max_length: int = 500) -> Dict[str, Any]:
        try:
            placeholders = self.extract_placeholders(template)
            missing_placeholders = self.validate_placeholders(placeholders, values)
            
            preview_values = values.copy()
            
            for missing in missing_placeholders:
                preview_values[missing] = f"[{missing.upper()}]"
            
            filled_template = self.fill_placeholders(template, preview_values)
            
            if len(filled_template) > max_length:
                filled_template = filled_template[:max_length] + "..."
            
            return {
                'preview': filled_template,
                'total_placeholders': len(placeholders),
                'filled_placeholders': len(placeholders) - len(missing_placeholders),
                'missing_placeholders': missing_placeholders,
                'completion_percentage': ((len(placeholders) - len(missing_placeholders)) / len(placeholders) * 100) if placeholders else 100
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate preview: {str(e)}")
            return {
                'preview': template,
                'total_placeholders': 0,
                'filled_placeholders': 0,
                'missing_placeholders': [],
                'completion_percentage': 0,
                'error': str(e)
            }
    
    def get_placeholder_help(self, placeholder_name: str) -> Optional[Dict[str, Any]]:
        try:
            if placeholder_name in self.standard_placeholders:
                return {
                    'name': placeholder_name,
                    'description': self.standard_placeholders[placeholder_name],
                    'example_usage': f'{{{placeholder_name}}}',
                    'formatted_examples': [
                        f'{{{placeholder_name}:upper}}',
                        f'{{{placeholder_name}:lower}}',
                        f'{{{placeholder_name}:title}}'
                    ] if placeholder_name in ['name', 'event_name', 'organization'] else [],
                    'is_standard': True
                }
            else:
                return {
                    'name': placeholder_name,
                    'description': 'Custom placeholder',
                    'example_usage': f'{{{placeholder_name}}}',
                    'formatted_examples': [],
                    'is_standard': False
                }
        except Exception as e:
            self.logger.error(f"Failed to get placeholder help: {str(e)}")
            return None
    
    def batch_process_templates(self, templates: List[str], values: Dict[str, str]) -> List[Dict[str, Any]]:
        results = []
        
        for i, template in enumerate(templates):
            try:
                filled_template = self.fill_placeholders(template, values)
                placeholders = self.extract_placeholders(template)
                missing = self.validate_placeholders(placeholders, values)
                
                results.append({
                    'index': i,
                    'original': template,
                    'filled': filled_template,
                    'placeholders': placeholders,
                    'missing_placeholders': missing,
                    'success': len(missing) == 0
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'original': template,
                    'filled': template,
                    'placeholders': [],
                    'missing_placeholders': [],
                    'success': False,
                    'error': str(e)
                })
        
        return results

placeholder_processor = PlaceholderProcessor()