"""Initialize default data"""
from app.services import AuthService
from app.models import Repository


async def initialize_default_data():
    """Initialize default admin user and data"""
    # Create default admin user
    await AuthService.initialize_admin_user()
    print(">> Default admin user initialized (username: admin, password: admin123)")
    
    # Create default public repository
    await initialize_public_repository()
    print(">> Default public repository 'public' initialized")


async def initialize_public_repository():
    """Initialize default public repository that everyone can pull and push"""
    public_repo = await Repository.get_or_none(name="public")
    if not public_repo:
        public_repo = await Repository.create(
            name="public",
            description="默认公开仓库 - 任何人都可以拉取，登录用户可以推送",
            is_public=True
        )
        print(">> Created default public repository: public")
    else:
        # Ensure it's marked as public
        if not public_repo.is_public:
            public_repo.is_public = True
            await public_repo.save()
            print(">> Updated existing 'public' repository to be public")
    return public_repo

