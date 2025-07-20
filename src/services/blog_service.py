from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
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
    
    def _check_avatar_exists(self, userid: int) -> str | None:
        """检查用户头像文件是否存在
        
        Args:
            userid: 用户ID
            
        Returns:
            str | None: 如果头像存在返回路径，否则返回None
        """
        if not userid:
            return None
            
        prefix = (userid // 10000) + 1
        avatar_path = f"/avatars/{prefix}/s_{userid}.jpg"
        real_path = f"/home/wy/pic/blogn_img/userlogo/{prefix}/s_{userid}.jpg"
        
        # 检查文件是否存在
        if os.path.exists(real_path):
            return avatar_path
        else:
            return None
    
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
            
            # 检查用户头像是否存在
            userid = project["userid"]
            avatar_path = self._check_avatar_exists(userid)
            
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
            
            # 检查用户头像是否存在
            userid = project["userid"]
            avatar_path = self._check_avatar_exists(userid)
            
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
                
                # 检查用户头像是否存在
                userid = comment["userid"]
                avatar_path = self._check_avatar_exists(userid)
            
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
    
    async def get_about_content(self) -> Dict[str, Any]:
        """获取关于页面的内容（来自ID为486的projectitem记录）"""
        try:
            project_item = await self.project_item_repo.get_by_id(486)
            
            if not project_item:
                return {
                    "title": "Why Blogn",
                    "content": "内容暂不可用",
                    "link": None
                }
            
            # 处理内容：转换换行符并截断到300字符
            content = project_item.comment or ""
            
            # 转换换行符为HTML的<br>标签
            content = content.replace('\r\n', '<br>').replace('\n', '<br>').replace('\r', '<br>')
            
            # 截断内容到300字符（在HTML标签之前）
            if len(content) > 300:
                # 找到300字符位置，但不要截断在HTML标签中间
                truncate_pos = 300
                while truncate_pos > 0 and content[truncate_pos-1:truncate_pos+3] != '<br>':
                    truncate_pos -= 1
                    if truncate_pos <= 0:
                        truncate_pos = 300
                        break
                
                content = content[:truncate_pos] + "..."
            
            return {
                "title": "Why Blogn",
                "content": content,
                "link": f"/projectitem/{project_item.id}"
            }
        except Exception as e:
            # 如果查询失败，返回默认内容
            print(f"Warning: Could not fetch about content: {e}")
            return {
                "title": "Why Blogn",
                "content": "内容暂不可用",
                "link": None
            } 