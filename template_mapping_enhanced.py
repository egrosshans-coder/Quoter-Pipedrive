#!/usr/bin/env python3
"""
Enhanced Template Mapping System
Based on webhook data analysis for comprehensive quote creation
"""

import requests

# Bundle 1: Template-Specific (Hardware + Labor) - Reduced Items
TEMPLATE_BUNDLES = {
    "floating-video": {
        "name": "Floating Video",
        "items": [
            # FV Category - Using ACTUAL Quoter Item Codes with simple categories (like Bundle 2)
            {"sku": "HG-FV-Graph-001", "name": "FV-Standard Graphics Pkg", "type": "FV-Graphics", "price": 500.00},
            {"sku": "HG-FV-Graph-002", "name": "FV-Advanced Graphics Pkg", "type": "FV-Graphics", "price": 1500.00},
            {"sku": "HG-FV-Graph-003", "name": "FV-Ultimate Graphics Pkg", "type": "FV-Graphics", "price": 3000.00},
            {"sku": "HG-FVH-L30-001", "name": "FV-30 Fan Holographic", "type": "FV", "price": 2500.00},
            {"sku": "HG-FVH-M22-001", "name": "FV-22 Fan Holographic", "type": "FV", "price": 2000.00},
            {"sku": "HG-FVV-100-001", "name": "FV-40in-100 Fan Holographic", "type": "FV", "price": 3000.00},
            {"sku": "HG-FVV-150-001", "name": "FV-5FT-150 Fan Holographic", "type": "FV", "price": 4000.00},
            {"sku": "HG-FVV-180-001", "name": "FV-6FT-180 Fan Holographic", "type": "FV", "price": 6000.00},
            {"sku": "HG-FVV-MBOX-001", "name": "FVV-MasterBox", "type": "FV", "price": 1000.00},
            {"sku": "HG-FVH-MBOX-001", "name": "FV-MasterBox", "type": "FV", "price": 1000.00},
            {"sku": "HG-FVH-HH-001", "name": "FV-HoloHuman", "type": "FV", "price": 10000.00},
            {"sku": "HG-FVH-HH-002", "name": "FV-HoloHuman-Case", "type": "FV", "price": 2000.00},
            
            # Labor for this template
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00}
        ]
    },
    "led-wristbands": {
        "name": "LED Wristbands",
        "items": [
            # Wristbands Section
            {"sku": "LED-WBX-MK4-001", "name": "Xylo 8-LED Wristband", "type": "Wristbands", "price": 25.00},
            {"sku": "LED-WBX-MK5-001", "name": "Xylo 12-Led Wristband", "type": "Wristbands", "price": 35.00},
            {"sku": "LED-WBT-4LED-001", "name": "TLC 4-Led Wristband", "type": "Wristbands", "price": 22.00},
            {"sku": "LED-WBT-4LED-002", "name": "TLC 4-Led Wristband-NOButton", "type": "Wristbands", "price": 20.00},
            {"sku": "LED-WBT-2LED-001", "name": "TLC 2-Led Wristband", "type": "Wristbands", "price": 15.00},
            
            # Branding Section
            {"sku": "LED-WB-BRAND", "name": "Wristband Branding Options", "type": "Branding", "price": 50.00},
            
            # Control Systems Section
            {"sku": "LED-WBT-TX306-001", "name": "Controller-TLC-306-Pixel-Wristbands&Lanyards", "type": "Control Systems", "price": 400.00},
            {"sku": "LED-WBE-LAP", "name": "Laptop for Wristbands/Lanyards", "type": "Control Systems", "price": 600.00},
            {"sku": "LED-WBX-CTX", "name": "Controller-Xylobands-Wristbands/Lanyards", "type": "Control Systems", "price": 350.00},
            {"sku": "LED-WBE-LPAD", "name": "Launchpad for Wristbands/Lanyards", "type": "Control Systems", "price": 250.00},
            {"sku": "LED-WBE-HTX", "name": "Remote Control for Wristbands/Lanyards", "type": "Control Systems", "price": 300.00},
            {"sku": "LED-WB-HTX1", "name": "HTX Controller Refundable Deposit", "type": "Control Systems", "price": 1000.00},
            
            # Labor Section
            {"sku": "SVC-LAB-WBL", "name": "Labor-Wristband/Landyards", "type": "Labor", "price": 950.00},
            {"sku": "SVC-LAB-OVR", "name": "Labor Overtime & Per-Diem", "type": "Labor", "price": 500.00},
            {"sku": "SVC-TEC-002", "name": "Second Technician Option", "type": "Labor", "price": 750.00},
            {"sku": "SVC-PGM-WB-LY-001", "name": "Programming Standard for Wristbands& Lanyards", "type": "Labor", "price": 250.00},
            {"sku": "SVC-PGM-WB-LY-002", "name": "Programming Mid-Level for Wristbands& Lanyards", "type": "Labor", "price": 350.00},
            {"sku": "SVC-PGM-WB-LY-003", "name": "Programming Advanced for Wristbands& Lanyards", "type": "Labor", "price": 500.00}
        ]
    },
    "balloons": {
        "name": "Balloons",
        "items": [
            # Balloon hardware items
            {"sku": "BAL-FII-001", "name": "Balloon air filler", "type": "Balloons", "price": 150.00},
            {"sku": "BAL-DRP-001", "name": "Balloon drop net", "type": "Balloons", "price": 200.00},
            {"sku": "BAL-MOON-001", "name": "Balloon Moon LED", "type": "Balloons", "price": 500.00},
            {"sku": "BAL-PKG-001", "name": "Balloons per package", "type": "Balloons", "price": 75.00},
            {"sku": "BAL-WALL-001", "name": "Disappearing Balloon Wall", "type": "Balloons", "price": 800.00},
            {"sku": "BAL-FLY", "name": "Flying Balloon Wall", "type": "Balloons", "price": 1200.00},
            
            # Labor for this template
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00}
        ]
    },
    "co2-smoke-foggers": {
        "name": "CO2/Smoke/Upright Foggers",
        "items": [
            # CO2 Jets Section
            {"sku": "CO2-CRY-JET", "name": "Cryo Jet", "type": "CO2", "price": 250.00},
            {"sku": "FOG-FGR-001", "name": "Fogger", "type": "CO2", "price": 300.00},
            {"sku": "ELE-RLY-001", "name": "Relay Pack", "type": "CO2", "price": 150.00},
            
            # Tanks Section
            {"sku": "TNK-DEW-180", "name": "Tanks - Dewar Tall", "type": "Tanks", "price": 400.00},
            {"sku": "TNK-DEW-230", "name": "Tanks - Dewar CO2 - New Footprint", "type": "Tanks", "price": 450.00},
            {"sku": "TNK-CO2-SYP-001", "name": "CO2 Syphon Tank", "type": "Tanks", "price": 350.00},
            {"sku": "SVC-RPR-CO2", "name": "CO2 Jet Repair", "type": "Tanks", "price": 200.00},
            
            # Additional Items Section
            {"sku": "TNK-3SPL-001", "name": "3-to-1 splitter CO2", "type": "Additional", "price": 100.00},
            
            # Labor Section
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00},
            {"sku": "SVC-TEC-002", "name": "Second Technician Option", "type": "Labor", "price": 750.00},
            {"sku": "SVC-LAB-OVR", "name": "Labor Overtime & Per-Diem", "type": "Labor", "price": 500.00}
        ]
    },
    "confetti-streamers": {
        "name": "Confetti/Streamers",
        "items": [
            # Hardware Section
            {"sku": "CNF-CAN-001", "name": "Confetti/Streamer Cannons", "type": "Hardware", "price": 300.00},
            {"sku": "CNF-BLW-SS", "name": "Silent Storm Confetti Blowers - SS", "type": "Hardware", "price": 250.00},
            {"sku": "CNF-BLW-SST", "name": "Silent Storm Confetti Blowers - T", "type": "Hardware", "price": 275.00},
            {"sku": "CNF-BLW-001", "name": "Confetti Blower Rental (TBD)", "type": "Hardware", "price": 200.00},
            
            # Confetti/Streamers Section
            {"sku": "CNF-STR-001", "name": "Streamers", "type": "Confetti/Streamers", "price": 75.00},
            {"sku": "CNF-CNF-001", "name": "Confetti", "type": "Confetti/Streamers", "price": 50.00},
            {"sku": "CNF-STR-002", "name": "Custom Streamers", "type": "Confetti/Streamers", "price": 125.00},
            
            # Additional Items Section
            {"sku": "TNK-NIT-001", "name": "Nitrogen Tank", "type": "Additional", "price": 400.00},
            {"sku": "ELE-RLY-001", "name": "Relay Pack", "type": "Additional", "price": 150.00},
            {"sku": "CNF-LNCH-CUST-001", "name": "Confetti Custom Launch", "type": "Additional", "price": 175.00},
            
            # Labor Section
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00},
            {"sku": "SVC-TEC-002", "name": "Second Technician Option", "type": "Labor", "price": 750.00},
            {"sku": "SVC-LAB-OVR", "name": "Labor Overtime & Per-Diem", "type": "Labor", "price": 500.00}
        ]
    },
    "fireworks-pyro-fire": {
        "name": "Fireworks/Pyro/Fire",
        "items": [
            # Firework/Pyrotechnic display Section
            {"sku": "PYR-FIR-WRK-001", "name": "Fireworks", "type": "Firework/Pyrotechnic", "price": 1500.00},
            {"sku": "PYR-EFF-EST", "name": "Pyro effects - Estimate", "type": "Firework/Pyrotechnic", "price": 800.00},
            {"sku": "PYR-FLM-GEN", "name": "Pyro-Canister flame generator", "type": "Firework/Pyrotechnic", "price": 400.00},
            {"sku": "PYR-FLM-CAN", "name": "Pyro-Canister", "type": "Firework/Pyrotechnic", "price": 300.00},
            {"sku": "PYR-PRO-TNK", "name": "Pyro-Propane tank", "type": "Firework/Pyrotechnic", "price": 200.00},
            {"sku": "PYRO-FIR-REAL", "name": "Pyro-real fire", "type": "Firework/Pyrotechnic", "price": 600.00},
            
            # White sparkle fountains Section
            {"sku": "PYR-WSF-MOD-001", "name": "White Sparkle Fountain", "type": "White Sparkle Fountains", "price": 150.00},
            
            # Fire effects Section
            {"sku": "PYR-FAUX-001", "name": "Simulated Fire", "type": "Fire Effects", "price": 250.00},
            {"sku": "PYR-DRG-FLY", "name": "Pyro-Dragon fly", "type": "Fire Effects", "price": 180.00},
            {"sku": "PYR-FIR-FLY", "name": "Pyro-Firefly", "type": "Fire Effects", "price": 120.00},
            
            # Labor Section
            {"sku": "PYR-LIC-TEC", "name": "Pyro-Licensed pyrotechnician", "type": "Labor", "price": 1500.00},
            {"sku": "PYR-PRM-001", "name": "Pyro-permit", "type": "Labor", "price": 300.00},
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00},
            {"sku": "SVC-LAB-OVR", "name": "Labor Overtime & Per-Diem", "type": "Labor", "price": 500.00},
            {"sku": "SVC-LAB-FX", "name": "Labor-FX Special effects", "type": "Labor", "price": 800.00},
            {"sku": "SVC-TEC-002", "name": "Second Technician Option", "type": "Labor", "price": 750.00}
        ]
    },
    "basic": {
        "name": "Basic",
        "items": [
            # Rental Items Section
            {"sku": "QTE-DRFT-ITM", "name": "01-Draft Quote-Instructions (delete before sending quote)", "type": "Rental Items", "price": 0.00}
        ]
    },
    "low-level-fog": {
        "name": "Low Level Fog",
        "items": [
            # Hardware Section
            {"sku": "FOG-LLF-001", "name": "Low Lying Fog", "type": "Hardware", "price": 250.00},
            {"sku": "FOG-LLF-CTL", "name": "Low Lying Fog Control System", "type": "Hardware", "price": 350.00},
            
            # CO2 Tanks Section
            {"sku": "TNK-DEW-230", "name": "Tanks - Dewar CO2 - New Footprint", "type": "CO2 tanks", "price": 450.00},
            {"sku": "TNK-DEW-180", "name": "Tanks - Dewar Tall", "type": "CO2 tanks", "price": 400.00},
            {"sku": "TNK-CO2-SYP-001", "name": "CO2 Syphon Tank", "type": "CO2 tanks", "price": 350.00},
            
            # Additional Items Section
            {"sku": "FOG-LLF-002", "name": "Low Lying Fog Fluid", "type": "Additional items", "price": 75.00},
            {"sku": "TNK-3SPL-001", "name": "3-to-1 splitter CO2", "type": "Additional items", "price": 100.00},
            
            # Labor Section
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00},
            {"sku": "SVC-LAB-OVR", "name": "Labor Overtime & Per-Diem", "type": "Labor", "price": 500.00}
        ]
    },
    "robotics": {
        "name": "Robotics",
        "items": [
            # Robot packages Section
            {"sku": "ROB-PACK-001", "name": "AI Robotics Bulk Package", "type": "Robot packages", "price": 2500.00},
            {"sku": "ROB-PKG", "name": "Robotics Event Technology Package", "type": "Robot packages", "price": 1500.00},
            {"sku": "ROB-FLEET", "name": "Robot Fleet", "type": "Robot packages", "price": 3000.00},
            
            # Robot Dog Section
            {"sku": "ROB-DOG-001", "name": "Robotic Dog", "type": "Robot Dog", "price": 800.00},
            {"sku": "ROB-DOG2-001", "name": "R Dog AI with AI Lidar", "type": "Robot Dog", "price": 1200.00},
            {"sku": "ROB-DOG-IPAD", "name": "Dual iPad on back of robot dog", "type": "Robot Dog", "price": 300.00},
            {"sku": "ROB-DOG-CART", "name": "Robot Dog Cart/Wagon", "type": "Robot Dog", "price": 400.00},
            
            # Robot (Not Dog) Section
            {"sku": "ROB-ARM-001", "name": "Robotic Arm", "type": "Robot (Not Dog)", "price": 1000.00},
            {"sku": "ROB-CHESS-001", "name": "Robotic Chess", "type": "Robot (Not Dog)", "price": 1500.00},
            {"sku": "ROB-DRAW-001", "name": "Robotic Draw", "type": "Robot (Not Dog)", "price": 1200.00},
            {"sku": "ROB-FLO-001", "name": "Robotics-FLO", "type": "Robot (Not Dog)", "price": 800.00},
            {"sku": "ROB-HENRY-001", "name": "HRAI (Henry) Humanoid Robot w/AI", "type": "Robot (Not Dog)", "price": 2000.00},
            {"sku": "ROB-MM1-001", "name": "Mixmaster I Robot Bartender Activation", "type": "Robot (Not Dog)", "price": 1800.00},
            {"sku": "ROB-MM2-001", "name": "Mixmaster II Robot Bartender Activation", "type": "Robot (Not Dog)", "price": 2200.00},
            {"sku": "ROB-HAND", "name": "Robot - Thing Robot Hand", "type": "Robot (Not Dog)", "price": 600.00},
            {"sku": "ROB-TRY-001", "name": "AI Character Robot Tray", "type": "Robot (Not Dog)", "price": 500.00},
            {"sku": "ROB-TRON", "name": "TRON Robot Rental", "type": "Robot (Not Dog)", "price": 1500.00},
            {"sku": "ROB-WAL-001", "name": "Robotic Wally", "type": "Robot (Not Dog)", "price": 1000.00},
            {"sku": "ROB-WAL-TAL", "name": "WBT Walle Bot (Tall)", "type": "Robot (Not Dog)", "price": 1200.00},
            
            # Robot Branding Section
            {"sku": "ROB-DOG-BRND", "name": "Robot Dog Branding", "type": "Robot Branding", "price": 200.00},
            {"sku": "ROB-CART-BRND", "name": "Wagon/cart branding", "type": "Robot Branding", "price": 150.00},
            {"sku": "ROB-MM2-BRND", "name": "Branding for Robot Bartender ADAM", "type": "Robot Branding", "price": 250.00},
            
            # Additional Options Section
            {"sku": "ROB-LLM-VCE", "name": "Voice Prompt System", "type": "Additional Options", "price": 300.00},
            {"sku": "PRO-CNT-CNV", "name": "Projector Management & Content Conversion", "type": "Additional Options", "price": 400.00},
            {"sku": "ROB-PWR-001", "name": "Power Banks for Robotics", "type": "Additional Options", "price": 100.00},
            {"sku": "ROB-LLM-001", "name": "AI-Large Language Models (LLMs)", "type": "Additional Options", "price": 500.00},
            
            # Services - Labor Section
            {"sku": "SVC-ROB-SUP", "name": "Robot Supervisors", "type": "Services - Labor", "price": 1200.00},
            {"sku": "SVC-ROB-HDLR", "name": "Robot Handler", "type": "Services - Labor", "price": 800.00},
            {"sku": "SVC-ROB-TECH", "name": "Robot Programming Tech", "type": "Services - Labor", "price": 1000.00},
            {"sku": "SVC-TEC-002", "name": "Second Technician Option", "type": "Services - Labor", "price": 750.00},
            {"sku": "SVC-LAB-OVR", "name": "Labor Overtime & Per-Diem", "type": "Services - Labor", "price": 500.00}
        ]
    },
    "tank-delivery": {
        "name": "Tank Delivery",
        "items": [
            # Tanks Section
            {"sku": "TNK-DEW-180", "name": "Tanks - Dewar Tall", "type": "Tanks", "price": 400.00},
            {"sku": "TNK-DEW-230", "name": "Tanks - Dewar CO2 - New Footprint", "type": "Tanks", "price": 450.00},
            {"sku": "TNK-CO2-SYP-001", "name": "CO2 Syphon Tank", "type": "Tanks", "price": 350.00},
            {"sku": "TNK-HEL-291", "name": "Tanks - Helium", "type": "Tanks", "price": 300.00},
            {"sku": "PYR-PRO-TNK", "name": "Pyro-Propane tank", "type": "Tanks", "price": 200.00},
            {"sku": "TNK-NIT-001", "name": "Nitrogen Tank", "type": "Tanks", "price": 400.00},
            {"sku": "TNK-DEL-001", "name": "Tanks - Force Majure", "type": "Tanks", "price": 500.00},
            {"sku": "TNK-RNT-FEE", "name": "Tanks - Rental Fee", "type": "Tanks", "price": 150.00},
            
            # Shipping Section
            {"sku": "TNK-SVC-FEE", "name": "Tanks - Service Fee", "type": "Shipping", "price": 100.00},
            
            # Additional Items Section
            {"sku": "TNK-RSH-FEE", "name": "Tanks - Last Minute Order", "type": "Additional Items", "price": 200.00},
            {"sku": "SVC-RPR-CO2", "name": "CO2 Jet Repair", "type": "Additional Items", "price": 200.00},
            {"sku": "TNK-RPR-CO2", "name": "Tanks - Hose Repair", "type": "Additional Items", "price": 150.00}
        ]
    },
    "led-lanyards": {
        "name": "LED Lanyards",
        "items": [
            # LED Lanyards Section
            {"sku": "LED-LYX-001", "name": "LED-Xylo-Lanyard", "type": "LED Lanyards", "price": 150.00},
            {"sku": "LED-LYT-12LED-001", "name": "TLC 12-Led Lanyard", "type": "LED Lanyards", "price": 200.00},
            
            # Programming and Control Section
            {"sku": "LED-WBT-TX306-001", "name": "Controller-TLC-306-Pixel-Wristbands&Lanyards", "type": "Programming", "price": 400.00},
            {"sku": "LED-WBX-CTX", "name": "Controller-Xylobands-Wristbands/Lanyards", "type": "Programming", "price": 350.00},
            {"sku": "LED-WBE-HTX", "name": "Remote Control for Wristbands/Lanyards", "type": "Programming", "price": 300.00},
            {"sku": "SVC-PGM-WB-LY-003", "name": "Programming Advanced for Wristbands& Lanyards", "type": "Programming", "price": 500.00},
            {"sku": "SVC-PGM-WB-LY-002", "name": "Programming Mid-Level for Wristbands& Lanyards", "type": "Programming", "price": 350.00},
            {"sku": "SVC-PGM-WB-LY-001", "name": "Programming Standard for Wristbands& Lanyards", "type": "Programming", "price": 250.00},
            {"sku": "LED-WB-HTX1", "name": "HTX Controller Refundable Deposit", "type": "Programming", "price": 500.00},
            
            # Branding Section
            {"sku": "LED-LAN-BRAND", "name": "Lanyard Branding Options", "type": "Branding", "price": 100.00},
            
            # Labor Section
            {"sku": "SVC-WBT-TECH", "name": "Service Technician for Wristbands", "type": "Labor", "price": 800.00},
            {"sku": "SVC-LAB-WBL", "name": "Labor-Wristband/Landyards", "type": "Labor", "price": 650.00},
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00},
            {"sku": "SVC-TEC-002", "name": "Second Technician Option", "type": "Labor", "price": 750.00}
        ]
    }
}

