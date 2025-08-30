import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import db
from bot.utils.embed import (
    volunteer_task_embed, volunteer_tasks_list_embed, success_embed, 
    error_embed, info_embed, confirmation_embed, ConfirmationView, PaginationView
)
from bot.utils.error_handler import (
    error_handler, defer_response, safe_send_response,
    ValidationError, DatabaseError, cooldown
)
import logging

class VolunteerTaskCreationModal(discord.ui.Modal, title="🤝 Create Volunteer Task"):
    """Modal for creating volunteer tasks with comprehensive information."""
    
    def __init__(self):
        super().__init__()
    
    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter a clear, descriptive title for the task",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    task_description = discord.ui.TextInput(
        label="Task Description",
        placeholder="Describe what needs to be done, requirements, and expectations...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    required_skills = discord.ui.TextInput(
        label="Required Skills (Optional)",
        placeholder="What skills are needed? (e.g., Photography, Social Media, Technical Support)",
        required=False,
        max_length=300,
        style=discord.TextStyle.short
    )
    
    time_commitment = discord.ui.TextInput(
        label="Time Commitment",
        placeholder="How long will this take? (e.g., 2 hours, 1 day, Ongoing)",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    location = discord.ui.TextInput(
        label="Location/Platform",
        placeholder="Where will this happen? (e.g., Discord, In-person, Hybrid)",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    contact_info = discord.ui.TextInput(
        label="Contact Information",
        placeholder="How should volunteers reach you? (Discord, email, etc.)",
        required=False,
        max_length=100,
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle volunteer task creation submission."""
        try:
            # Validate inputs
            if not self.task_title.value.strip():
                await interaction.response.send_message(
                    "❌ Task title is required!",
                    ephemeral=True
                )
                return
            
            if not self.task_description.value.strip():
                await interaction.response.send_message(
                    "❌ Task description is required!",
                    ephemeral=True
                )
                return
            
            discord_id = str(interaction.user.id)
            discord_username = interaction.user.name
            
            # Create volunteer task
            try:
                task_id = db.create_volunteer_task(
                    self.task_title.value.strip(),
                    discord_id,
                    discord_username
                )
            except Exception as e:
                await interaction.response.send_message(
                    "❌ Failed to create volunteer task. Please try again.",
                    ephemeral=True
                )
                return
            
            # Create success response
            embed = success_embed(
                "🤝 Volunteer Task Created!",
                f"**Task:** {self.task_title.value.strip()}\n**ID:** {task_id}"
            )
            
            embed.add_field(
                name="📝 Description",
                value=self.task_description.value[:1024],
                inline=False
            )
            
            if self.required_skills.value:
                embed.add_field(
                    name="🔧 Required Skills",
                    value=self.required_skills.value,
                    inline=True
                )
            
            embed.add_field(
                name="⏰ Time Commitment",
                value=self.time_commitment.value,
                inline=True
            )
            
            embed.add_field(
                name="📍 Location",
                value=self.location.value,
                inline=True
            )
            
            if self.contact_info.value:
                embed.add_field(
                    name="📞 Contact",
                    value=self.contact_info.value,
                    inline=True
                )
            
            embed.add_field(
                name="🎯 Next Steps",
                value="• Share this task with potential volunteers\n• Use the buttons below to manage your task\n• Volunteers can join using the task ID",
                inline=False
            )
            
            # Get task data for the view
            task_data = db.get_volunteer_task_by_id(task_id)
            if task_data:
                view = VolunteerTaskView(task_data, discord_id)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating volunteer task: {str(e)}",
                ephemeral=True
            )

class VolunteerTaskView(discord.ui.View):
    """Interactive view for volunteer task actions."""
    
    def __init__(self, task_data: dict, user_id: str, timeout: int = 300):
        super().__init__(timeout=timeout)
        self.task_data = task_data
        self.user_id = user_id
        self.is_creator = task_data.get('creator_id') == user_id
        self.is_open = task_data.get('status') == 'open'
        
        # Update button states based on task status and user role
        self.join_task.disabled = not self.is_open or self.is_creator
        self.leave_task.disabled = not self._is_participant()
        self.close_task.disabled = not self.is_creator or not self.is_open
        self.reopen_task.disabled = not self.is_creator or self.is_open
    
    def _is_participant(self) -> bool:
        """Check if user is a participant in this task."""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT COUNT(*) FROM volunteer_participants WHERE task_id = %s AND discord_id = %s" if db.mode == "postgres" else "SELECT COUNT(*) FROM volunteer_participants WHERE task_id = ? AND discord_id = ?"
                cursor.execute(query, (self.task_data['id'], self.user_id))
                count = cursor.fetchone()[0] if db.mode == "sqlite" else cursor.fetchone()["count"]
                return count > 0
        except Exception:
            return False
    
    @discord.ui.button(label="🙋 Join Task", style=discord.ButtonStyle.success)
    async def join_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ You can only join tasks for yourself!", ephemeral=True
            )
            return
        
        try:
            success = db.join_volunteer_task(
                self.task_data['id'], 
                self.user_id, 
                interaction.user.name
            )
            
            if success:
                embed = success_embed(
                    "Joined Task",
                    f"You've successfully joined **{self.task_data['title']}**!"
                )
                embed.add_field(
                    name="🎉 What's Next?",
                    value="The task creator will coordinate with volunteers. Check your DMs or the task updates!",
                    inline=False
                )
                
                # Update the view with new participant count
                updated_task = db.get_volunteer_task_by_id(self.task_data['id'])
                if updated_task:
                    task_embed = volunteer_task_embed(updated_task)
                    updated_view = VolunteerTaskView(updated_task, self.user_id)
                    await interaction.response.edit_message(embed=task_embed, view=updated_view)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = error_embed(
                    "Cannot Join Task",
                    "This task is no longer available or you're already a participant."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Join task error: {e}")
            embed = error_embed(
                "Join Failed",
                "An error occurred while joining the task."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🚪 Leave Task", style=discord.ButtonStyle.danger)
    async def leave_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "❌ You can only leave tasks for yourself!", ephemeral=True
            )
            return
        
        try:
            success = db.leave_volunteer_task(self.task_data['id'], self.user_id)
            
            if success:
                embed = success_embed(
                    "Left Task",
                    f"You've left **{self.task_data['title']}**."
                )
                
                # Update the view
                updated_task = db.get_volunteer_task_by_id(self.task_data['id'])
                if updated_task:
                    task_embed = volunteer_task_embed(updated_task)
                    updated_view = VolunteerTaskView(updated_task, self.user_id)
                    await interaction.response.edit_message(embed=task_embed, view=updated_view)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = error_embed(
                    "Cannot Leave Task",
                    "You're not a participant in this task."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Leave task error: {e}")
            embed = error_embed(
                "Leave Failed",
                "An error occurred while leaving the task."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="👥 View Participants", style=discord.ButtonStyle.primary)
    async def view_participants(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM volunteer_participants WHERE task_id = %s ORDER BY joined_at" if db.mode == "postgres" else "SELECT * FROM volunteer_participants WHERE task_id = ? ORDER BY joined_at"
                cursor.execute(query, (self.task_data['id'],))
                participants = cursor.fetchall()
            
            embed = info_embed(
                f"👥 Participants - {self.task_data['title']}",
                f"**Task ID:** #{self.task_data['id']}"
            )
            
            if participants:
                participant_list = []
                for i, participant in enumerate(participants, 1):
                    p_data = db._row_to_dict(participant)
                    join_date = p_data['joined_at']
                    if hasattr(join_date, 'strftime'):
                        date_str = join_date.strftime("%b %d, %Y")
                    else:
                        date_str = str(join_date)
                    
                    participant_list.append(f"{i}. {p_data['discord_username']} (joined {date_str})")
                
                embed.add_field(
                    name=f"Volunteers ({len(participants)})",
                    value="\n".join(participant_list),
                    inline=False
                )
            else:
                embed.add_field(
                    name="Volunteers",
                    value="No volunteers yet. Be the first to join!",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"View participants error: {e}")
            await interaction.response.send_message(
                "❌ Failed to load participants.", ephemeral=True
            )
    
    @discord.ui.button(label="🔒 Close Task", style=discord.ButtonStyle.secondary)
    async def close_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_creator:
            await interaction.response.send_message(
                "❌ Only task creators can close tasks!", ephemeral=True
            )
            return
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                query = "UPDATE volunteer_tasks SET status = %s WHERE id = %s" if db.mode == "postgres" else "UPDATE volunteer_tasks SET status = ? WHERE id = ?"
                cursor.execute(query, ('closed', self.task_data['id']))
                if db.mode == "sqlite":
                    conn.commit()
            
            embed = success_embed(
                "Task Closed",
                f"**{self.task_data['title']}** has been closed to new volunteers."
            )
            
            # Update the view
            updated_task = db.get_volunteer_task_by_id(self.task_data['id'])
            if updated_task:
                task_embed = volunteer_task_embed(updated_task)
                updated_view = VolunteerTaskView(updated_task, self.user_id)
                await interaction.response.edit_message(embed=task_embed, view=updated_view)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Close task error: {e}")
            embed = error_embed(
                "Close Failed",
                "An error occurred while closing the task."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔓 Reopen Task", style=discord.ButtonStyle.secondary)
    async def reopen_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_creator:
            await interaction.response.send_message(
                "❌ Only task creators can reopen tasks!", ephemeral=True
            )
            return
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                query = "UPDATE volunteer_tasks SET status = %s WHERE id = %s" if db.mode == "postgres" else "UPDATE volunteer_tasks SET status = ? WHERE id = ?"
                cursor.execute(query, ('open', self.task_data['id']))
                if db.mode == "sqlite":
                    conn.commit()
            
            embed = success_embed(
                "Task Reopened",
                f"**{self.task_data['title']}** is now open for new volunteers!"
            )
            
            # Update the view
            updated_task = db.get_volunteer_task_by_id(self.task_data['id'])
            if updated_task:
                task_embed = volunteer_task_embed(updated_task)
                updated_view = VolunteerTaskView(updated_task, self.user_id)
                await interaction.response.edit_message(embed=task_embed, view=updated_view)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Reopen task error: {e}")
            embed = error_embed(
                "Reopen Failed",
                "An error occurred while reopening the task."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class CreateTaskModal(discord.ui.Modal, title="Create Volunteer Task"):
    """Modal for creating a new volunteer task."""
    
    title_input = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter a clear, descriptive title for your task...",
        required=True,
        max_length=100
    )
    
    description = discord.ui.TextInput(
        label="Task Description (Optional)",
        placeholder="Provide more details about what volunteers will do...",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            title = self.title_input.value.strip()
            desc = self.description.value.strip()
            
            # Validate title
            if not 5 <= len(title) <= 100:
                embed = error_embed(
                    "Invalid Title",
                    "Task title must be between 5-100 characters."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create the task
            user = interaction.user
            task_id = db.create_volunteer_task(title, str(user.id), user.name)
            task_data = db.get_volunteer_task_by_id(task_id)
            
            if not task_data:
                embed = error_embed(
                    "Creation Failed",
                    "Failed to create the volunteer task."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create success embed
            embed = volunteer_task_embed(task_data)
            embed.title = "✅ Task Created Successfully!"
            
            if desc:
                embed.add_field(
                    name="📝 Description",
                    value=desc,
                    inline=False
                )
            
            embed.add_field(
                name="🎉 What's Next?",
                value="Your task is now live! Volunteers can join using `/volunteer join` or the buttons below.",
                inline=False
            )
            
            view = VolunteerTaskView(task_data, str(user.id))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Create task modal error: {e}")
            embed = error_embed(
                "Creation Failed",
                "An error occurred while creating the task."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class VolunteerCog(commands.Cog):
    volunteer_group = app_commands.Group(name="volunteer", description="Volunteer task management")

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    @volunteer_group.command(name="add", description="Create a new volunteer task")
    @error_handler("volunteer-add")
    @cooldown(30)  # 30 second cooldown to prevent spam
    async def add_task(self, interaction: discord.Interaction):
        """Open volunteer task creation modal."""
            # Show modal for detailed creation
        modal = VolunteerTaskCreationModal()
        await interaction.response.send_modal(modal)

    @volunteer_group.command(name="list", description="List all volunteer tasks with interactive browsing")
    @app_commands.describe(
        status="Filter by task status (optional)"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Open Tasks", value="open"),
        app_commands.Choice(name="Closed Tasks", value="closed"),
        app_commands.Choice(name="All Tasks", value="all")
    ])
    @error_handler("volunteer-list")
    async def list_tasks(self, interaction: discord.Interaction, status: str = "all"):
        await defer_response(interaction, ephemeral=True)
        
        try:
            if status == "all":
                tasks = db.get_all_volunteer_tasks()
            else:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    query = "SELECT * FROM volunteer_tasks WHERE status = %s ORDER BY created_at DESC" if db.mode == "postgres" else "SELECT * FROM volunteer_tasks WHERE status = ? ORDER BY created_at DESC"
                    cursor.execute(query, (status,))
                    rows = cursor.fetchall()
                    tasks = [db._row_to_dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"List tasks error: {e}")
            raise DatabaseError()
        
        if not tasks:
            status_text = f" ({status})" if status != "all" else ""
            embed = info_embed(
                f"No Volunteer Tasks{status_text}",
                "No volunteer tasks found."
            )
            embed.add_field(
                name="🚀 Get Started",
                value="Create the first task with `/volunteer add`!",
                inline=False
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        # Create paginated task list
        tasks_per_page = 5
        embeds = []
        
        for i in range(0, len(tasks), tasks_per_page):
            page_tasks = tasks[i:i + tasks_per_page]
            page_num = (i // tasks_per_page) + 1
            total_pages = (len(tasks) + tasks_per_page - 1) // tasks_per_page
            
            embed = volunteer_tasks_list_embed(page_tasks)
            status_text = f" ({status.title()})" if status != "all" else ""
            embed.title = f"📋 Volunteer Tasks{status_text}"
            embed.description = f"Found **{len(tasks)}** tasks • Page {page_num}/{total_pages}"
            
            embeds.append(embed)
        
        if len(embeds) == 1:
            await safe_send_response(interaction, embed=embeds[0], ephemeral=True)
        else:
            view = PaginationView(embeds)
            await safe_send_response(interaction, embed=embeds[0], view=view, ephemeral=True)

    @volunteer_group.command(name="join", description="Join a volunteer task")
    @app_commands.describe(
        task_id="ID of the task to join"
    )
    @error_handler("volunteer-join")
    @cooldown(5)
    async def join_task(self, interaction: discord.Interaction, task_id: int):
        await defer_response(interaction, ephemeral=True)
        
        # Get task data
        task_data = db.get_volunteer_task_by_id(task_id)
        if not task_data:
            embed = error_embed(
                "Task Not Found",
                f"No volunteer task found with ID #{task_id}.",
                "Use `/volunteer list` to see available tasks."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        if task_data['status'] != 'open':
            embed = error_embed(
                "Task Closed",
                f"Task **{task_data['title']}** is no longer accepting volunteers.",
                "Look for other open tasks with `/volunteer list`."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        user = interaction.user
        user_id = str(user.id)
        
        # Check if user is the creator
        if task_data['creator_id'] == user_id:
            embed = error_embed(
                "Cannot Join Own Task",
                "You cannot join a task you created.",
                "You're already the task coordinator!"
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        try:
            success = db.join_volunteer_task(task_id, user_id, user.name)
            
            if success:
                embed = volunteer_task_embed(task_data)
                embed.title = f"✅ Joined Task #{task_id}!"
                embed.add_field(
                    name="🎉 Welcome Aboard!",
                    value="You've successfully joined this volunteer task. The task creator will coordinate with all volunteers.",
                    inline=False
                )
                
                view = VolunteerTaskView(task_data, user_id)
                await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)
                
                self.logger.info(f"{user.name} joined volunteer task #{task_id}")
            else:
                embed = error_embed(
                    "Cannot Join Task",
                    "You may already be a participant or the task is no longer available."
                )
                await safe_send_response(interaction, embed=embed, ephemeral=True)
                
        except Exception as e:
            self.logger.error(f"Join task error: {e}")
            raise DatabaseError()

    @volunteer_group.command(name="leave", description="Leave a volunteer task")
    @app_commands.describe(
        task_id="ID of the task to leave"
    )
    @error_handler("volunteer-leave")
    @cooldown(5)
    async def leave_task(self, interaction: discord.Interaction, task_id: int):
        await defer_response(interaction, ephemeral=True)
        
        user = interaction.user
        user_id = str(user.id)
        
        try:
            success = db.leave_volunteer_task(task_id, user_id)
            
            if success:
                embed = success_embed(
                    "Left Task",
                    f"You've successfully left volunteer task #{task_id}."
                )
                await safe_send_response(interaction, embed=embed, ephemeral=True)
                
                self.logger.info(f"{user.name} left volunteer task #{task_id}")
            else:
                embed = error_embed(
                    "Cannot Leave Task",
                    "You're not a participant in this task or the task doesn't exist.",
                    "Use `/volunteer status` to see your current volunteer activities."
                )
                await safe_send_response(interaction, embed=embed, ephemeral=True)
                
        except Exception as e:
            self.logger.error(f"Leave task error: {e}")
            raise DatabaseError()

    @volunteer_group.command(name="status", description="View your volunteer activity and manage your tasks")
    @error_handler("volunteer-status")
    async def status(self, interaction: discord.Interaction):
        await defer_response(interaction, ephemeral=True)
        
        user = interaction.user
        user_id = str(user.id)
        
        try:
            data = db.get_user_volunteer_status(user_id)
            created = data.get("created", [])
            joined = data.get("joined", [])
        except Exception as e:
            self.logger.error(f"Status query error: {e}")
            raise DatabaseError()
        
        embed = info_embed(
            "👤 Your Volunteer Status",
            f"Activity summary for {user.mention}"
        )
        
        if created:
            created_list = []
            for task in created[:5]:  # Show max 5
                status_emoji = "🟢" if task['status'] == 'open' else "🔴"
                created_list.append(f"{status_emoji} **#{task['id']}** {task['title']} ({task['status']})")
            
            embed.add_field(
                name=f"📋 Tasks Created ({len(created)})",
                value="\n".join(created_list),
                inline=False
            )
            
            if len(created) > 5:
                embed.add_field(
                    name="",
                    value=f"*... and {len(created) - 5} more*",
                    inline=False
                )
        
        if joined:
            joined_list = []
            for task in joined[:5]:  # Show max 5
                status_emoji = "🟢" if task['status'] == 'open' else "🔴"
                joined_list.append(f"{status_emoji} **#{task['id']}** {task['title']} ({task['status']})")
            
            embed.add_field(
                name=f"🙋 Tasks Joined ({len(joined)})",
                value="\n".join(joined_list),
                inline=False
            )
            
            if len(joined) > 5:
                embed.add_field(
                    name="",
                    value=f"*... and {len(joined) - 5} more*",
                    inline=False
                )
        
        if not created and not joined:
            embed.description = "No volunteer activity yet."
            embed.add_field(
                name="🚀 Get Started",
                value="• Create a task: `/volunteer add`\n• Join a task: `/volunteer list` then `/volunteer join`\n• Discover opportunities: `/volunteer list`",
                inline=False
            )
        else:
            embed.add_field(
                name="💡 Quick Actions",
                value="• View all tasks: `/volunteer list`\n• Create new task: `/volunteer add`\n• Manage tasks: Use task ID with other commands",
                inline=False
            )
        
        await safe_send_response(interaction, embed=embed, ephemeral=True)

    @volunteer_group.command(name="view", description="View details of a specific volunteer task")
    @app_commands.describe(
        task_id="ID of the task to view"
    )
    @error_handler("volunteer-view")
    async def view_task(self, interaction: discord.Interaction, task_id: int):
        await defer_response(interaction, ephemeral=True)
        
        task_data = db.get_volunteer_task_by_id(task_id)
        if not task_data:
            embed = error_embed(
                "Task Not Found",
                f"No volunteer task found with ID #{task_id}.",
                "Use `/volunteer list` to see available tasks."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        embed = volunteer_task_embed(task_data)
        view = VolunteerTaskView(task_data, str(interaction.user.id))
        
        await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)

    @volunteer_group.command(name="remove", description="Remove a volunteer task (admin only)")
    @app_commands.describe(
        task_id="ID of the task to remove"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @error_handler("volunteer-remove")
    @cooldown(10)
    async def remove_task(self, interaction: discord.Interaction, task_id: int):
        await defer_response(interaction, ephemeral=True)
        
        # Get task data for confirmation
        task_data = db.get_volunteer_task_by_id(task_id)
        if not task_data:
            embed = error_embed(
                "Task Not Found",
                f"No volunteer task found with ID #{task_id}."
            )
            await safe_send_response(interaction, embed=embed, ephemeral=True)
            return
        
        embed = confirmation_embed(
            "Remove Volunteer Task",
            f"Are you sure you want to permanently remove task **#{task_id}: {task_data['title']}**?",
            "⚠️ This will remove all participants and cannot be undone!"
        )
        
        view = ConfirmationView()
        await safe_send_response(interaction, embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        if view.confirmed:
            try:
                success = db.remove_volunteer_task(task_id)
                
                if success:
                    embed = success_embed(
                        "Task Removed",
                        f"Volunteer task **#{task_id}: {task_data['title']}** has been permanently removed."
                    )
                else:
                    embed = error_embed(
                        "Removal Failed",
                        "Task not found or already removed."
                    )
                
                await interaction.edit_original_response(embed=embed, view=None)
                
                if success:
                    self.logger.info(f"Admin {interaction.user.name} removed volunteer task #{task_id}")
                    
            except Exception as e:
                self.logger.error(f"Remove task error: {e}")
                embed = error_embed(
                    "Removal Failed",
                    "An error occurred while removing the task."
                )
                await interaction.edit_original_response(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(VolunteerCog(bot))