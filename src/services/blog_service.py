from typing import List, Dict, Any, Optional
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
        avatar_path = f"/avatar/{prefix}/s_{userid}.jpg"
        real_path = f"../pic/blogn_img/userlogo/{prefix}/s_{userid}.jpg"
        
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
            # 格式化创建时间
            createtime = project["createtime"]
            if createtime:
                join_date = self._format_relative_time(createtime)
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
                # 格式化评论时间
                post_time = comment["post_time"]
                if post_time:
                    time_str = self._format_relative_time(post_time)
                else:
                    time_str = "未知时间"
                
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
    
    async def get_recent_messages(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的留言本记录"""
        try:
            messages = await self.post_repo.get_recent_messages(limit)
            
            formatted_messages = []
            for message in messages:
                # 格式化留言时间为相对时间
                post_time = message["post_time"]
                if post_time:
                    time_str = self._format_relative_time(post_time)
                else:
                    time_str = "未知时间"
                
                # 检查用户头像是否存在
                userid = message["userid"]
                avatar_path = self._check_avatar_exists(userid)
                
                # 处理留言标题
                subject = message["subject"] or "无标题"
                if len(subject) > 50:
                    subject = subject[:50] + "..."
                
                # 处理回复信息
                reply_info = ""
                if message["last_reply_author"]:
                    reply_info = f"最后回复: {message['last_reply_author']}"
                elif message["reply_count"] > 0:
                    reply_info = f"回复数: {message['reply_count']}"
                
                formatted_messages.append({
                    "id": message["id"],
                    "author": message["author_name"],
                    "subject": subject,
                    "time": time_str,
                    "avatar": avatar_path,
                    "userid": userid,
                    "reply_info": reply_info,
                    "reply_count": message["reply_count"]
                })
            
            return formatted_messages
        except Exception as e:
            # 如果查询失败，返回空列表
            print(f"Warning: Could not fetch messages: {e}")
            return []

    async def get_messages_list(self, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """获取留言本分页列表"""
        try:
            # 计算偏移量
            offset = (page - 1) * limit
            
            # 获取总数
            total = await self.post_repo.count_messages()
            
            # 获取分页数据
            messages = await self.post_repo.get_messages_paginated(limit, offset)
            
            formatted_messages = []
            for message in messages:
                # 格式化留言时间
                post_time = message["post_time"]
                if post_time:
                    time_str = self._format_relative_time(post_time)
                else:
                    time_str = "未知时间"
                
                # 格式化最后回复时间
                last_reply_time = message.get("last_reply_time")
                last_reply_time_str = ""
                if last_reply_time:
                    last_reply_time_str = self._format_relative_time(last_reply_time)
                
                formatted_messages.append({
                    "id": message["id"],
                    "author": message["author_name"],
                    "subject": message["subject"] or "无标题",
                    "post_time": time_str,
                    "last_reply_author": message.get("last_reply_author"),
                    "last_reply_time": last_reply_time_str,
                    "size": message.get("size", 0),
                    "hits": message.get("hits", 0),
                    "reply_count": message.get("reply_count", 0),
                    "userid": message["userid"]
                })
            
            # 计算总页数
            total_pages = (total + limit - 1) // limit
            
            return {
                "messages": formatted_messages,
                "total": total,
                "current_page": page,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages
            }
        except Exception as e:
            # 如果查询失败，返回空数据
            print(f"Warning: Could not fetch messages list: {e}")
            return {
                "messages": [],
                "total": 0,
                "current_page": page,
                "total_pages": 0,
                "has_prev": False,
                "has_next": False
            }

    async def get_thread(self, thread_id: int) -> Dict[str, Any]:
        """获取主题的所有留言"""
        try:
            messages = await self.post_repo.get_thread_messages(thread_id)
            
            formatted_messages = []
            for message in messages:
                # 格式化留言时间
                post_time = message["post_time"]
                if post_time:
                    time_str = self._format_relative_time(post_time)
                else:
                    time_str = "未知时间"
                
                formatted_messages.append({
                    "id": message["id"],
                    "author": message["author_name"],
                    "subject": message["subject"] or "无标题",
                    "content": message["content"] or "",
                    "post_time": time_str,
                    "is_main_post": message["is_main_post"],
                    "userid": message["userid"]
                })
            
            return {
                "messages": formatted_messages,
                "thread_id": thread_id
            }
        except Exception as e:
            # 如果查询失败，返回空数据
            print(f"Warning: Could not fetch thread {thread_id}: {e}")
            return {
                "messages": [],
                "thread_id": thread_id
            }

    
    async def get_latest_posts(self, page: int = 1, page_size: int = 10, exclude: Optional[int] = None, blogid: Optional[int] = None) -> Dict[str, Any]:
        """获取最新的博文记录（支持分页）"""
        try:
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 获取总数
            total = await self.project_item_repo.get_posts_count(exclude, blogid)
            
            # 获取分页数据
            posts = await self.project_item_repo.get_latest_posts(page_size, exclude, blogid, offset)
            
            formatted_posts = []
            for post in posts:
                # 格式化创建时间
                createtime = post["createtime"]
                if createtime:
                    time_str = self._format_relative_time(createtime)
                else:
                    time_str = "未知时间"
                
                # 检查用户头像是否存在
                userid = post["userid"]
                avatar_path = self._check_avatar_exists(userid)
                
                # 处理博文标题
                title = post["name"] or "无标题"
                if len(title) > 50:
                    title = title[:50] + "..."
                
                # 处理博文摘要
                excerpt = post["comment"] or ""
                if len(excerpt) > 100:
                    excerpt = excerpt[:100] + "..."
                
                # 处理附件图片路径
                image_path = None
                if post["attachment"]:
                    image_path = f"/upload/{post['attachment']}"
                
                formatted_posts.append({
                    "id": post["id"],
                    "title": title,
                    "excerpt": excerpt,
                    "author": post["author_name"],
                    "blog_name": post["blog_name"],
                    "blog_id": post["blog_id"],
                    "time": time_str,
                    "avatar": avatar_path,
                    "userid": post["userid"],
                    "image": image_path
                })
            
            return {
                "posts": formatted_posts,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            # 如果查询失败，返回空列表
            print(f"Warning: Could not fetch latest posts: {e}")
            return {
                "posts": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def _format_relative_time(self, post_time: datetime) -> str:
        """格式化时间显示"""
        now = datetime.now()
        diff = now - post_time
        
        # 如果是今天，显示相对时间
        if diff.days == 0:
            if diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours}小时前"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes}分钟前"
            else:
                return "刚刚"
        # 如果是昨天，显示"昨天"
        elif diff.days == 1:
            return "昨天"
        # 如果是前天，显示"前天"
        elif diff.days == 2:
            return "前天"
        # 其他情况显示具体日期
        else:
            return post_time.strftime("%Y-%m-%d") 