# Bundle 2: Universal (T&E + Shipping) - Complete list from interface
UNIVERSAL_BUNDLE = {
    "name": "Travel & Shipping",
    "items": [
        {"sku": "SHP-S&H-001", "name": "Shipping & Handling", "type": "Shipping", "price": 150.00},
        {"sku": "T&E-BUY-OUT", "name": "T&E - accommodations Buyout", "type": "Buyout", "price": 500.00},
        {"sku": "T&E-BAG-001", "name": "T&E-Baggage fees", "type": "Baggage", "price": 100.00},
        {"sku": "T&E-FLY-001", "name": "T&E-Flights", "type": "Flights", "price": 800.00},
        {"sku": "T&E-GND-001", "name": "T&E-Ground transportation", "type": "Ground", "price": 200.00},
        {"sku": "T&E-MLS-001", "name": "T&E-Meals", "type": "Meals", "price": 150.00},
        {"sku": "T&E-PRK-001", "name": "T&E-Parking", "type": "Parking", "price": 50.00},
        {"sku": "T&E-PER-DIM", "name": "T&E-Per Diem", "type": "PerDiem", "price": 95.00},
        {"sku": "T&E-RMS-001", "name": "T&E-Rooms", "type": "Rooms", "price": 400.00}
    ]
}

