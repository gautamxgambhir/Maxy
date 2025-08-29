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