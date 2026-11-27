class Sector:
    """Sector metadata and multipliers for company fundamentals."""

    SECTORS = {
        "Technology": {
            "growth_multiplier": 1.15,
            "volatility_multiplier": 1.25,
            "pe_multiplier": 1.2,
            "sentiment_sensitivity": 1.3,
        },
        "Healthcare": {
            "growth_multiplier": 1.05,
            "volatility_multiplier": 1.1,
            "pe_multiplier": 1.1,
            "sentiment_sensitivity": 1.0,
        },
        "Finance": {
            "growth_multiplier": 0.95,
            "volatility_multiplier": 1.2,
            "pe_multiplier": 0.9,
            "sentiment_sensitivity": 1.15,
        },
        "Energy": {
            "growth_multiplier": 1.0,
            "volatility_multiplier": 1.4,
            "pe_multiplier": 0.85,
            "sentiment_sensitivity": 1.2,
        },
        "Consumer": {
            "growth_multiplier": 1.0,
            "volatility_multiplier": 1.0,
            "pe_multiplier": 1.0,
            "sentiment_sensitivity": 1.1,
        },
        "Industrial": {
            "growth_multiplier": 0.98,
            "volatility_multiplier": 1.05,
            "pe_multiplier": 0.95,
            "sentiment_sensitivity": 0.9,
        },
        "Utilities": {
            "growth_multiplier": 0.85,
            "volatility_multiplier": 0.75,
            "pe_multiplier": 0.8,
            "sentiment_sensitivity": 0.7,
        },
        "Biotech": {
            "growth_multiplier": 1.25,
            "volatility_multiplier": 1.6,
            "pe_multiplier": 1.35,
            "sentiment_sensitivity": 1.5,
        },
    }

    DEFAULT = {
        "growth_multiplier": 1.0,
        "volatility_multiplier": 1.0,
        "pe_multiplier": 1.0,
        "sentiment_sensitivity": 1.0,
    }

    def __init__(self, name):
        self.name = name
        profile = self.SECTORS.get(name, self.DEFAULT)
        self.growth_multiplier = profile["growth_multiplier"]
        self.volatility_multiplier = profile["volatility_multiplier"]
        self.pe_multiplier = profile["pe_multiplier"]
        self.sentiment_sensitivity = profile["sentiment_sensitivity"]

    def apply_to_company(self, company):
        company.expected_revenue_growth *= self.growth_multiplier
        company.revenue_volatility *= self.volatility_multiplier
        company.pe_ratio *= self.pe_multiplier
        company.update_fundamental_value()
