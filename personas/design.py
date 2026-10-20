"""Fictional needs-based archetypes; not inferred demographic segments."""
PERSONAS = {
    "value": {"name": "Value planner", "need": "Low unit cost and predictable household supply", "weights": [0.55, 0.15, 0.15, 0.15]},
    "comfort": {"name": "Comfort seeker", "need": "Soft feel and clear fragrance information", "weights": [0.15, 0.55, 0.15, 0.15]},
    "eco": {"name": "Resource-conscious buyer", "need": "Less packaging with credible evidence of environmental benefits", "weights": [0.15, 0.20, 0.50, 0.15]},
    "convenience": {"name": "Convenience seeker", "need": "Easy storage and reliable replenishment", "weights": [0.15, 0.20, 0.15, 0.50]},
}
# Features are fictional design assumptions, not product test results.
CONCEPTS = {
    "essential": {"name": "Essential bulk tissue", "description": "Low-price bulk tissue; basic softness; large storage footprint.", "features": [0.95, 0.45, 0.35, 0.35]},
    "gentle": {"name": "Gentle compact tissue", "description": "Premium-priced soft fragrance-free tissue in a compact dispenser; standard packaging.", "features": [0.35, 0.95, 0.40, 0.75]},
    "refill": {"name": "Refill tissue pack", "description": "Mid-price tissue refill with reduced packaging and reusable dispenser; refilling takes effort.", "features": [0.60, 0.65, 0.95, 0.45]},
}
QUESTION = "How likely would you be to buy this concept? 1=very unlikely, 2=unlikely, 3=neutral, 4=likely, 5=very likely. Explain one benefit and one concern."
PROMPT_VERSION = "needs-only-v1"
