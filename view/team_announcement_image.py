"""
Team Announcement Image Generator Module

This module provides functionality to generate visual team announcements for esports matches.
It creates stylized images showing team matchups with player information and role assignments.

Features:
- Creates visually appealing team matchup images
- Downloads required fonts if not available
- Uses custom background image
- Displays player information and roles clearly
"""

import os
from PIL import Image, ImageDraw, ImageFont
import pathlib
from config import settings
from datetime import datetime

# Define file paths for resources
BASE_DIR = pathlib.Path(__file__).parent.parent
BACKGROUND_PATH = BASE_DIR / "common" / "images" / "background.png"
FONTS_DIR = BASE_DIR / "view" / "fonts"
OUTPUT_DIR = BASE_DIR / "temp"

# Ensure directories exist
try:
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create fonts directory if it doesn't exist - this is important since we store our fonts here
    os.makedirs(FONTS_DIR, exist_ok=True)
    print(f"Directories created or verified: {FONTS_DIR}, {OUTPUT_DIR}")
except (PermissionError, OSError) as e:
    print(f"Warning: Could not create required directories: {e}")
    # Use a temporary directory that should be writable
    import tempfile
    OUTPUT_DIR = pathlib.Path(tempfile.gettempdir())

# Default font paths - these will be checked and downloaded if needed
DEFAULT_BOLD_FONT = FONTS_DIR / "Roboto-Bold.ttf"
DEFAULT_REGULAR_FONT = FONTS_DIR / "Roboto-Regular.ttf"

# Color definitions - more professional palette
TEAM1_COLOR = (65, 105, 225)      # Royal Blue
TEAM2_COLOR = (220, 20, 60)       # Crimson
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (40, 40, 40)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Background gradient colors (fallback if background image not found)
BACKGROUND_TOP = (15, 15, 25)      # Dark blue-black
BACKGROUND_BOTTOM = (40, 40, 60)   # Slightly lighter blue-black

# Role colors - more vibrant professional colors
ROLE_COLORS = {
    "top": (220, 55, 55),           # Refined red
    "jungle": (50, 180, 80),        # Forest green
    "mid": (255, 200, 40),          # Golden yellow
    "bottom": (40, 120, 240),       # Deep blue
    "support": (170, 60, 220),      # Royal purple
    "tbd": (180, 180, 180),         # Gray
    "forced": (40, 40, 40)          # Dark gray
}

def check_bundled_fonts():
    """Check for bundled fonts in the repository"""
    global DEFAULT_BOLD_FONT, DEFAULT_REGULAR_FONT
    
    # Use the fonts bundled with the repository
    bold_font_path = FONTS_DIR / "Roboto-Bold.ttf"
    regular_font_path = FONTS_DIR / "Roboto-Regular.ttf"
    
    if bold_font_path.exists() and regular_font_path.exists():
        DEFAULT_BOLD_FONT = str(bold_font_path)
        DEFAULT_REGULAR_FONT = str(regular_font_path)
        print(f"Using bundled Roboto fonts from {FONTS_DIR}")
        return True
    else:
        print(f"Warning: Expected bundled fonts not found in {FONTS_DIR}")
        print(f"Make sure Roboto-Bold.ttf and Roboto-Regular.ttf are in the view/fonts directory")
        return False

def get_role_icon(role):
    """Return a text representation of the role icon"""
    role = role.lower()
    icon_map = {
        "top": "🟥",
        "jungle": "🟩",
        "mid": "🟨",
        "bottom": "🟦",
        "support": "🟪",
        "tbd": "⬜",
        "forced": "⬛"
    }
    return icon_map.get(role, "⬜")

def create_gradient_background(width, height, top_color, bottom_color):
    """
    Creates a gradient background image (fallback if background.png not found)
    
    Args:
        width: Image width
        height: Image height
        top_color: RGB color tuple for top
        bottom_color: RGB color tuple for bottom
        
    Returns:
        Image: PIL image with gradient background
    """
    # Create a new image
    bg = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(bg)
    
    # Draw gradient (divide into multiple bands for smoother gradient)
    num_bands = 100
    for i in range(num_bands):
        y0 = int(i * height / num_bands)
        y1 = int((i + 1) * height / num_bands)
        
        # Calculate interpolated color
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * i / num_bands)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * i / num_bands)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * i / num_bands)
        
        # Draw rectangle for this band
        draw.rectangle([(0, y0), (width, y1)], fill=(r, g, b))
    
    return bg

