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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote using the links below:</p>

<p>
  <a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; margin-right: 10px;">View Online</a>
  <a href="{{quote.pdf_url}}" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Download PDF</a>
</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Important Notes for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Power requirements: Standard 120V outlets (quantity varies by package)</li>
    <li>Space requirements: Minimum ceiling height and clear viewing areas</li>
    <li>Content preparation: Graphics files must be provided in specified formats</li>
</ul>

<p><strong>Timeline:</strong></p>
<ul>
    <li>Setup: 2-4 hours depending on package complexity</li>
    <li>Testing: 1 hour for system verification</li>
    <li>Strike: 1-2 hours for equipment breakdown</li>
</ul>

<p><strong>Next Steps:</strong></p>
<ol>
    <li>Review this quote and confirm package selection</li>
    <li>Schedule site visit for technical assessment</li>
    <li>Provide content files for graphics preparation</li>
    <li>Confirm event timeline and access requirements</li>
</ol>

<p>Questions? Contact us at {{quote.owner.email}} or call us directly.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Technical Specifications for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Wristband Options:</strong></p>
<ul>
    <li><strong>Xylo Wristbands:</strong> 8-LED and 12-LED options with premium features</li>
    <li><strong>TLC Wristbands:</strong> 2-LED, 4-LED with/without button options</li>
    <li><strong>Battery Life:</strong> 8-12 hours continuous operation</li>
    <li><strong>Range:</strong> 300+ feet from controller</li>
</ul>

<p><strong>Control Systems:</strong></p>
<ul>
    <li>Professional laptop with specialized software</li>
    <li>Launchpad for live control and synchronization</li>
    <li>Remote control options for operator mobility</li>
    <li>HTX Controller with refundable deposit</li>
</ul>

<p><strong>Programming Services:</strong></p>
<ul>
    <li><strong>Standard:</strong> Basic color patterns and simple sequences</li>
    <li><strong>Mid-Level:</strong> Complex patterns and audience interaction</li>
    <li><strong>Advanced:</strong> Custom programming and music synchronization</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Power: Standard 120V outlets for control systems</li>
    <li>Space: Clear line-of-sight for controller communication</li>
    <li>Timing: 2-3 hours for setup and testing</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for technical specifications.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Balloon Package Details for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Available Effects:</strong></p>
<ul>
    <li><strong>Balloon Drop:</strong> Ceiling-mounted net system for dramatic releases</li>
    <li><strong>Balloon Moon LED:</strong> Large illuminated balloon for evening ambiance</li>
    <li><strong>Disappearing Balloon Wall:</strong> Interactive wall effect</li>
    <li><strong>Flying Balloon Wall:</strong> Suspended balloon display</li>
</ul>

<p><strong>Equipment Included:</strong></p>
<ul>
    <li>Professional balloon air filler for efficient inflation</li>
    <li>Balloon drop net system (ceiling mounted)</li>
    <li>Balloon packages (quantity varies by package)</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Ceiling access for balloon drop installation</li>
    <li>Power outlets for LED balloon displays</li>
    <li>Setup time: 1-2 hours depending on package</li>
    <li>Strike time: 30 minutes</li>
</ul>

<p><strong>Safety Notes:</strong></p>
<ul>
    <li>All installations performed by certified technicians</li>
    <li>Venue requirements: Ceiling height minimum 10 feet</li>
    <li>Safety inspections included in labor</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for venue-specific requirements.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>CO2/Smoke System Specifications for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>CO2 Effects:</strong></p>
<ul>
    <li><strong>Cryo Jet:</strong> High-impact CO2 burst effects</li>
    <li><strong>Fogger:</strong> Professional atmospheric fog system</li>
    <li><strong>Relay Pack:</strong> Control system for synchronized effects</li>
</ul>

<p><strong>Tank Systems:</strong></p>
<ul>
    <li><strong>Dewar Tanks:</strong> Tall (180) and New Footprint (230) options</li>
    <li><strong>CO2 Syphon Tank:</strong> Specialized CO2 delivery system</li>
    <li><strong>3-to-1 Splitter:</strong> Multiple effect distribution</li>
