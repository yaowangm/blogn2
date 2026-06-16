from typing import List, Dict, Any, Optional
from datetime import datetime
from src.repositories.project_repository import ProjectRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.user_repository import UserRepository
from src.utils.time_utils import TimeUtils

class RSSService:
    """RSS服务类
    
    提供全站和博客RSS数据获取功能
    """
    
    def __init__(self, project_repo: ProjectRepository, project_item_repo: ProjectItemRepository, user_repo: UserRepository):
        self.project_repo = project_repo
        self.project_item_repo = project_item_repo
        self.user_repo = user_repo
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成文章摘要"""
        if not content:
            return ""
        
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        if len(clean_content) <= max_length:
            return clean_content
        
        truncated = clean_content[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:
            summary = truncated[:last_space]
        else:
            summary = truncated
        
        return summary + "..."
    
    def _format_rss_date(self, date: datetime) -> str:
        """格式化日期为RSS标准格式"""
        if not date:
            return TimeUtils.now_utc().strftime("%a, %d %b %Y %H:%M:%S %z")
        
        return date.strftime("%a, %d %b %Y %H:%M:%S %z")
    
    def _extract_image_url(self, content: str, attachment: str | None = None) -> str:
        """从文章内容或附件字段中提取图片URL"""
        if attachment:
            return f"/upload/{attachment}"
        
        if not content:
            return ""
        
        import re
        
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        img_match = re.search(img_pattern, content, re.IGNORECASE)
        if img_match:
            return img_match.group(1)
        
        md_img_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
        md_img_match = re.search(md_img_pattern, content)
        if md_img_match:
            return md_img_match.group(1)
        
        url_pattern = r'https?://[^\s<>"\']+\.(jpg|jpeg|png|gif|webp|bmp)'
        url_match = re.search(url_pattern, content, re.IGNORECASE)
        if url_match:
            return url_match.group(0)
        
        return ""
    
    async def get_site_rss_data(self, limit: int = 20) -> Dict[str, Any]:
        """获取全站RSS数据"""
        articles = await self.project_item_repo.get_recent_articles(limit)
        
        rss_items = []
        for article in articles:
            summary = self._generate_summary(article.get("comment", ""))
            
            rss_items.append({
                "title": article.get("name", "无标题"),
                "link": f"/article/{article.get('id', 0)}",
                "description": summary,
                "author": article.get("author_name") or "未知作者",
                "category": article.get("project_name") or "未知博客",
                "pub_date": self._format_rss_date(article.get("createtime")),
                "guid": f"/article/{article.get('id', 0)}",
                "content": summary,
                "image_url": self._extract_image_url(article.get("comment", ""), article.get("attachment")),
            })
        
        return {
            "title": "BlogN2 - 全站最新文章",
            "link": "/",
            "description": "聚合所有博客的最新文章",
            "language": "zh-CN",
            "last_build_date": self._format_rss_date(TimeUtils.now_utc()),
            "items": rss_items
        }
    
    async def get_blog_rss_data(self, project_id: int, limit: int = 20) -> Dict[str, Any]:
        """获取指定博客的RSS数据"""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError("博客不存在")
        
        articles = await self.project_item_repo.get_articles_by_project(project_id, limit)
        
        rss_items = []
        for article in articles:
            summary = self._generate_summary(article.get("comment", ""))
            
            rss_items.append({
                "title": article.get("name", "无标题"),
                "link": f"/article/{article.get('id', 0)}",
                "description": summary,
                "author": article.get("author_name") or "未知作者",
                "category": "文章",
                "pub_date": self._format_rss_date(article.get("createtime")),
                "guid": f"/article/{article.get('id', 0)}",
                "content": summary,
                "image_url": self._extract_image_url(article.get("comment", ""), article.get("attachment")),
            })
        
        return {
            "title": f"{project.name or '未知博客'} - RSS订阅",
            "link": f"/blog/{project_id}",
            "description": project.comment or "博客RSS订阅",
            "language": "zh-CN",
            "last_build_date": self._format_rss_date(TimeUtils.now_utc()),
            "items": rss_items
        }
