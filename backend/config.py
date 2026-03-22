"""
InFinea — Application configuration.
JWT settings, constants, and shared configuration values.
"""

import os

# JWT Config
JWT_SECRET = os.environ.get("JWT_SECRET", "infinea-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Stripe
SUBSCRIPTION_PRICE = 6.99  # EUR
