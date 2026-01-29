"""
Unified configuration management module for Elysium Discord Bot.

This module provides a centralized way to load and access configuration
from config.json with caching and validation.
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for loaded config
_config_cache: Optional[Dict[str, Any]] = None
_config_path: Optional[str] = None


def get_config_path() -> str:
    """
    Get the absolute path to the config.json file.
    
    Returns:
        str: Absolute path to config.json
        
    Raises:
        FileNotFoundError: If config.json cannot be found
    """
    global _config_path
    
    if _config_path:
        return _config_path
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Try multiple possible locations
    possible_paths = [
        script_dir / "config.json",
        script_dir.parent / "config.json",
        Path("config.json").absolute(),
        Path("./config.json").absolute(),
    ]
    
    for path in possible_paths:
        if path.exists():
            _config_path = str(path)
            logger.info(f"Found config at: {_config_path}")
            return _config_path
    
    raise FileNotFoundError(
        f"Could not find config.json in any of the expected locations: "
        f"{[str(p) for p in possible_paths]}"
    )


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load configuration from config.json file with caching.
    
    Args:
        force_reload: If True, reload config from disk even if cached
        
    Returns:
        dict: Configuration dictionary
        
    Raises:
        FileNotFoundError: If config.json cannot be found
        json.JSONDecodeError: If config.json is not valid JSON
    """
    global _config_cache
    
    if _config_cache is not None and not force_reload:
        return _config_cache
    
    config_path = get_config_path()
    
    try:
        with open(config_path, encoding='utf-8') as config_file:
            _config_cache = json.load(config_file)
            logger.info(f"Successfully loaded config from: {config_path}")
            return _config_cache
    except FileNotFoundError:
        logger.error(f"Config file not found at: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        raise


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to config.json file.
    
    Args:
        config: Configuration dictionary to save
        
    Raises:
        IOError: If config file cannot be written
    """
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(config, config_file, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved config to: {config_path}")
        
        # Update cache
        global _config_cache
        _config_cache = config
    except IOError as e:
        logger.error(f"Error saving config file: {e}")
        raise


def get_bot_config() -> Dict[str, Any]:
    """
    Get bot-specific configuration.
    
    Returns:
        dict: Bot configuration section
    """
    config = load_config()
    return config.get("bot", {})


def get_twitch_config() -> Dict[str, Any]:
    """
    Get Twitch-specific configuration.
    
    Returns:
        dict: Twitch configuration section
    """
    config = load_config()
    return config.get("twitch", {})


def get_moderation_config() -> Dict[str, Any]:
    """
    Get moderation-specific configuration.
    
    Returns:
        dict: Moderation configuration section
    """
    config = load_config()
    return config.get("moderation", {})


def reload_config() -> Dict[str, Any]:
    """
    Force reload configuration from disk.
    
    Returns:
        dict: Reloaded configuration dictionary
    """
    return load_config(force_reload=True)