def create_team_matchup_image(match_id, team1_players, team2_players):
    """
    Create a stylized image showing the team matchups
    
    Args:
        match_id: The match ID
        team1_players: List of player dictionaries for team 1 with assigned_role
        team2_players: List of player dictionaries for team 2 with assigned_role
        
    Returns:
        str: Path to the created image
    """
    # Check for bundled fonts
    print("Checking for bundled fonts...")
    have_custom_fonts = check_bundled_fonts()
    
    # Debug font paths
    print(f"Font detection results:")
    print(f"  Bundled fonts available: {have_custom_fonts}")
    print(f"  Bold font path: {DEFAULT_BOLD_FONT}")
    print(f"  Regular font path: {DEFAULT_REGULAR_FONT}")
    
    # Image dimensions - use standard 1080p size
    width = 1920
    height = 1080
    
    # Load the background image
    try:
        if BACKGROUND_PATH.exists():
            img = Image.open(BACKGROUND_PATH)
            # Ensure the background is the right size
            if img.size != (width, height):
                # Check if LANCZOS is available (Pillow versions may differ)
                resize_method = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
                img = img.resize((width, height), resize_method)
                
            # Convert to RGB mode to prevent color mode mixing issues
            if img.mode != 'RGB':
                print(f"Converting background from {img.mode} to RGB mode")
                img = img.convert('RGB')
        else:
            # Fallback to generated gradient if background image doesn't exist
            print("Background image not found, generating gradient...")
            img = create_gradient_background(width, height, BACKGROUND_TOP, BACKGROUND_BOTTOM)
    except Exception as e:
        print(f"Error loading background image: {e}, falling back to gradient")
        img = create_gradient_background(width, height, BACKGROUND_TOP, BACKGROUND_BOTTOM)
    
    draw = ImageDraw.Draw(img)
    
    # Create a subtle footer for match ID and date
    footer_height = 60
    # Check image mode and create footer with same mode
    if img.mode == 'RGB':
        # For RGB images, create an RGB footer with solid color
        footer_overlay = Image.new('RGB', (width, footer_height), BLACK)
        img.paste(footer_overlay, (0, height - footer_height))
    else:
        # For RGBA images, we can use transparency
        footer_overlay = Image.new('RGBA', (width, footer_height), (*BLACK, 150))
        img.paste(footer_overlay, (0, height - footer_height), footer_overlay)
    
    # Load fonts for text rendering
    try:
        if have_custom_fonts:
            print("Loading fonts with specified sizes...")
            # Using our bundled Roboto fonts with moderate sizing
            title_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 96)
            header_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 72)
            player_name_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 40)
            detail_font = ImageFont.truetype(str(DEFAULT_REGULAR_FONT), 40)
            role_font = ImageFont.truetype(str(DEFAULT_BOLD_FONT), 40)
            footer_font = ImageFont.truetype(str(DEFAULT_REGULAR_FONT), 36)
            print("Successfully loaded all fonts")
        else:
            # Only as a last resort, use default fonts
            print("Warning: Bundled fonts not found, using default fonts (text sizing won't work)")
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            player_name_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
            role_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
    except Exception as e:
        print(f"Error loading fonts: {e}")
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        player_name_font = ImageFont.load_default()
        detail_font = ImageFont.load_default()
        role_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()
    
    # Draw match heading
    match_id_clean = match_id.replace('match_', '')

    # Draw team headers with fancy styling
    team1_x = width // 4
    team2_x = width - (width // 4)
    
    # Team 1 Header - use larger font
    team1_text = "BLUE TEAM"
    draw.text((team1_x, 170), team1_text, fill=TEAM1_COLOR, font=title_font, anchor="mm")
    
    # Team 2 Header - use larger font
    team2_text = "RED TEAM"
    draw.text((team2_x, 170), team2_text, fill=TEAM2_COLOR, font=title_font, anchor="mm")
    
    # Simple VS text in center
    draw.text((width // 2, 170), "VS", fill=WHITE, font=title_font, anchor="mm")
    
    # Get standard roles to ensure order
    standard_roles = ["top", "jungle", "mid", "bottom", "support"]
    
    # Group players by role
    team1_by_role = {}
    for player in team1_players:
        role = player.get('assigned_role', 'tbd').lower()
        team1_by_role[role] = player
    
    team2_by_role = {}
    for player in team2_players:
        role = player.get('assigned_role', 'tbd').lower()
        team2_by_role[role] = player
    
    # Draw player matchups by role
    for i, role in enumerate(standard_roles):
        y_position = 300 + (i * 140)  # Standard spacing for normal card sizes
        
        # Draw role indicator in center
        role_color = ROLE_COLORS.get(role, GRAY)
        circle_radius = 35
        circle_x = width // 2
        circle_y = y_position
        
        # Draw circle background - handle RGB mode
        if img.mode == 'RGB':
            # In RGB mode, just use solid colors
            draw.ellipse([(circle_x - circle_radius, circle_y - circle_radius), 
                        (circle_x + circle_radius, circle_y + circle_radius)], 
                      fill=role_color, outline=WHITE, width=5)
        else:
            # In RGBA mode, we can use full features
            draw.ellipse([(circle_x - circle_radius, circle_y - circle_radius), 
                        (circle_x + circle_radius, circle_y + circle_radius)], 
                      fill=role_color, outline=WHITE, width=3)
        
        # Draw role text
        role_display = role[0].upper()  # Just first letter
        draw.text((circle_x, circle_y), role_display,
                fill=WHITE, font=role_font, anchor="mm")
        
        # Draw small role name below icon
        role_name = role.upper()
        draw.text((circle_x, circle_y + circle_radius + 35), role_name,
                fill=WHITE, font=footer_font, anchor="mm")
        
        # Draw team 1 player
        team1_player = team1_by_role.get(role)
        if team1_player:
            player_name = team1_player.get('game_name', 'Unknown')
            tier = team1_player.get('tier', 'unknown').capitalize()
            rank = team1_player.get('rank', '')
            
            # Draw player card background - standard size
            card_width = 400
            card_height = 100
            card_x = team1_x - (card_width // 2)
            card_y = y_position - (card_height // 2)
            
            # Create player card overlay compatible with the image mode
            if img.mode == 'RGB':
                # For RGB images, use a solid but darker version of the team color
                darker_color = tuple(int(c * 0.4) for c in TEAM1_COLOR)  # 40% brightness
                player_card = Image.new('RGB', (card_width, card_height), darker_color)
                img.paste(player_card, (card_x, card_y))
            else:
                # For RGBA images, we can use transparency
                player_card = Image.new('RGBA', (card_width, card_height), (*TEAM1_COLOR, 40))
                img.paste(player_card, (card_x, card_y), player_card)
            
            # Draw clean card border (use solid color for RGB mode)
            if img.mode == 'RGB':
                draw.rectangle([(card_x, card_y), (card_x + card_width, card_y + card_height)], 
                            outline=TEAM1_COLOR, width=3)
            else:
                draw.rectangle([(card_x, card_y), (card_x + card_width, card_y + card_height)], 
                            outline=(*TEAM1_COLOR, 180), width=3)
            
            # Simple player name rendering - draw with a larger font
            draw.text((team1_x, y_position - 20), player_name,
                    fill=TEAM1_COLOR, font=player_name_font, anchor="mm")
            
            # Player rank - using regular detail font
            draw.text((team1_x, y_position + 25), f"{tier} {rank}",
                    fill=WHITE, font=detail_font, anchor="mm")
        
        # Draw team 2 player
        team2_player = team2_by_role.get(role)
        if team2_player:
            player_name = team2_player.get('game_name', 'Unknown')
            tier = team2_player.get('tier', 'unknown').capitalize()
            rank = team2_player.get('rank', '')
            
            # Draw player card background - standard size
            card_width = 400
            card_height = 100
            card_x = team2_x - (card_width // 2)
            card_y = y_position - (card_height // 2)
            
            # Create player card overlay compatible with the image mode
            if img.mode == 'RGB':
                # For RGB images, use a solid but darker version of the team color
                darker_color = tuple(int(c * 0.4) for c in TEAM2_COLOR)  # 40% brightness
                player_card = Image.new('RGB', (card_width, card_height), darker_color)
                img.paste(player_card, (card_x, card_y))
            else:
                # For RGBA images, we can use transparency
                player_card = Image.new('RGBA', (card_width, card_height), (*TEAM2_COLOR, 40))
                img.paste(player_card, (card_x, card_y), player_card)
            
            # Draw clean card border (use solid color for RGB mode)
            if img.mode == 'RGB':
                draw.rectangle([(card_x, card_y), (card_x + card_width, card_y + card_height)], 
                            outline=TEAM2_COLOR, width=3)
            else:
                draw.rectangle([(card_x, card_y), (card_x + card_width, card_y + card_height)], 
                            outline=(*TEAM2_COLOR, 180), width=3)
            
            # Simple player name rendering - draw with a larger font
            draw.text((team2_x, y_position - 20), player_name,
                    fill=TEAM2_COLOR, font=player_name_font, anchor="mm")
            
            # Player rank - using regular detail font
            draw.text((team2_x, y_position + 25), f"{tier} {rank}",
                    fill=WHITE, font=detail_font, anchor="mm")
    
    # Add match ID to bottom left
    draw.text((30, height - 30), f"Match ID: {match_id_clean}",
            fill=GRAY, font=footer_font, anchor="lm")
    
    # Add timestamp to bottom right
    timestamp = datetime.now().strftime("%Y-%m-%d")
    draw.text((width - 30, height - 30), timestamp,
            fill=GRAY, font=footer_font, anchor="rm")
    
    # Save the image with better quality
    try:
        # Try to use the defined output directory
        img_path = OUTPUT_DIR / f"match_{match_id}_teams.png"
        img.save(img_path, quality=95, optimize=True)
    except (PermissionError, OSError) as e:
        # If saving fails due to permission error, try using the system temp directory
        print(f"Warning: Could not save to {img_path}: {e}")
        import tempfile
        tmp_dir = pathlib.Path(tempfile.gettempdir())
        img_path = tmp_dir / f"match_{match_id}_teams.png"
        img.save(img_path, quality=95, optimize=True)
        
    return str(img_path)


def create_role_matchup_image(match_id, team1_players, team2_players):
    """
    Create a more detailed role matchup image
    
    Args:
        match_id: The match ID
        team1_players: List of player dictionaries for team 1 with assigned_role
        team2_players: List of player dictionaries for team 2 with assigned_role
        
    Returns:
        str: Path to the created image
    """
    # This just calls the standard image generation
    try:
        return create_team_matchup_image(match_id, team1_players, team2_players)
    except Exception as e:
        # Log error but don't crash
        print(f"Error in create_role_matchup_image: {e}")
        # Return None or use a fallback image
        return None


# Simple test function if this file is run directly
if __name__ == "__main__":
    # Create sample team data for testing
    team1 = [
        {"user_id": 1, "game_name": "BluePlayer1", "assigned_role": "top", "tier": "diamond", "rank": "II"},
        {"user_id": 2, "game_name": "BluePlayer2", "assigned_role": "jungle", "tier": "platinum", "rank": "I"},
        {"user_id": 3, "game_name": "BluePlayer3", "assigned_role": "mid", "tier": "gold", "rank": "IV"},
        {"user_id": 4, "game_name": "BluePlayer4", "assigned_role": "bottom", "tier": "silver", "rank": "III"},
        {"user_id": 5, "game_name": "BluePlayer5", "assigned_role": "support", "tier": "platinum", "rank": "II"}
    ]
    
    team2 = [
        {"user_id": 6, "game_name": "RedPlayer1", "assigned_role": "top", "tier": "platinum", "rank": "III"},
        {"user_id": 7, "game_name": "RedPlayer2", "assigned_role": "jungle", "tier": "diamond", "rank": "IV"},
        {"user_id": 8, "game_name": "RedPlayer3", "assigned_role": "mid", "tier": "platinum", "rank": "II"},
        {"user_id": 9, "game_name": "RedPlayer4", "assigned_role": "bottom", "tier": "diamond", "rank": "I"},
        {"user_id": 10, "game_name": "RedPlayer5", "assigned_role": "support", "tier": "gold", "rank": "II"}
    ]
    
    # Generate a test image
    output_path = create_team_matchup_image("test_123", team1, team2)
    print(f"Test image created at: {output_path}")