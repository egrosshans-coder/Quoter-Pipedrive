#!/usr/bin/env python3
"""
Simple Template Mapping for Cover Letter Editor
Contains only the template data without API dependencies
"""

# Bundle 1: Template-Specific (Hardware + Labor) - Reduced Items
TEMPLATE_BUNDLES = {
    "floating-video": {
        "name": "Floating Video",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Technical Specifications for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Floating Video System:</strong> Professional-grade floating video display with 4K resolution</li>
<li><strong>Control System:</strong> Advanced software for seamless video management</li>
<li><strong>Installation:</strong> Complete setup and configuration by certified technicians</li>
<li><strong>Support:</strong> 24/7 technical support during your event</li>
</ul>"""
    },
    "led-wristbands": {
        "name": "LED Wristbands",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>LED Wristband System Details for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>LED Wristbands:</strong> Custom-programmed LED wristband systems</li>
<li><strong>Programming:</strong> Custom light patterns and sequences</li>
<li><strong>Control System:</strong> Centralized control for all wristbands</li>
<li><strong>Battery Life:</strong> Long-lasting battery systems for extended use</li>
</ul>"""
    },
    "balloons": {
        "name": "Balloons",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Balloon Package Details for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Balloon Arrangements:</strong> Custom-designed balloon displays and centerpieces</li>
<li><strong>Colors & Themes:</strong> Coordinated with your event's color scheme</li>
<li><strong>Setup & Breakdown:</strong> Professional installation and cleanup service</li>
<li><strong>Materials:</strong> High-quality latex and foil balloons</li>
</ul>"""
    },
    "co2-smoke-system": {
        "name": "CO2/Smoke System",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>CO2/Smoke System Specifications for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>CO2 Machines:</strong> Professional-grade CO2 fog machines</li>
<li><strong>Control System:</strong> Remote-controlled operation for precise timing</li>
<li><strong>Safety Equipment:</strong> All necessary safety measures and monitoring</li>
<li><strong>CO2 Supply:</strong> Sufficient CO2 for your event duration</li>
</ul>"""
    },
    "confetti-streamers": {
        "name": "Confetti/Streamers",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Confetti/Streamers Package Details for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Confetti Cannons:</strong> Professional confetti launching systems</li>
<li><strong>Streamer Machines:</strong> Automated streamer deployment</li>
<li><strong>Custom Colors:</strong> Coordinated with your event theme</li>
<li><strong>Timing Control:</strong> Precise activation for perfect moments</li>
</ul>"""
    },
    "fireworks-pyro-fire": {
        "name": "Fireworks/Pyro/Fire",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Pyrotechnic System Specifications for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Fireworks Display:</strong> Professional pyrotechnic show</li>
<li><strong>Safety Compliance:</strong> All permits and safety measures included</li>
<li><strong>Custom Design:</strong> Tailored to your event's theme and timing</li>
<li><strong>Professional Setup:</strong> Licensed pyrotechnicians on-site</li>
</ul>"""
    },
    "basic": {
        "name": "Basic",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Basic Template Instructions for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Service Details:</strong> Comprehensive breakdown of all services included</li>
<li><strong>Equipment List:</strong> Complete inventory of equipment and materials</li>
<li><strong>Timeline:</strong> Detailed schedule for setup, execution, and breakdown</li>
<li><strong>Support:</strong> Ongoing support and communication throughout the process</li>
</ul>"""
    },
    "low-level-fog": {
        "name": "Low Level Fog",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Low Level Fog System Specifications for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Fog Machines:</strong> Professional low-level fog generators</li>
<li><strong>Fog Fluid:</strong> High-quality, safe fog solution</li>
<li><strong>Control System:</strong> Remote operation and timing control</li>
<li><strong>Safety Measures:</strong> All necessary safety equipment and monitoring</li>
</ul>"""
    },
    "robotics": {
        "name": "Robotics",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Robotics System Specifications for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Robotic Equipment:</strong> Advanced robotic systems for your event</li>
<li><strong>Programming:</strong> Custom programming for specific movements and timing</li>
<li><strong>Control Interface:</strong> User-friendly control system for operators</li>
<li><strong>Technical Support:</strong> On-site technical support and maintenance</li>
</ul>"""
    },
    "tank-delivery": {
        "name": "Tank Delivery",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>Tank Delivery Service Details for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>Tank Delivery:</strong> Professional tank delivery and setup service</li>
<li><strong>Equipment:</strong> All necessary tanks and related equipment</li>
<li><strong>Installation:</strong> Complete setup and configuration</li>
<li><strong>Pickup Service:</strong> Post-event pickup and cleanup</li>
</ul>"""
    },
    "led-lanyards": {
        "name": "LED Lanyards",
        "cover_letter": """<h2>Proposal for ##CustomerOrganization##</h2>

<p>Dear ##CustomerFirstName##,</p>

<p>Thank you for the opportunity to work with ##CustomerOrganization##. We've prepared a custom proposal to support your upcoming project. This quote was created on ##QuoteCreatedDate## and is valid through ##QuoteExpiryDate##.</p>

<p>Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.</p>

<p>We are truly excited about the opportunity to collaborate with you and your esteemed team.</p>

<p>Should you have any questions, clarifications, or special requests, please do not hesitate to reach out. We are here to accommodate your needs and ensure a seamless process leading up to the event.</p>

<p>Sincerely,<br><br>
##UserFirstName## ##UserLastName##<br>
{% if deal.owner_name == 'Maurice Capillaire' %}Sales and Logistics{% elif deal.owner_name == 'Jeff Ward' %}Sales and Logistics{% elif deal.owner_name == 'Eric Grosshans' %}Technical Director{% else %}Sales Team{% endif %}<br>
TLC Creative</p>""",
        "appended_content": """<h3>LED Lanyard System Details for {{deal.title}} - {{deal.id}}:</h3>
<ul>
<li><strong>LED Lanyards:</strong> Custom-programmed LED lanyard systems</li>
<li><strong>Programming:</strong> Custom light patterns and sequences</li>
<li><strong>Control System:</strong> Centralized control for all lanyards</li>
<li><strong>Battery Life:</strong> Long-lasting battery systems for extended use</li>
</ul>"""
    }
}

def get_template_cover_letter(template_key):
    """Get cover letter for a template"""
    if template_key in TEMPLATE_BUNDLES:
        return TEMPLATE_BUNDLES[template_key]['cover_letter']
    return ""

def get_template_appended_content(template_key):
    """Get appended content for a template"""
    if template_key in TEMPLATE_BUNDLES:
        return TEMPLATE_BUNDLES[template_key]['appended_content']
    return ""
