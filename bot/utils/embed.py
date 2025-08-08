import discord
from config import Config

def create_embed(title, description, color=discord.Color.blue()):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if Config.MAXIMALLY_LOGO_URL:
        embed.set_thumbnail(url=Config.MAXIMALLY_LOGO_URL)
    embed.set_footer(text="Maximally Hackers Network")
    return embed

def profile_embed(profile):
    embed = create_embed(
        f"Profile: {profile['name']}",
        f"Discord: {profile['discord_username']}",
        discord.Color.green()
    )
    if profile['skills']:
        embed.add_field(name="Skills", value=profile['skills'], inline=False)
    if profile['interests']:
        embed.add_field(name="Interests", value=profile['interests'], inline=False)
    return embed

def search_results_embed(results):
    embed = create_embed(
        "🔍 Hackers Search Results",
        f"Found {len(results)} matching profiles:",
        discord.Color.blue()
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