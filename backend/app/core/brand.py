"""
SED Energy Brand Identity & Knowledge Constants
This module is the single source of truth for all brand data used by AI agents.
"""

SED_BRAND = {
    "company_name": "SED Energy",
    "legal_name": "Solar Energy Distributor Pty Ltd",
    "tagline": "South Africa Tier 1 Solar Distributor",
    "website": "sed.energy",
    "store": "solarenergydistributor.co.za",
    "email": "info@sed.energy",
    "phone": "010 006 8246",
    "phone_alt": "+27 11 876 1000",
    "whatsapp": "+27 79 748 6483",
    "hq_address": "3 Rydal Lane, Longlake, Sandton, Johannesburg, 1609",
    "pe_address": "Unit A2 Multiuser Facility, Zone 3 Coega SEZ",
    "zambia_address": "Plot No. 11026, Off Mumbwa Road, Lusaka, Zambia",
    "social": {
        "facebook": "facebook.com/SolarEnergyDistributorSA",
        "instagram": "instagram.com/sed_energy",
        "linkedin": "linkedin.com/company/sed-energy",
    },
    "colors": {
        "primary": "#E85A0C",        # SED Orange
        "secondary": "#333333",      # Dark Grey
        "text": "#1A1A1A",
        "white": "#FFFFFF",
        "light_grey": "#F5F5F5",
        "accent_dark": "#1C1C1C",
    },
    "mission": (
        "To make it easier for solar professionals to access quality products "
        "and keep projects moving forward. We are not simply moving products — "
        "we are helping trade customers build solar solutions with confidence."
    ),
    "value_propositions": [
        "Tier 1 distributor status with certified manufacturer partnerships",
        "Comprehensive product range: panels, inverters, batteries, mounting, accessories",
        "High stock availability with competitive wholesale pricing",
        "Same-day or next-day responses and fast nationwide logistics",
        "Expert technical support and dedicated account managers",
        "25+ year product warranties on all distributed brands",
        "B2B trade-focused — not retail",
        "3 office locations: Johannesburg, Port Elizabeth, Zambia",
    ],
}

SED_BRANDS_DISTRIBUTED = {
    "Astronergy": {
        "category": "solar_panel",
        "tier": 1,
        "description": "High-efficiency monocrystalline panels, Tier 1, bankable, field-proven in SA conditions",
    },
    "Hanersun": {
        "category": "solar_panel",
        "tier": 1,
        "description": "Premium solar panels for residential, commercial, and industrial applications",
    },
    "Sungrow": {
        "category": "inverter",
        "tier": 1,
        "description": "World's largest inverter manufacturer. Grid-tied and hybrid inverter solutions",
    },
    "Hinen": {
        "category": "battery",
        "tier": 1,
        "description": "Advanced lithium battery solutions for backup power and off-grid storage",
    },
    "Sunova": {
        "category": "solar_panel",
        "tier": 1,
        "description": "High-performance solar modules",
    },
    "Powerco": {"category": "accessory", "tier": 1, "description": "Solar BOS components"},
    "Grenex": {"category": "accessory", "tier": 1, "description": "Solar accessories and hardware"},
    "Knyee": {"category": "mounting", "tier": 1, "description": "Mounting systems and structures"},
    "PROJOY": {"category": "accessory", "tier": 1, "description": "Solar connectors and junction boxes"},
}

SED_TARGET_AUDIENCES = {
    "installers": {
        "description": "Solar installation contractors and technicians",
        "pain_points": ["stock availability", "competitive pricing", "technical support", "fast delivery"],
        "content_focus": ["stock alerts", "technical tips", "product launches", "pricing"],
        "tone": "professional, practical, partner-like",
    },
    "epc_contractors": {
        "description": "Engineering, Procurement, and Construction companies",
        "pain_points": ["bulk pricing", "project delivery timelines", "technical specifications", "warranty support"],
        "content_focus": ["C&I solutions", "large-scale projects", "technical education", "case studies"],
        "tone": "technical, executive, credibility-focused",
    },
    "project_developers": {
        "description": "Renewable energy project developers",
        "pain_points": ["bankable equipment", "financing compatibility", "long-term reliability"],
        "content_focus": ["bankability", "warranties", "financing", "project scale"],
        "tone": "executive, investment-grade",
    },
    "resellers": {
        "description": "Secondary distributors and resellers",
        "pain_points": ["margin protection", "stock access", "brand support"],
        "content_focus": ["bulk offers", "partner programs", "product range"],
        "tone": "trade, commercial",
    },
    "commercial_buyers": {
        "description": "C&I businesses buying solar for own use",
        "pain_points": ["ROI", "loadshedding", "energy costs", "reliability"],
        "content_focus": ["ROI education", "case studies", "loadshedding resilience", "C&I solutions"],
        "tone": "business-case driven, educational",
    },
}

