"""
InFinea — Database connection module.
Single source of truth for the MongoDB client and database instance.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
