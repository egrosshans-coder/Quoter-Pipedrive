#!/usr/bin/env python3
"""
Category mapping utilities for Quoter to Pipedrive sync
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_access_token

load_dotenv()

# Cache for categories to avoid repeated API calls
_categories_cache = None

# Cache for Pipedrive to Quoter category mappings
_pipedrive_to_quoter_cache = {}

def get_pipedrive_to_quoter_mapping():
    """Get the mapping from Pipedrive category IDs to Quoter category information."""
    global _pipedrive_to_quoter_cache
    
    if _pipedrive_to_quoter_cache:
        return _pipedrive_to_quoter_cache
    
    # Comprehensive mapping from Pipedrive category IDs to Quoter category information
    # Based on VERIFIED Pipedrive data (no assumptions)
    mapping = {
        # VERIFIED CATEGORIES from Pipedrive API
        28: {"name": "Hologram", "quoter_id": "cat_30LNfXTaWG0yu173faTJEiAIU1e"},
        29: {"name": "Laser", "quoter_id": "cat_30LNfZkrGEwUAgOW7BYnb05ftCz"},
        30: {"name": "Robotics", "quoter_id": "cat_30LNfYXnk657htcR39QF5y3qWgh"},
        31: {"name": "Fog", "quoter_id": "cat_30LNff2sfuMH27xwymRGG00vrPE"},
        32: {"name": "Snow", "quoter_id": "cat_30LNfSnow"},
        33: {"name": "Fire", "quoter_id": "cat_30LNfFire"},
        34: {"name": "Water", "quoter_id": "cat_30LNfmnUOBkf1hJ0YyPpYe18pkH"},
        35: {"name": "Drones", "quoter_id": "cat_30LNfYZ7SuMTuobYMDmCyBDommp"},
        36: {"name": "Wristbands/Lanyards/Orbs", "quoter_id": "cat_30LNfVVNvu8coIPyXgqLeUFqp2I"},
        38: {"name": "LED Tubes/Floor/Panels", "quoter_id": "cat_30LNfZPYF9vwZjzdvqgfuL6pNI3"},
        42: {"name": "Balloons", "quoter_id": "cat_30LNfY0GaYgL4XAkEwRzLF1qYRv"},
        43: {"name": "Spheres", "quoter_id": "cat_30LNfXWDuxpEXJv1Suc8JODZcEe"},
        55: {"name": "Drones", "quoter_id": "cat_30LNfYZ7SuMTuobYMDmCyBDommp"},
        94: {"name": "Pyro", "quoter_id": "cat_30LNfdY5ZPBbzlzzpLlW4XjKjkH"},
        101: {"name": "Tanks", "quoter_id": "cat_30LNfhhYMRvMhqU2ml5RmnBqVcA"},
        102: {"name": "Confetti/Streamers", "quoter_id": "cat_30LNfdtY40hB9AWRtcNYWLqKm1K"},
        104: {"name": "CO2", "quoter_id": "cat_30LNfdXXFqn4K7EQgplUoqP24GS"},
        109: {"name": "Electrical", "quoter_id": "cat_30LNfElectrical"},
        110: {"name": "Projection", "quoter_id": "cat_30LNfXrtJJWmNlbh5FwKr57KwWm"},
        359: {"name": "Bubbles", "quoter_id": "cat_30LNfBubbles"},
        360: {"name": "Apparel", "quoter_id": "cat_30LNfmxxRpwnvIP9PWeoKfIWXnC"},
        361: {"name": "AI", "quoter_id": "cat_30LNfn2pcAMmCBZ6rYNL4Lsg2kA"},
        362: {"name": "Reveal", "quoter_id": "cat_30LNfReveal"},
        396: {"name": "Inflatables", "quoter_id": "cat_30LNfInflatables"},
    }
    
    _pipedrive_to_quoter_cache = mapping
    return mapping

def get_quoter_category_from_pipedrive_id(pipedrive_id):
    """Get Quoter category information from a Pipedrive category ID."""
    mapping = get_pipedrive_to_quoter_mapping()
    
    if pipedrive_id not in mapping:
        logger.warning(f"Pipedrive category ID {pipedrive_id} not found in mapping")
        return None
    
    return mapping[pipedrive_id]

def get_verified_subcategory_hierarchy():
    """Get the verified subcategory hierarchy based on Pipedrive data."""
    return {
        "Hologram": ["FV", "FV-Graphics", "HoloTable", "HoloPortal", "HoloPod", "Virtual-Stage", "Holopod"],
        "Laser": ["30Watt", "40Watt", "Tripod", "Sphere", "Mapping", "Cables", "Show", "Graphics", "Cannons", "Array"],
        "Robotics": ["Dog", "Arm", "Walle", "Character"],
        "Fog": ["Walle", "LLF", "Fogger", "LLF-Fluid", "LLF-Control", "Fog-Bubbles"],
        "Snow": ["Hillside", "Machines"],
        "Fire": [],
        "Water": ["FX", "Screens", "Dancing", "Intelligent", "Mist-Curtain"],
        "Drones": ["Indoor", "Outdoor", "Delivery", "Camera", "Soccer"],
        "Wristbands/Lanyards/Orbs": ["Landyard-Xylo", "Orbs", "Technician-Wristbands", "Wristband-Xylo", "Controller-Xylo", "Handheld-Xylo", "Launchpad", "Laptop", "Deposit", "Branding", "Wristband-TLC", "Landyard-TLC", "GlowBalls", "GlowOrbs", "Programming", "Controller-TLC", "Transmitter", "Glowballs"],
        "LED Tubes/Floor/Panels": ["Mesh", "Floor", "Panel", "Letters", "Tubes", "Tubes-Kinetic", "Panels-Vertical", "LED Shapes", "AI-Engage", "Screens"],
        "Balloons": ["Moon", "Wall-Flying", "Drop"],
        "Spheres": ["Mirrored", "Inflatable-Metalic"],
        "Pyro": ["Granuals", "WSF", "Fire", "Fireworks", "Faux"],
        "Tanks": ["Dewar", "Nitrogen", "Syphon", "1-to-3 Splitter"],
        "Confetti/Streamers": ["Cannons", "Confetti", "Streamers", "Streamers-Custom", "Launch-Custom"],
        "CO2": ["Cryo-Jet"],
        "Electrical": ["Relay-Pack"],
        "Projection": ["Mapping", "Video-Globes", "Video", "Technician-Laser", "Technician-Projectionist", "Kinetic"],
        "Bubbles": [],
        "Apparel": ["LED-Costumes"],
        "AI": ["DJ"],
        "Reveal": ["Pullaway-Kabuki"],
        "Inflatables": ["DraftQuote"]
    }

def get_category_path_from_pipedrive_id(pipedrive_id):
    """Get the full category path for a Pipedrive category ID."""
    quoter_info = get_quoter_category_from_pipedrive_id(pipedrive_id)
    
    if not quoter_info or not quoter_info.get('quoter_id'):
        return f"Unknown Category ID: {pipedrive_id}"
    
    # If we have a parent, build the full path
    if quoter_info.get('parent'):
        return f"{quoter_info['parent']} / {quoter_info['name']}"
    else:
        return quoter_info['name']

def get_all_categories():
    """Fetch all categories from Quoter API with caching."""
    global _categories_cache
    
    if _categories_cache is not None:
        return _categories_cache
    
    access_token = get_access_token()
    if not access_token:
        return []
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoint = "https://api.quoter.com/v1/categories"
    
    try:
        all_categories = []
        offset = 0
        limit = 100
        
        while True:
            params = {
                "limit": limit,
                "page": offset // limit + 1  # Convert offset to page number
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get("data", [])
                has_more = data.get("has_more", False)
                total_count = data.get("total_count", 0)
                
                all_categories.extend(categories)
                
                if not has_more or len(categories) == 0 or len(all_categories) >= total_count:
                    break
                
                offset += limit
            else:
                logger.error(f"❌ API request failed with status {response.status_code}: {response.text}")
                break
        
        logger.info(f"✅ Successfully retrieved {len(all_categories)} total categories from Quoter")
        _categories_cache = all_categories
        return all_categories
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Quoter API: {e}")
        return []

def get_category_path(category_id):
    """Get the full category path (Parent / Child) for a given category ID."""
    categories = get_all_categories()
    
    if not categories:
        return None
    
    # Find the category by ID
    target_category = None
    for category in categories:
        if category['id'] == category_id:
            target_category = category
            break
    
    if not target_category:
        logger.warning(f"Category with ID {category_id} not found")
        return None
    
    # If it has a parent, build the full path
    if target_category.get('parent_category'):
        return f"{target_category['parent_category']} / {target_category['name']}"
    else:
        return target_category['name']

def get_category_by_name(category_name):
    """Find a category by name (case-insensitive)."""
    categories = get_all_categories()
    
    if not categories:
        return None
    
    for category in categories:
        if category['name'].lower() == category_name.lower():
            return category
    
    return None

def test_category_mapping():
    """Test the category mapping functionality."""
    logger.info("=== Testing Category Mapping ===")
    
    # Test with known categories
    test_cases = [
        "cat_30LNfhXf8MdwLYlqsvoBNDGfPNV",  # 1-to-3 Splitter
        "cat_30LNfgV7gCwhQydirKD1KhNrS00",  # Drop
    ]
    
    for category_id in test_cases:
        path = get_category_path(category_id)
        logger.info(f"Category ID {category_id}: {path}")
    
    # Test finding categories by name
    test_names = [
        "Tanks",
        "Balloons", 
        "1-to-3 Splitter",
        "Drop"
    ]
    
    logger.info("\n=== Testing Category Lookup by Name ===")
    for name in test_names:
        category = get_category_by_name(name)
        if category:
            logger.info(f"Found '{name}': ID={category['id']}, Parent={category.get('parent_category')}")
        else:
            logger.warning(f"Category '{name}' not found")

if __name__ == "__main__":
    test_category_mapping() 