SED_WHATSAPP_GROUP_PROFILES = {
    "installer_general": {
        "type": "installer",
        "audience": "General pool of certified solar installers",
        "posting_frequency": "2-3x per week",
        "preferred_content": ["stock arrivals", "price updates", "technical tips", "product launches"],
        "tone": "practical, direct, informative",
        "avoid": ["hard sell language", "excessive emojis", "off-topic content"],
    },
    "vip_clients": {
        "type": "vip_client",
        "audience": "Top-tier clients with priority access",
        "posting_frequency": "As needed, priority updates",
        "preferred_content": ["exclusive stock", "early pricing", "priority delivery", "VIP offers"],
        "tone": "exclusive, premium, relationship-focused",
        "avoid": ["generic content", "anything sent to general groups first"],
    },
    "internal_sales": {
        "type": "internal_sales",
        "audience": "Internal sales team",
        "posting_frequency": "Daily",
        "preferred_content": ["lead alerts", "stock updates", "pricing changes", "performance reports"],
        "tone": "direct, data-driven, motivating",
        "avoid": ["public-facing marketing language"],
    },
    "epc_commercial": {
        "type": "epc",
        "audience": "EPC contractors and project developers",
        "posting_frequency": "1-2x per week",
        "preferred_content": ["large stock availability", "technical specs", "project case studies", "industry news"],
        "tone": "technical, professional, expert",
        "avoid": ["residential content", "small system sizes"],
    },
}

SED_CONTENT_TOPICS = [
    "stock_arrival",
    "product_launch",
    "technical_education",
    "solar_myth_busting",
    "loadshedding_update",
    "eskom_news",
    "industry_news",
    "c_and_i_insight",
    "installer_tip",
    "battery_knowledge",
    "inverter_guide",
    "panel_comparison",
    "roi_education",
    "sa_solar_regulation",
    "project_case_study",
    "company_announcement",
    "supplier_partnership",
    "warehouse_update",
    "seasonal_campaign",
    "energy_market_trend",
]

PLATFORM_POSTING_GUIDELINES = {
    "facebook": {
        "optimal_length": "100-250 words for posts, 50 words for captions",
        "hashtag_count": "5-10",
        "posting_frequency": "5-7x per week",
        "best_times_sast": ["07:00-09:00", "12:00-14:00", "17:00-19:00"],
        "content_mix": {"educational": 40, "promotional": 30, "engagement": 20, "company": 10},
    },
    "instagram": {
        "optimal_length": "Caption: 125-150 chars (before 'more')",
        "hashtag_count": "20-30",
        "posting_frequency": "4-5x per week",
        "best_times_sast": ["06:00-08:00", "12:00-14:00", "19:00-21:00"],
        "content_mix": {"visual_product": 35, "educational": 25, "lifestyle": 20, "behind_scenes": 20},
    },
    "linkedin": {
        "optimal_length": "150-300 words for posts, 1200+ for articles",
        "hashtag_count": "3-5",
        "posting_frequency": "3-4x per week",
        "best_times_sast": ["07:30-08:30", "12:00-13:00", "17:00-18:00"],
        "content_mix": {"thought_leadership": 40, "company_news": 30, "industry": 20, "product": 10},
    },
    "whatsapp": {
        "optimal_length": "50-200 words depending on group type",
        "hashtag_count": "0-3",
        "posting_frequency": "Group-specific (see WhatsApp group profiles)",
        "best_times_sast": ["07:30-08:30", "12:30-13:30"],
        "format": "Concise, scannable, action-oriented",
    },
}
