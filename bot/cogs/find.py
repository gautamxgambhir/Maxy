import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils.embed import search_results_embed, info_embed, error_embed, PaginationView
from bot.utils.error_handler import (
    error_handler, defer_response, safe_send_response, 
    ValidationError, cooldown
)
from typing import List, Dict, Any
import logging

class SearchFiltersView(discord.ui.View):
    """Interactive view for search filters and options."""
    
    def __init__(self, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.skills_filter = ""
        self.interests_filter = ""
        self.limit = 10
    
    @discord.ui.button(label="🛠️ Filter by Skills", style=discord.ButtonStyle.primary)
    async def filter_skills(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SearchModal("Skills", "Enter skills to search for (comma separated)", "Python, JavaScript, Design...")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.search_value:
            self.skills_filter = modal.search_value
            await self._perform_search(interaction)
    
    @discord.ui.button(label="❤️ Filter by Interests", style=discord.ButtonStyle.primary)
    async def filter_interests(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SearchModal("Interests", "Enter interests to search for (comma separated)", "Machine Learning, Gaming, Web Dev...")
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.search_value:
            self.interests_filter = modal.search_value
            await self._perform_search(interaction)
    
    @discord.ui.button(label="🔍 Combined Search", style=discord.ButtonStyle.success)
    async def combined_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CombinedSearchModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.skills_value or modal.interests_value:
            self.skills_filter = modal.skills_value
            self.interests_filter = modal.interests_value
            await self._perform_search(interaction)
    
    @discord.ui.button(label="📊 Browse All", style=discord.ButtonStyle.secondary)
    async def browse_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Get all profiles with pagination
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM profiles ORDER BY updated_at DESC LIMIT 50")
                rows = cursor.fetchall()
                results = [db._row_to_dict(row) for row in rows]
            
            if not results:
                embed = info_embed(
                    "No Profiles Found",
                    "No profiles have been created yet. Be the first to create one with `/register-profile`!"
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return
            
            # Create paginated results
            embeds = self._create_paginated_embeds(results, "All Profiles")
            
            if len(embeds) == 1:
                await interaction.response.edit_message(embed=embeds[0], view=None)
            else:
                view = PaginationView(embeds)
                await interaction.response.edit_message(embed=embeds[0], view=view)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Browse all error: {e}")
            embed = error_embed(
                "Search Failed",
                "Failed to retrieve profiles. Please try again later."
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    async def _perform_search(self, interaction: discord.Interaction):
        """Perform search with current filters."""
        try:
            results = db.search_profiles(
                skills=self.skills_filter,
                interests=self.interests_filter,
                limit=50  # Get more results for pagination
            )
            
            if not results:
                search_terms = []
                if self.skills_filter:
                    search_terms.append(f"Skills: {self.skills_filter}")
                if self.interests_filter:
                    search_terms.append(f"Interests: {self.interests_filter}")
                
                embed = info_embed(
                    "No Results Found",
                    f"No profiles found matching: {', '.join(search_terms)}",
                )
                embed.add_field(
                    name="💡 Search Tips",
                    value="• Try broader terms\n• Check spelling\n• Use common skill names\n• Try searching interests instead",
                    inline=False
                )
                await interaction.response.edit_message(embed=embed, view=None)
                return
            
            # Create paginated results
            search_type = "Search Results"
            if self.skills_filter and self.interests_filter:
                search_type = f"Skills: {self.skills_filter[:20]}... & Interests: {self.interests_filter[:20]}..."
            elif self.skills_filter:
                search_type = f"Skills: {self.skills_filter}"
            elif self.interests_filter:
                search_type = f"Interests: {self.interests_filter}"
            
            embeds = self._create_paginated_embeds(results, search_type)
            
            if len(embeds) == 1:
                await interaction.response.edit_message(embed=embeds[0], view=None)
            else:
                view = PaginationView(embeds)
                await interaction.response.edit_message(embed=embeds[0], view=view)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Search error: {e}")
            embed = error_embed(
                "Search Failed",
                "An error occurred while searching. Please try again."
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    def _create_paginated_embeds(self, results: List[Dict[str, Any]], search_type: str) -> List[discord.Embed]:
        """Create paginated embeds for search results."""
        embeds = []
        results_per_page = 5
        
        for i in range(0, len(results), results_per_page):
            page_results = results[i:i + results_per_page]
            page_num = (i // results_per_page) + 1
            total_pages = (len(results) + results_per_page - 1) // results_per_page
            
            embed = search_results_embed(page_results)
            embed.title = f"🔍 {search_type}"
            embed.description = f"Found **{len(results)}** profiles • Page {page_num}/{total_pages}"
            
            embeds.append(embed)
        
        return embeds

class SearchModal(discord.ui.Modal):
    """Modal for single search input."""
    
    def __init__(self, search_type: str, label: str, placeholder: str):
        super().__init__(title=f"Search by {search_type}")
        self.search_value = ""
        
        self.search_input = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            required=True,
            max_length=200
        )
        self.add_item(self.search_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.search_value = self.search_input.value.strip()
        await interaction.response.defer()

class CombinedSearchModal(discord.ui.Modal, title="Combined Search"):
    """Modal for combined skills and interests search."""
    
    def __init__(self):
        super().__init__()
        self.skills_value = ""
        self.interests_value = ""
    
    skills_input = discord.ui.TextInput(
        label="Skills (optional)",
        placeholder="Python, JavaScript, Design...",
        required=False,
        max_length=200
    )
    
    interests_input = discord.ui.TextInput(
        label="Interests (optional)",
        placeholder="Machine Learning, Gaming, Web Development...",
        required=False,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        self.skills_value = self.skills_input.value.strip()
        self.interests_value = self.interests_input.value.strip()
        
        if not self.skills_value and not self.interests_value:
            embed = error_embed(
                "Invalid Search",
                "Please provide at least one search criteria."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()

class FindCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @app_commands.command(
        name="find",
        description="Find users by skills, interests, or browse all profiles"
    )
    @app_commands.describe(
        skills="Skills to search for (comma separated, optional)",
        interests="Interests to search for (comma separated, optional)",
        limit="Number of results to show (1-20, default: 10)"
    )
    @error_handler("find")
    @cooldown(3)  # 3 second cooldown
    async def find_command(
        self,
        interaction: discord.Interaction,
        skills: str = "",
        interests: str = "",
        limit: app_commands.Range[int, 1, 20] = 10
    ):
        await defer_response(interaction, ephemeral=True)
        
        # If no parameters provided, show interactive search
        if not skills and not interests:
            embed = info_embed(
                "🔍 Find Hackathon Partners",
                "Use the buttons below to search for teammates with specific skills or interests!"
            )
            embed.add_field(
                name="🎯 Search Options",
                value="• **Filter by Skills** - Find people with specific technical skills\n• **Filter by Interests** - Find people with similar interests\n• **Combined Search** - Search both skills and interests\n• **Browse All** - See all registered profiles",
                inline=False
            )
            embed.add_field(
                name="💡 Pro Tips",
                value="• Use specific skill names (e.g., 'React', 'Python')\n• Try broader terms if no results\n• Check out profiles to find potential teammates",
                inline=False
            )
            
            view = SearchFiltersView()
            await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)
            return
        
        # Validate input lengths
        if len(skills) > 200:
            raise ValidationError("Skills search term is too long (max 200 characters)")
        if len(interests) > 200:
            raise ValidationError("Interests search term is too long (max 200 characters)")
        
        # Perform search
        try:
            results = db.search_profiles(
                skills=skills.strip() if skills else None,
                interests=interests.strip() if interests else None,
                limit=min(limit, 20)  # Cap at 20 for performance
            )
        except Exception as e:
            self.logger.error(f"Database search error: {e}")
            embed = error_embed(
                "Search Failed",
                "Database error occurred while searching.",
                "Please try again in a few moments."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        if not results:
            search_terms = []
            if skills:
                search_terms.append(f"Skills: {skills}")
            if interests:
                search_terms.append(f"Interests: {interests}")
            
            embed = info_embed(
                "No Results Found",
                f"No profiles found matching: {', '.join(search_terms)}"
            )
            embed.add_field(
                name="💡 Try These Tips",
                value="• Use broader search terms\n• Check your spelling\n• Try searching by interests instead\n• Use `/find` without parameters for interactive search",
                inline=False
            )
            
            # Add suggestion to create profile if user doesn't have one
            user_profile = db.get_profile(str(interaction.user.id))
            if not user_profile:
                embed.add_field(
                    name="🚀 Get Started",
                    value="Create your own profile with `/register-profile` to help others find you!",
                    inline=False
                )
            
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        # Create search results embed
        embed = search_results_embed(results)
        
        # Add search context
        search_context = []
        if skills:
            search_context.append(f"Skills: {skills}")
        if interests:
            search_context.append(f"Interests: {interests}")
        
        embed.description = f"Found **{len(results)}** profiles matching: {', '.join(search_context)}"
        
        # Add helpful footer
        if len(results) == limit:
            embed.set_footer(text=f"Showing {limit} results • Use interactive search for more options • Maximally : The global hackathon league")
        
        await safe_send_response(interaction, embed=embed, ephemeral=True)
        self.logger.info(f"Search completed by {interaction.user.name}: {len(results)} results")

    @app_commands.command(
        name="find-random",
        description="Discover random profiles to find potential teammates"
    )
    @app_commands.describe(
        count="Number of random profiles to show (1-10, default: 5)"
    )
    @error_handler("find-random")
    @cooldown(5)
    async def find_random(
        self,
        interaction: discord.Interaction,
        count: app_commands.Range[int, 1, 10] = 5
    ):
        await defer_response(interaction, ephemeral=True)
        
        try:
            # Get random profiles
            with db.get_connection() as conn:
                cursor = conn.cursor()
                if db.mode == "postgres":
                    cursor.execute("SELECT * FROM profiles ORDER BY RANDOM() LIMIT %s", (count,))
                else:
                    cursor.execute("SELECT * FROM profiles ORDER BY RANDOM() LIMIT ?", (count,))
                
                rows = cursor.fetchall()
                results = [db._row_to_dict(row) for row in rows]
        
        except Exception as e:
            self.logger.error(f"Random search error: {e}")
            embed = error_embed(
                "Search Failed",
                "Failed to retrieve random profiles.",
                "Please try again in a few moments."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        if not results:
            embed = info_embed(
                "No Profiles Available",
                "No profiles have been created yet.",
                "Be the first to create one with `/register-profile`!"
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        # Remove self from results if present
        user_id = str(interaction.user.id)
        results = [r for r in results if r['discord_id'] != user_id]
        
        if not results:
            embed = info_embed(
                "Only Your Profile Found",
                "You're the only one with a profile so far!",
                "Encourage others to create profiles with `/register-profile`"
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        embed = search_results_embed(results)
        embed.title = "🎲 Random Profile Discovery"
        embed.description = f"Here are **{len(results)}** random profiles to explore:"
        embed.add_field(
            name="💡 Discovery Tip",
            value="Reach out to people with complementary skills or similar interests!",
            inline=False
        )
        
        await safe_send_response(interaction, embed=embed, ephemeral=True)
        self.logger.info(f"Random discovery by {interaction.user.name}: {len(results)} profiles")

async def setup(bot):
    await bot.add_cog(FindCog(bot))