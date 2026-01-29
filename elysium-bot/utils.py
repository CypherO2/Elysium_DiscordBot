"""
Utility functions for Elysium Discord Bot.
"""
import logging
from typing import Optional
import discord

logger = logging.getLogger(__name__)


def validate_channel_id(channel_id: str) -> Optional[int]:
    """
    Validate and extract channel ID from Discord channel mention or ID string.
    
    Args:
        channel_id: Channel mention (e.g., "<#123456>") or ID string
        
    Returns:
        int: Channel ID if valid, None otherwise
    """
    try:
        # Remove Discord mention formatting
        cleaned = channel_id.replace("<#", "").replace(">", "").strip()
        return int(cleaned)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid channel ID format: {channel_id}")
        return None


def get_channel_safely(bot: discord.Client, channel_id: int) -> Optional[discord.TextChannel]:
    """
    Safely get a channel by ID, returning None if not found.
    
    Args:
        bot: Discord bot client
        channel_id: Channel ID to retrieve
        
    Returns:
        Optional[discord.TextChannel]: Channel if found, None otherwise
    """
    try:
        channel = bot.get_channel(channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            return channel
        return None
    except Exception as e:
        logger.error(f"Error getting channel {channel_id}: {e}")
        return None