</ul>

<p><strong>Safety & Service:</strong></p>
<ul>
    <li>CO2 Jet Repair service included</li>
    <li>Professional technician setup and operation</li>
    <li>Safety inspections and equipment testing</li>
    <li>Venue compliance verification</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Access to venue for tank placement</li>
    <li>Clear pathways for effect distribution</li>
    <li>Setup time: 2-3 hours</li>
    <li>Strike time: 1-2 hours</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for safety requirements and venue specifications.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Confetti/Streamers Package Details for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Cannon Systems:</strong></p>
<ul>
    <li><strong>Confetti Cannons:</strong> Professional-grade cannon systems</li>
    <li><strong>Silent Storm Blowers:</strong> SS and T models for different effects</li>
    <li><strong>Confetti Blower Rental:</strong> Additional blower options</li>
</ul>

<p><strong>Materials:</strong></p>
<ul>
    <li><strong>Streamers:</strong> Standard and custom options</li>
    <li><strong>Confetti:</strong> Various colors and materials</li>
    <li><strong>Custom Streamers:</strong> Branded or themed options</li>
</ul>

<p><strong>Control Systems:</strong></p>
<ul>
    <li>Nitrogen tank for propellant</li>
    <li>Relay pack for synchronized timing</li>
    <li>Custom launch coordination</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Ceiling mounting for cannon systems</li>
    <li>Clear firing zones for safety</li>
    <li>Setup time: 2-3 hours</li>
    <li>Strike time: 1 hour</li>
</ul>

<p><strong>Safety Notes:</strong></p>
<ul>
    <li>Professional installation and operation</li>
    <li>Venue safety compliance verification</li>
    <li>Cleanup service included</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for venue-specific requirements.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Pyrotechnic System Specifications for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Fireworks & Pyro Effects:</strong></p>
<ul>
    <li><strong>Fireworks:</strong> Professional-grade pyrotechnic displays</li>
    <li><strong>Pyro Effects:</strong> Custom effect estimates and designs</li>
    <li><strong>Flame Generators:</strong> Canister and propane-based systems</li>
    <li><strong>Real Fire Effects:</strong> Controlled fire displays</li>
</ul>

<p><strong>Special Effects:</strong></p>
<ul>
    <li><strong>White Sparkle Fountains:</strong> Elegant sparkle effects</li>
    <li><strong>Simulated Fire:</strong> Safe fire simulation systems</li>
    <li><strong>Dragon Fly & Firefly:</strong> Specialized fire effect systems</li>
</ul>

<p><strong>Professional Services:</strong></p>
<ul>
    <li><strong>Licensed Pyrotechnician:</strong> Certified professional on-site</li>
    <li><strong>Pyro Permits:</strong> All necessary permits and approvals</li>
    <li><strong>Safety Coordination:</strong> Venue compliance and safety protocols</li>
</ul>

<p><strong>⚠️ Safety Requirements:</strong></p>
<ul>
    <li>Venue must meet fire department requirements</li>
    <li>Proper permits and approvals required</li>
    <li>Safety inspections and fire marshal approval</li>
    <li>Professional operation and supervision mandatory</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Site inspection and safety assessment</li>
    <li>Permit application and approval process</li>
    <li>Setup time: 4-6 hours (including safety checks)</li>
    <li>Strike time: 2-3 hours (including cleanup)</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for permit requirements and safety specifications.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Basic Template Instructions for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>⚠️ Important:</strong> This is a draft template. Please complete the following steps:</p>

<ol>
    <li><strong>Delete Instruction Item:</strong> Remove the "01-Draft Quote-Instructions" item from the quote</li>
    <li><strong>Add Services:</strong> Add the specific services and equipment needed for this event</li>
    <li><strong>Review Pricing:</strong> Verify all pricing is accurate and up-to-date</li>
    <li><strong>Add Details:</strong> Include any special requirements or notes</li>
    <li><strong>Final Review:</strong> Double-check all items before publishing</li>
</ol>

