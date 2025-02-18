"""
Configuration settings for the Flask Blog API application.

This module handles loading environment variables, setting up paths,
and defining configuration parameters for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Determine the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
if not env_path.exists():
    raise FileNotFoundError(
        f"Environment file not found at {env_path}. "
        "Please create a .env file with required configuration."
    )

load_dotenv(env_path)


class Config:
    """
    Application configuration class.

    Contains all configuration parameters for the application,
    including paths, API settings, and runtime options.

    Attributes:
        BASE_DIR (Path): Base directory path
        API_KEY (str): API key for authentication
        DEBUG (bool): Debug mode flag
        RATE_LIMITS (list): Rate limiting rules
        STORAGE_FILE (Path): Path to JSON storage file
    """

    # Directory and file paths
    BASE_DIR = BASE_DIR
    STORAGE_FILE = BASE_DIR / "posts_storage.json"

    # API and security settings
    API_KEY = os.getenv("API_KEY")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Rate limiting settings
    RATE_LIMITS = os.getenv("RATE_LIMITS", "20 per minute").split(",")