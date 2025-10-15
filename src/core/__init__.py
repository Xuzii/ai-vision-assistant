"""
Core functionality for AI Vision Assistant
Includes camera management, database setup, and automation
"""

from .database_setup import setup_database, create_user, hash_password, verify_password
from .camera_manager import CameraManager

__all__ = ['setup_database', 'create_user', 'hash_password', 'verify_password', 'CameraManager']