<p><strong>Available Services:</strong></p>
<ul>
    <li>LED Wristbands & Lanyards</li>
    <li>Floating Video Holographic Systems</li>
    <li>Atmospheric Effects (CO2, Fog, Smoke)</li>
    <li>Balloon Effects & Displays</li>
    <li>Confetti & Streamer Systems</li>
    <li>Pyrotechnic & Fire Effects</li>
    <li>Robotic Entertainment</li>
    <li>Tank Delivery Services</li>
</ul>

<p><strong>Need Help?</strong></p>
<p>Contact {{quote.owner.email}} for assistance with quote customization or to discuss your specific event requirements.</p>""",
        "items": [
            # Rental Items Section
            {"sku": "QTE-DRFT-ITM", "name": "01-Draft Quote-Instructions (delete before sending quote)", "type": "Rental Items", "price": 0.00}
        ]
    },
    "low-level-fog": {
        "name": "Low Level Fog",
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Low Level Fog System Specifications for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Fog Equipment:</strong></p>
<ul>
    <li><strong>Low Lying Fog:</strong> Professional fog machine for ground-level effects</li>
    <li><strong>Control System:</strong> Advanced control system for fog management</li>
    <li><strong>Fog Fluid:</strong> Specialized low-lying fog fluid</li>
</ul>

<p><strong>Tank Systems:</strong></p>
<ul>
    <li><strong>Dewar CO2 Tanks:</strong> New Footprint (230) and Tall (180) options</li>
    <li><strong>CO2 Syphon Tank:</strong> Specialized CO2 delivery system</li>
    <li><strong>3-to-1 Splitter:</strong> Multiple effect distribution</li>
</ul>

<p><strong>Professional Services:</strong></p>
<ul>
    <li>Professional technician setup and operation</li>
    <li>System testing and calibration</li>
    <li>Safety inspections and equipment verification</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Access to venue for tank and equipment placement</li>
    <li>Clear pathways for fog distribution</li>
    <li>Setup time: 2-3 hours</li>
    <li>Strike time: 1-2 hours</li>
</ul>

<p><strong>Safety Notes:</strong></p>
<ul>
    <li>All installations performed by certified technicians</li>
    <li>Venue compliance verification included</li>
    <li>Equipment testing and safety checks</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for venue-specific requirements.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Robotics System Specifications for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Robot Packages:</strong></p>
<ul>
    <li><strong>AI Robotics Bulk Package:</strong> Comprehensive robotics solution</li>
    <li><strong>Event Technology Package:</strong> Standard robotics package</li>
    <li><strong>Robot Fleet:</strong> Multiple robot deployment</li>
</ul>

<p><strong>Robot Dogs:</strong></p>
<ul>
    <li><strong>Robotic Dog:</strong> AI-powered robotic companion</li>
    <li><strong>R Dog AI with Lidar:</strong> Advanced AI with spatial awareness</li>
    <li><strong>Dual iPad Mount:</strong> Interactive display system</li>
    <li><strong>Robot Dog Cart/Wagon:</strong> Mobile platform for robot</li>
</ul>

<p><strong>Specialized Robots:</strong></p>
<ul>
    <li><strong>Robotic Arm:</strong> Precision robotic arm system</li>
    <li><strong>Robotic Chess:</strong> AI chess playing robot</li>
    <li><strong>Robotic Draw:</strong> Artistic drawing robot</li>
    <li><strong>Robot Bartenders:</strong> Mixmaster I & II systems</li>
    <li><strong>Humanoid Robots:</strong> HRAI (Henry) and TRON robots</li>
</ul>

<p><strong>Professional Services:</strong></p>
<ul>
    <li><strong>Robot Supervisors:</strong> Professional robot oversight</li>
    <li><strong>Robot Handlers:</strong> Trained robot operators</li>
    <li><strong>Programming Techs:</strong> Custom programming services</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Power: Standard 120V outlets for robot charging</li>
    <li>Space: Clear pathways for robot movement</li>
    <li>Setup time: 3-4 hours for full system deployment</li>
    <li>Programming time: 2-3 hours for custom sequences</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for robotics specifications.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Tank Delivery Service Details for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Available Tank Types:</strong></p>
<ul>
    <li><strong>CO2 Dewar Tanks:</strong> Tall (180) and New Footprint (230) options</li>
    <li><strong>CO2 Syphon Tanks:</strong> Specialized CO2 delivery systems</li>
    <li><strong>Helium Tanks:</strong> For balloon and special effects</li>
    <li><strong>Propane Tanks:</strong> For pyrotechnic and fire effects</li>
    <li><strong>Nitrogen Tanks:</strong> For confetti and streamer systems</li>
</ul>

<p><strong>Service Options:</strong></p>
<ul>
    <li><strong>Standard Delivery:</strong> Regular delivery and pickup service</li>
    <li><strong>Force Majeure:</strong> Emergency delivery service</li>
    <li><strong>Rental Fees:</strong> Tank rental charges</li>
    <li><strong>Service Fees:</strong> Delivery and setup charges</li>
</ul>

<p><strong>Additional Services:</strong></p>
<ul>
    <li><strong>Last Minute Orders:</strong> Rush delivery service</li>
    <li><strong>CO2 Jet Repair:</strong> On-site repair services</li>
    <li><strong>Hose Repair:</strong> Tank connection repairs</li>
</ul>

<p><strong>Delivery Requirements:</strong></p>
<ul>
    <li>Access to venue for tank delivery</li>
    <li>Clear pathways for tank placement</li>
    <li>Setup time: 1-2 hours</li>
    <li>Pickup time: 30 minutes</li>
</ul>

<p><strong>Safety Notes:</strong></p>
<ul>
    <li>All tanks delivered by certified technicians</li>
    <li>Safety inspections included with delivery</li>
    <li>Proper handling and storage instructions provided</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for delivery scheduling and requirements.</p>""",
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
        "cover_letter": """<p>Hi {{person.first_name}},</p>

<p>You have a quote from <strong>TLC Creative</strong> for '{{deal.title}} - {{deal.id}}'. You can review the quote by following the link below.</p>

<p><a href="{{quote.url}}" style="background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Your Quote</a></p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
{{deal.owner_name}}<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>LED Lanyard System Details for {{deal.title}} - {{deal.id}}:</h3>

<p><strong>Lanyard Options:</strong></p>
<ul>
    <li><strong>LED-Xylo-Lanyard:</strong> Premium LED lanyard system</li>
    <li><strong>TLC 12-LED Lanyard:</strong> High-brightness LED option</li>
    <li><strong>Battery Life:</strong> 8-12 hours continuous operation</li>
    <li><strong>Range:</strong> 300+ feet from controller</li>
</ul>

<p><strong>Control & Programming:</strong></p>
<ul>
    <li><strong>TLC Controller:</strong> 306-pixel control system</li>
    <li><strong>Xylobands Controller:</strong> Specialized Xylo control</li>
    <li><strong>Remote Control:</strong> Wireless control options</li>
    <li><strong>Programming Levels:</strong> Standard, Mid-Level, and Advanced</li>
</ul>

<p><strong>Branding & Customization:</strong></p>
<ul>
    <li>Custom lanyard branding options</li>
    <li>HTX Controller with refundable deposit</li>
    <li>Professional service technician support</li>
</ul>

<p><strong>Setup Requirements:</strong></p>
<ul>
    <li>Power: Standard 120V outlets for control systems</li>
    <li>Space: Clear line-of-sight for controller communication</li>
    <li>Setup time: 2-3 hours for system configuration</li>
    <li>Programming time: 1-2 hours for custom sequences</li>
</ul>

<p>Questions? Contact {{quote.owner.email}} for programming specifications.</p>""",
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

def get_template_cover_letter(template_name):
    """
    Get cover letter for a specific template.
    
    Args:
        template_name (str): Template name
        
    Returns:
        str: Cover letter HTML content
    """
    bundle = TEMPLATE_BUNDLES.get(template_name)
    return bundle.get('cover_letter', '') if bundle else ''

def get_template_appended_content(template_name):
    """
    Get appended content for a specific template.
    
    Args:
        template_name (str): Template name
        
    Returns:
        str: Appended content HTML
    """
    bundle = TEMPLATE_BUNDLES.get(template_name)
    return bundle.get('appended_content', '') if bundle else ''

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
