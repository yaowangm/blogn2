from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.repositories.user_repository import UserRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.post_repository import PostRepository

class BlogService:
    """博客业务逻辑服务类
    
    提供博客相关的业务逻辑处理，包括最新加入、最热门、最近评论等功能。
    """
    
    def __init__(self, user_repo: UserRepository, project_item_repo: ProjectItemRepository, project_repo: ProjectRepository, post_repo: PostRepository):
        self.user_repo = user_repo
        self.project_item_repo = project_item_repo
        self.project_repo = project_repo
        self.post_repo = post_repo
    
    async def get_recent_blogs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最新加入的博客（按创建时间倒序）"""
        recent_projects = await self.project_repo.get_recent_projects(limit)
        
        blogs = []
        for project in recent_projects:
            # 格式化创建时间为具体日期
            createtime = project["createtime"]
            if createtime:
                join_date = createtime.strftime("%Y-%m-%d")
            else:
                join_date = "未知日期"
            
            # 计算用户头像路径
            userid = project["userid"]
            if userid:
                prefix = (userid // 10000) + 1
                avatar_path = f"/avatars/{prefix}/s_{userid}.jpg"
            else:
                avatar_path = None
            
            blogs.append({
                "id": project["id"],
                "name": project["name"],
                "join_date": join_date,
                "avatar": avatar_path,
                "userid": userid
            })
        
        return blogs
    
    async def get_popular_blogs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最热门的博客（按访问量排序）"""
        popular_projects = await self.project_repo.get_popular_projects(limit)
        
        blogs = []
        for i, project in enumerate(popular_projects):
            # 格式化访问量
            access_count = project["accesscount"]
            if access_count >= 1000:
                access_str = f"{access_count/1000:.1f}k"
            else:
                access_str = str(access_count)
            
            # 计算用户头像路径
            userid = project["userid"]
            if userid:
                prefix = (userid // 10000) + 1
                avatar_path = f"/avatars/{prefix}/s_{userid}.jpg"
            else:
                avatar_path = None
            
            blogs.append({
                "id": project["id"],
                "name": project["name"],
                "followers": access_str,  # 这里显示的是访问量，但保持字段名兼容
                "avatar": avatar_path,
                "rank": i + 1,
                "author": project["author_name"],
                "userid": userid
            })
        
        return blogs
    
    async def get_recent_comments(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的评论（不包括留言本）"""
        try:
            comments = await self.post_repo.get_recent_comments(limit)
            
            formatted_comments = []
            for comment in comments:
                # 格式化评论时间为具体日期
                post_time = comment["post_time"]
                if post_time:
                    time_str = post_time.strftime("%Y-%m-%d")
                else:
                    time_str = "未知日期"
                
                            # 计算用户头像路径
            userid = comment["userid"]
            if userid:
                prefix = (userid // 10000) + 1
                avatar_path = f"/avatars/{prefix}/s_{userid}.jpg"
            else:
                avatar_path = None
            
            formatted_comments.append({
                "id": comment["id"],
                "author": comment["author_name"],
                "content": comment["content"],
                "time": time_str,
                "projectitemid": comment["projectitemid"],
                "avatar": avatar_path,
                "userid": userid
            })
            
            return formatted_comments
        except Exception as e:
            # 如果查询失败，返回空列表
            print(f"Warning: Could not fetch comments: {e}")
            return [] 