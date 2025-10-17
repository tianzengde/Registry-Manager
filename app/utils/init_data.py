"""初始化默认数据"""
from app.services import AuthService
from app.models import Repository


async def initialize_default_data():
    """初始化默认管理员用户和数据"""
    # 创建默认管理员用户
    await AuthService.initialize_admin_user()
    print(">> 默认管理员用户已初始化 (用户名: admin, 密码: admin123)")
    
    # 创建默认公开仓库
    await initialize_public_repository()
    print(">> 默认公开仓库 'public' 已初始化")


async def initialize_public_repository():
    """初始化默认公开仓库，任何人都可以拉取和推送"""
    public_repo = await Repository.get_or_none(name="public")
    if not public_repo:
        public_repo = await Repository.create(
            name="public",
            description="默认公开仓库 - 任何人都可以拉取，登录用户可以推送",
            is_public=True
        )
        print(">> 已创建默认公开仓库: public")
    else:
        # 确保它被标记为公开
        if not public_repo.is_public:
            public_repo.is_public = True
            await public_repo.save()
            print(">> 已更新现有 'public' 仓库为公开")
    return public_repo

