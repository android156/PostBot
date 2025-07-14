"""
Utility functions for the Telegram bot.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def validate_city_name(city_name: str) -> bool:
    """
    Validate city name format.
    
    Args:
        city_name: City name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not city_name or len(city_name.strip()) < 2:
        return False
        
    # Check for obviously invalid patterns
    if re.search(r'^\d+$', city_name):  # Only digits
        return False
        
    if re.search(r'^[^a-zA-Zа-яА-Я]+$', city_name):  # No letters
        return False
        
    return True

def validate_weight(weight: int) -> bool:
    """
    Validate weight value.
    
    Args:
        weight: Weight in grams
        
    Returns:
        True if valid, False otherwise
    """
    return 0 < weight <= 50000  # 0g to 50kg

def format_weight(weight: int) -> str:
    """
    Format weight for display.
    
    Args:
        weight: Weight in grams
        
    Returns:
        Formatted weight string
    """
    if weight >= 1000:
        return f"{weight / 1000:.1f} кг"
    else:
        return f"{weight} г"

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram markdown.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    # Characters that need to be escaped in Telegram markdown
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
        
    return text

def parse_file_size(size_bytes: int) -> str:
    """
    Parse file size into human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def clean_phone_number(phone: str) -> Optional[str]:
    """
    Clean and validate phone number.
    
    Args:
        phone: Phone number string
        
    Returns:
        Cleaned phone number or None if invalid
    """
    if not phone:
        return None
        
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Russian phone number validation
    if len(digits) == 11 and digits.startswith('7'):
        return f"+{digits}"
    elif len(digits) == 10 and digits.startswith('9'):
        return f"+7{digits}"
    
    return None

def log_api_call(endpoint: str, params: dict, response_status: int):
    """
    Log API call details.
    
    Args:
        endpoint: API endpoint
        params: Request parameters
        response_status: HTTP response status
    """
    logger.info(f"API Call: {endpoint} | Status: {response_status} | Params: {len(params)} parameters")