def find_item_details_by_sku(sku, access_token):
    """
    Find Quoter item details by Item Code (cross-system SKU)
    
    Args:
        sku: Item Code (cross-system identifier)
        access_token: Quoter API token
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    page = 1
    while page <= 5:
        search_params = {'search': sku, 'page': page, 'limit': 100}
        response = requests.get('https://api.quoter.com/v1/items', headers=headers, params=search_params)

        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])

            for item in items:
                if item.get('code') == sku:  # Use 'code' field, not 'sku'
                    return {
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'code': item.get('code'),
                        'price': float(item.get('base_price', 0)),
                        'category': item.get('category', 'Unknown')
                    }

            if len(items) == 0:
                break
            page += 1

    return None

def get_template_line_items(template_name, access_token=None):
    """
    Get all items for a template with real Quoter pricing
    
    Args:
        template_name (str): Template identifier (e.g., 'floating-video')
        access_token (str): Quoter API access token for fetching real prices
        
    Returns:
        list: All items for the template with real pricing from Quoter
    """
    items = []
    
    # Add template-specific bundle
    if template_name in TEMPLATE_BUNDLES:
        template_items = TEMPLATE_BUNDLES[template_name]["items"].copy()
        
        # Fetch real pricing for each item if access token provided
        if access_token:
            for item in template_items:
                item_details = find_item_details_by_sku(item['sku'], access_token)
                if item_details:
                    item['id'] = item_details['id']
                    item['price'] = item_details['price']
                    item['real_name'] = item_details['name']
                    print(f"✅ Found {item_details['name']} - ${item_details['price']:,.2f} (Code: {item['sku']})")
                else:
                    item['id'] = None
                    item['price'] = item.get('price', 100.00)  # Fallback price
                    print(f"⚠️ Item not found in Quoter: {item['sku']} - using fallback ${item['price']:,.2f}")
        
        items.extend(template_items)
        print(f"✅ Added {len(template_items)} items from {TEMPLATE_BUNDLES[template_name]['name']} template")
    else:
        print(f"⚠️ Template '{template_name}' not found in TEMPLATE_BUNDLES")
    
    # Always add universal bundle
    universal_items = UNIVERSAL_BUNDLE["items"].copy()
    
    # Fetch real pricing for universal items if access token provided
    if access_token:
        for item in universal_items:
            item_details = find_item_details_by_sku(item['sku'], access_token)
            if item_details:
                item['id'] = item_details['id']
                item['price'] = item_details['price']
                item['real_name'] = item_details['name']
                print(f"✅ Found {item_details['name']} - ${item_details['price']:,.2f}")
            else:
                item['id'] = None
                item['price'] = item.get('price', 100.00)  # Fallback price
                print(f"⚠️ Item not found in Quoter: {item['sku']} - using fallback ${item['price']:,.2f}")
    
    items.extend(universal_items)
    print(f"✅ Added {len(universal_items)} universal items")
    
    return items

def get_template_info(template_name):
    """
    Get template information
    
    Args:
        template_name (str): Template identifier
        
    Returns:
        dict: Template information or None if not found
    """
    return TEMPLATE_BUNDLES.get(template_name)

def verify_bundle_against_quoter(template_name, access_token):
    """
    Verify stored bundle data against current Quoter items
    
    Args:
        template_name (str): Template identifier
        access_token (str): Quoter API access token
        
    Returns:
        dict: Verification results with changes detected
    """
    print(f"🔍 Verifying {template_name} bundle against Quoter...")
    
    # Get all items from bundle
    all_items = get_template_line_items(template_name, access_token)
    
    verification_results = {
        "template_name": template_name,
        "total_items": len(all_items),
        "items_verified": 0,
        "items_changed": [],
        "items_not_found": [],
        "items_unchanged": []
    }
    
    for item in all_items:
        sku = item['sku']
        stored_name = item['name']
        stored_price = item['price']
        stored_type = item['type']
        
        # Try to find item in Quoter
        item_details = find_item_details_by_sku(sku, access_token)
        
        if item_details:
            quoter_name = item_details['name']
            quoter_price = item_details['price']
            quoter_category = item_details['category']
            
            verification_results["items_verified"] += 1
            
            # Check for changes
            changes = []
            if stored_name != quoter_name:
                changes.append(f"name: '{stored_name}' → '{quoter_name}'")
            if abs(stored_price - quoter_price) > 0.01:  # Allow for rounding
                changes.append(f"price: ${stored_price:,.2f} → ${quoter_price:,.2f}")
            if stored_type != quoter_category:
                changes.append(f"type: '{stored_type}' → '{quoter_category}'")
            
            if changes:
                verification_results["items_changed"].append({
                    "sku": sku,
                    "changes": changes,
                    "stored": {"name": stored_name, "price": stored_price, "type": stored_type},
                    "quoter": {"name": quoter_name, "price": quoter_price, "category": quoter_category}
                })
                print(f"⚠️  {sku}: {', '.join(changes)}")
            else:
                verification_results["items_unchanged"].append(sku)
                print(f"✅ {sku}: No changes detected")
        else:
            verification_results["items_not_found"].append({
                "sku": sku,
                "stored": {"name": stored_name, "price": stored_price, "type": stored_type}
            })
            print(f"❌ {sku}: Item not found in Quoter")
    
    return verification_results

def update_bundle_from_quoter(template_name, access_token, dry_run=True):
    """
    Update stored bundle data with current Quoter information
    
    Args:
        template_name (str): Template identifier
        access_token (str): Quoter API access token
        dry_run (bool): If True, only show what would be updated
        
    Returns:
        dict: Update results
    """
    print(f"🔄 {'[DRY RUN] ' if dry_run else ''}Updating {template_name} bundle from Quoter...")
    
    verification = verify_bundle_against_quoter(template_name, access_token)
    
    if dry_run:
        print(f"\n📊 DRY RUN RESULTS:")
        print(f"   Items to update: {len(verification['items_changed'])}")
        print(f"   Items not found: {len(verification['items_not_found'])}")
        print(f"   Items unchanged: {len(verification['items_unchanged'])}")
        
        if verification['items_changed']:
            print(f"\n🔄 Items that would be updated:")
            for item in verification['items_changed']:
                print(f"   {item['sku']}: {', '.join(item['changes'])}")
        
        return verification
    
    else:
        print(f"\n⚠️  LIVE UPDATE MODE - This would modify the stored bundle!")
        print(f"   Run with dry_run=True first to preview changes.")
        return verification

def get_available_templates():
    """
    Get list of available templates
    
    Returns:
        list: Available template names
    """
    return list(TEMPLATE_BUNDLES.keys())

def get_item_by_sku(sku, template_name=None):
    """
    Find an item by SKU across all bundles
    
    Args:
        sku (str): Item SKU code
        template_name (str, optional): Specific template to search
        
    Returns:
        dict: Item information or None if not found
    """
    # Search in template bundles
    if template_name and template_name in TEMPLATE_BUNDLES:
        for item in TEMPLATE_BUNDLES[template_name]["items"]:
            if item["sku"] == sku:
                return item
    
    # Search in all template bundles
    for template_name, template_data in TEMPLATE_BUNDLES.items():
        for item in template_data["items"]:
            if item["sku"] == sku:
                return item
    
    # Search in universal bundle
    for item in UNIVERSAL_BUNDLE["items"]:
        if item["sku"] == sku:
            return item
    
    return None

# Test function
if __name__ == "__main__":
    print("🧪 Testing Enhanced Template Mapping System")
    print("=" * 50)
    
    # Test available templates
    templates = get_available_templates()
    print(f"📋 Available templates: {templates}")
    
    # Test floating video template
    if "floating-video" in templates:
        items = get_template_line_items("floating-video")
        print(f"\n🎯 Floating Video Template:")
        print(f"   Total items: {len(items)}")
        
        # Group by type
        types = {}
        for item in items:
            item_type = item["type"]
            if item_type not in types:
                types[item_type] = []
            types[item_type].append(item["name"])
        
        print(f"   Items by type:")
        for item_type, names in types.items():
            print(f"     {item_type}: {len(names)} items")
    
    print("\n✅ Template mapping system ready!")
