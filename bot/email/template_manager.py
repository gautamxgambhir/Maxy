
import logging
import uuid
from typing import List, Optional, Dict, Any, Tuple
from .models import Template, TemplateCategory, TemplateTone
from .database import email_db
from .all_templates import get_complete_template_collection

class TemplateManager:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = email_db
        
    async def get_template(self, category: str, template_name: str) -> Optional[Template]:
       """Retrieve specific template by category and name."""
       try:
           row = self.db.get_template_by_name(category, template_name)
           if row:
               return Template.from_dict(self.db._row_to_dict(row))
           return None
       except Exception as e:
           self.logger.error(f"Failed to get template {category}/{template_name}: {str(e)}")
           return None
    
    async def get_template_by_id(self, template_id: str) -> Optional[Template]:
       """Retrieve specific template by ID."""
       try:
           row = self.db.get_template(template_id)
           if row:
               return Template.from_dict(self.db._row_to_dict(row))
           return None
       except Exception as e:
           self.logger.error(f"Failed to get template by ID {template_id}: {str(e)}")
           return None
        
    async def get_available_templates(self, category: str) -> List[Template]:
       """List templates by category."""
       try:
           rows = self.db.get_templates_by_category(category)
           return [Template.from_dict(self.db._row_to_dict(row)) for row in rows]
       except Exception as e:
           self.logger.error(f"Failed to get templates for category {category}: {str(e)}")
           return []
    
    async def get_all_templates(self) -> List[Template]:
       """Get all templates."""
       try:
           rows = self.db.get_all_templates()
           return [Template.from_dict(self.db._row_to_dict(row)) for row in rows]
       except Exception as e:
           self.logger.error(f"Failed to get all templates: {str(e)}")
           return []
    
    async def get_templates_by_category_dict(self) -> Dict[str, List[Template]]:
        """Get all templates organized by category."""
        try:
            all_templates = await self.get_all_templates()
            templates_by_category = {}
            
            for template in all_templates:
                if template.category not in templates_by_category:
                    templates_by_category[template.category] = []
                templates_by_category[template.category].append(template)
            
            return templates_by_category
        except Exception as e:
            self.logger.error(f"Failed to organize templates by category: {str(e)}")
            return {}
        
    async def add_template(self, category: str, name: str, subject: str, 
                          body: str, tone: str = "formal") -> Optional[Template]:
        """Add new template."""
        try:
            template = Template.create_new(category, name, subject, body, tone)
            
            success = self.db.create_template(
                template.id,
                template.category,
                template.name,
                template.subject,
                template.body,
                template.tone,
                template.to_dict()['placeholders']
            )
            
            if success:
                self.logger.info(f"Created template: {category}/{name}")
                return template
            else:
                self.logger.warning(f"Template already exists: {category}/{name}")
                return None
                
        except ValueError as e:
            self.logger.error(f"Template validation failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to add template: {str(e)}")
            return None
        
    async def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Modify existing template."""
        try:
            existing_template = await self.get_template_by_id(template_id)
            if not existing_template:
                self.logger.warning(f"Template not found for update: {template_id}")
                return False
            
            updated_data = existing_template.to_dict()
            updated_data.update(updates)
            
            try:
                temp_template = Template.from_dict(updated_data)
            except ValueError as e:
                self.logger.error(f"Update validation failed: {str(e)}")
                return False
            
            if 'subject' in updates or 'body' in updates:
                updates['placeholders'] = temp_template.to_dict()['placeholders']
            
            success = self.db.update_template(template_id, updates)
            
            if success:
                self.logger.info(f"Updated template: {template_id}")
            else:
                self.logger.warning(f"No changes made to template: {template_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update template: {str(e)}")
            return False
    
    async def delete_template(self, template_id: str) -> bool:
        """Delete template by ID."""
        try:
            success = self.db.delete_template(template_id)
            if success:
                self.logger.info(f"Deleted template: {template_id}")
            else:
                self.logger.warning(f"Template not found for deletion: {template_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete template: {str(e)}")
            return False
    
    async def clone_template(self, template_id: str, new_name: str, 
                           new_tone: Optional[str] = None) -> Optional[Template]:
        """Clone an existing template with a new name."""
        try:
            original = await self.get_template_by_id(template_id)
            if not original:
                self.logger.warning(f"Template not found for cloning: {template_id}")
                return None
            
            cloned = original.clone(new_name, new_tone)
            
            success = self.db.create_template(
                cloned.id,
                cloned.category,
                cloned.name,
                cloned.subject,
                cloned.body,
                cloned.tone,
                cloned.to_dict()['placeholders']
            )
            
            if success:
                self.logger.info(f"Cloned template: {original.name} -> {new_name}")
                return cloned
            else:
                self.logger.warning(f"Failed to save cloned template: {new_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to clone template: {str(e)}")
            return None
    
    async def search_templates(self, query: str, category: Optional[str] = None) -> List[Template]:
        """Search templates by name, subject, or body content."""
        try:
            if category:
                templates = await self.get_available_templates(category)
            else:
                templates = await self.get_all_templates()
            
            query_lower = query.lower()
            matching_templates = []
            
            for template in templates:
                if (query_lower in template.name.lower() or
                    query_lower in template.subject.lower() or
                    query_lower in template.body.lower()):
                    matching_templates.append(template)
            
            return matching_templates
            
        except Exception as e:
            self.logger.error(f"Failed to search templates: {str(e)}")
            return []
    
    async def get_template_suggestions(self, partial_name: str, category: Optional[str] = None) -> List[str]:
        """Get template name suggestions based on partial input."""
        try:
            if category:
                templates = await self.get_available_templates(category)
            else:
                templates = await self.get_all_templates()
            
            partial_lower = partial_name.lower()
            suggestions = []
            
            for template in templates:
                if template.name.lower().startswith(partial_lower):
                    suggestions.append(template.name)
            
            return sorted(suggestions)[:10]
            
        except Exception as e:
            self.logger.error(f"Failed to get template suggestions: {str(e)}")
            return []
    
    async def validate_template_name(self, category: str, name: str, 
                                   exclude_id: Optional[str] = None) -> Tuple[bool, str]:
        """Validate if template name is available in category."""
        try:
            existing = await self.get_template(category, name)
            
            if existing and (not exclude_id or existing.id != exclude_id):
                return False, f"Template '{name}' already exists in category '{category}'"
            
            if not name or not name.strip():
                return False, "Template name cannot be empty"
            
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', name):
                return False, "Template name can only contain letters, numbers, hyphens, and underscores"
            
            return True, "Template name is valid"
            
        except Exception as e:
            self.logger.error(f"Failed to validate template name: {str(e)}")
            return False, "Error validating template name"
    
    async def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each template category."""
        try:
            templates_by_category = await self.get_templates_by_category_dict()
            stats = {}
            
            for category in TemplateCategory:
                category_templates = templates_by_category.get(category.value, [])
                
                tone_counts = {}
                for tone in TemplateTone:
                    tone_counts[tone.value] = sum(1 for t in category_templates if t.tone == tone.value)
                
                stats[category.value] = {
                    'total_templates': len(category_templates),
                    'tone_distribution': tone_counts,
                    'template_names': [t.name for t in category_templates]
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get category stats: {str(e)}")
            return {}
    
    async def bulk_import_templates(self, templates_data: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """Import multiple templates at once."""
        success_count = 0
        error_count = 0
        errors = []
        
        for template_data in templates_data:
            try:
                template = await self.add_template(
                    template_data['category'],
                    template_data['name'],
                    template_data['subject'],
                    template_data['body'],
                    template_data.get('tone', 'formal')
                )
                
                if template:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Failed to create template: {template_data.get('name', 'unknown')}")
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Error importing {template_data.get('name', 'unknown')}: {str(e)}")
        
        self.logger.info(f"Bulk import completed: {success_count} success, {error_count} errors")
        return success_count, error_count, errors

    async def seed_templates_async(self):
        """Seed the database with default templates if not already present."""
        try:
            # Check if templates are already seeded by counting existing templates
            existing_count = len(self.db.get_all_templates())

            if existing_count > 0:
                self.logger.info(f"Templates already seeded: {existing_count} templates found")
                return

            # Get all templates from the collection
            template_data = get_complete_template_collection()
            self.logger.info(f"Seeding {len(template_data)} templates into database")

            success_count = 0
            error_count = 0

            for template_dict in template_data:
                try:
                    # Create template using the existing add_template method
                    template = await self.add_template(
                        category=template_dict['category'],
                        name=template_dict['name'],
                        subject=template_dict['subject'],
                        body=template_dict['body'],
                        tone=template_dict.get('tone', 'formal')
                    )

                    if template:
                        success_count += 1
                    else:
                        error_count += 1
                        self.logger.warning(f"Failed to seed template: {template_dict['category']}/{template_dict['name']}")

                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Error seeding template {template_dict.get('name', 'unknown')}: {str(e)}")

            self.logger.info(f"Template seeding completed: {success_count} success, {error_count} errors")

        except Exception as e:
            self.logger.error(f"Template seeding failed: {str(e)}")

template_manager = TemplateManager()