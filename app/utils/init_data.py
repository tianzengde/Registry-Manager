"""Initialize default data"""
from app.services import AuthService


async def initialize_default_data():
    """Initialize default admin user and data"""
    # Create default admin user
    await AuthService.initialize_admin_user()
    print(">> Default admin user initialized (username: admin, password: admin123)")

