import discord
import time
import os
import json
from config import settings

logger = settings.logging.getLogger("discord")

class Details_Cached:

    # max_cache_idle_time = 3600
    cached_info = "cached_details.json"
    
    @staticmethod
    async def load_cache():

        if os.path.exists(Details_Cached.cached_info):
            try:
                with open(Details_Cached.cached_info, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except Exception as ex:
                print(f"error reading files {ex}")
        return {}
    
    def save_cache(cached_file):
        with open(Details_Cached.cached_info, 'w', encoding='utf-8') as file:
            json.dump(cached_file, file, ensure_ascii=False)

    @staticmethod
    async def get_channel_id(channelName, guild_id):
        channel_lists = await Details_Cached.load_cache()

        if str(guild_id) in channel_lists:
            for i in channel_lists[str(guild_id)]:
                if channelName in i:
                    value = i[channelName]
                    logger.info(f"channel id is {value}")
                    return value
    @staticmethod
    async def isChannelNotCreated(ch_config, guild, cachedChListsDic) -> bool:

        if str(guild.id) in cachedChListsDic:

            for channel in cachedChListsDic[str(guild.id)]:
                for cha_name, cha_id in channel.items():
                    ch = guild.get_channel(cha_id)
                    if ch:
                        continue
                    return True
            return False
        else:
            return True

    async def channels_for_tournament(ch_config, guild):
        object = Details_Cached()
        cachedChListsDic = await Details_Cached.load_cache()
        isChannelCreated : bool = await object.isChannelNotCreated(ch_config, guild, cachedChListsDic)

        if isChannelCreated:
            cachedChListsDic[str(guild.id)] = []
            
            try:
                # Try to parse as JSON first
                channel_config = json.loads(ch_config)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, provide a default channel configuration
                logger.warning(f"Failed to parse CHANNEL_CONFIG as JSON. Using default configuration.")
                # Try to find an admin role in the guild
                admin_roles = ["Admin", "Administrator", "Mod", "Moderator"]
                admin_role_name = "Admin"  # Default
                for role_name in admin_roles:
                    if discord.utils.get(guild.roles, name=role_name):
                        admin_role_name = role_name
                        break
                
                # Use found admin role or create configuration with just @everyone
                channel_config = {
                    "Tournament": {
                        "announcements": {"admin": admin_role_name, "everyone": "@everyone"},
                        "registration": {"everyone": "@everyone"},
                        "team-info": {"everyone": "@everyone"},
                        "results": {"everyone": "@everyone"},
                        "admin": {"admin": admin_role_name}
                    }
                }

            for category_name, channelList in channel_config.items():
                category = discord.utils.get(guild.categories, name=category_name)
                if not category:
                    category = await guild.create_category(category_name)

                    for channel_name, roles in channelList.items():

                        if(channel_name.lower() == settings.PRIVATE_CH.lower()):
                            # Create permission overwrites dictionary
                            overwrites = {
                                guild.default_role: discord.PermissionOverwrite(view_channel=False)
                            }
                            
                            # Add role permissions only for roles that exist
                            for key, role_name in roles.items():
                                # Check for '@everyone' special case
                                if role_name == "@everyone":
                                    overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=True)
                                else:
                                    # Try to find the role by name
                                    role = discord.utils.get(guild.roles, name=role_name)
                                    # Also try to find by case-insensitive search if needed
                                    if not role:
                                        for server_role in guild.roles:
                                            if server_role.name.lower() == role_name.lower():
                                                role = server_role
                                                break
                                
                                    if role:  # Only add if role exists
                                        overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                                    else:
                                        logger.warning(f"Role '{role_name}' not found in guild '{guild.name}'. Skipping permission for this role.")
                            
                            # Debug log to show what permissions will be used
                            logger.info(f"Creating private channel '{channel_name}' with permissions: {[role.name if hasattr(role, 'name') else 'default' for role in overwrites.keys()]}")
                            
                            # Create the channel with valid overwrites
                            channel = await guild.create_text_channel(
                                channel_name,
                                category=category,
                                overwrites=overwrites
                            )
                            
                            cachedChListsDic[str(guild.id)].append({channel_name : channel.id})
                        
                        else:
                            # First create the channel
                            channel = await guild.create_text_channel(channel_name, category=category)
                            cachedChListsDic[str(guild.id)].append({channel_name : channel.id})
                            
                            logger.info(f"Created channel '{channel_name}' in category '{category_name}'")
                
                            # Then set permissions for the channel
                            for key, role_name in roles.items():
                                if role_name == "@everyone":
                                    # Handle @everyone role specially
                                    await channel.set_permissions(guild.default_role, read_messages=True)
                                    logger.info(f"Set permissions for @everyone in '{channel_name}'")
                                else:
                                    # Try to find role by exact name
                                    discord_role = discord.utils.get(guild.roles, name=role_name)
                                    
                                    # If not found, try case-insensitive search
                                    if not discord_role:
                                        for server_role in guild.roles:
                                            if server_role.name.lower() == role_name.lower():
                                                discord_role = server_role
                                                break
                                    
                                    # Check if role exists before setting permissions
                                    if discord_role:
                                        await channel.set_permissions(discord_role, read_messages=True)
                                        logger.info(f"Set permissions for role '{discord_role.name}' in '{channel_name}'")
                                    else:
                                        logger.warning(f"Role '{role_name}' not found in guild '{guild.name}'. Channel created with default permissions.")

        
            Details_Cached.save_cache(cachedChListsDic)
