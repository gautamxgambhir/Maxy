import discord
from config import Config

def create_embed(title, description, color=discord.Color.red()):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if Config.MAXIMALLY_LOGO_URL:
        embed.set_thumbnail(url=Config.MAXIMALLY_LOGO_URL)
    embed.set_footer(text="Maximally : The global hackathon league")
    return embed

def profile_embed(profile):
    embed = create_embed(
        f"Profile: {profile['name']}",
        f"Discord: {profile['discord_username']}",
        discord.Color.red()
    )
    if profile['skills']:
        embed.add_field(name="Skills", value=profile['skills'], inline=False)
    if profile['interests']:
        embed.add_field(name="Interests", value=profile['interests'], inline=False)
    return embed

def search_results_embed(results):
    embed = create_embed(
        "🔍 Users Search Results",
        f"Found {len(results)} matching profiles:",
        discord.Color.red()
    )
    
    for profile in results:
        skills = profile['skills'] or "No skills listed"
        interests = profile['interests'] or "No interests listed"
        
        embed.add_field(
            name=f"{profile['name']} (@{profile['discord_username']})",
            value=f"**Skills:** {skills}\n**Interests:** {interests}\n━━━━━━━━━━━━━━",
            inline=False
        )
    
    return embed

def base_embed(title, description=None, color=discord.Color.blue()):
    """Create a basic embed with consistent styling."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if Config.MAXIMALLY_LOGO_URL:
        embed.set_thumbnail(url=Config.MAXIMALLY_LOGO_URL)
    embed.set_footer(text="Maximally : The global hackathon league")
    return embed

def volunteer_task_embed(task):
    """Create an embed for a single volunteer task."""
    status_emoji = "🟢" if task["status"] == "open" else "🔴"
    embed = create_embed(
        f"{status_emoji} Volunteer Task #{task['id']}",
        f"**{task['title']}**",
        discord.Color.green() if task["status"] == "open" else discord.Color.red()
    )

    embed.add_field(
        name="Status",
        value=task["status"].title(),
        inline=True
    )

    embed.add_field(
        name="Created By",
        value=task["creator_username"],
        inline=True
    )

    embed.add_field(
        name="Created",
        value=task["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(task["created_at"], 'strftime') else str(task["created_at"]),
        inline=True
    )

    # Get participants count
    from bot.core.database import db
    with db.get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM volunteer_participants WHERE task_id = %s" if db.mode == "postgres" else "SELECT COUNT(*) FROM volunteer_participants WHERE task_id = ?"
        cursor.execute(query, (task["id"],))
        count_result = cursor.fetchone()
        participants = count_result[0] if db.mode == "sqlite" else count_result["count"]

    embed.add_field(
        name="Participants",
        value=str(participants),
        inline=True
    )

    return embed

def volunteer_tasks_list_embed(tasks):
    """Create an embed listing all volunteer tasks."""
    embed = create_embed(
        "📋 Volunteer Tasks",
        f"Found {len(tasks)} volunteer tasks:",
        discord.Color.blue()
    )

    if not tasks:
        embed.description = "No volunteer tasks available. Create one with `/volunteer add`!"
        return embed

    for task in tasks[:10]:  # Limit to 10 tasks
        status_emoji = "🟢" if task["status"] == "open" else "🔴"
        created_date = task["created_at"].strftime("%Y-%m-%d") if hasattr(task["created_at"], 'strftime') else str(task["created_at"])

        embed.add_field(
            name=f"{status_emoji} #{task['id']}: {task['title']}",
            value=f"**Creator:** {task['creator_username']}\n**Status:** {task['status'].title()}\n**Created:** {created_date}",
            inline=False
        )

    if len(tasks) > 10:
        embed.set_footer(text=f"Showing 10 of {len(tasks)} tasks • Maximally : The global hackathon league")

    return embed

def team_info_embed(team_info):
    owner_name = team_info.get('owner_name', team_info['owner'])
    
    embed = create_embed(
        f"Team: {team_info['name']}",
        f"Invite Code: `{team_info['code']}`\nOwner: {owner_name}",
        discord.Color.blue()
    )
    
    if team_info['members']:
        members_list = "\n".join([f"• {member}" for member in team_info['members']])
        embed.add_field(
            name=f"Members ({len(team_info['members'])})",
            value=members_list,
            inline=False
        )
    else:
        embed.add_field(
            name="Members",
            value="No members yet",
            inline=False
        )
    
    return embed    