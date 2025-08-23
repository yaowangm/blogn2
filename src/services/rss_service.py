from typing import List, Dict, Any, Optional
from datetime import datetime
from src.repositories.project_repository import ProjectRepository
from src.repositories.project_item_repository import ProjectItemRepository
from src.repositories.user_repository import UserRepository

class RSSService:
    """RSS服务类
    
    提供全站和博客RSS数据获取功能
    """
    
    def __init__(self, project_repo: ProjectRepository, project_item_repo: ProjectItemRepository, user_repo: UserRepository):
        self.project_repo = project_repo
        self.project_item_repo = project_item_repo
        self.user_repo = user_repo
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成文章摘要
        
        Args:
            content: 文章内容
            max_length: 最大长度
            
        Returns:
            str: 摘要内容
        """
        if not content:
            return ""
        
        # 去除HTML标签
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # 去除多余空白
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        # 如果内容长度在限制内，直接返回
        if len(clean_content) <= max_length:
            return clean_content
        
        # 截取到指定长度，确保不截断单词
        truncated = clean_content[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # 如果截断点太靠前，重新找
            summary = truncated[:last_space]
        else:
            summary = truncated
        
        return summary + "..."
    
    def _format_rss_date(self, date: datetime) -> str:
        """格式化日期为RSS标准格式
        
        Args:
            date: 日期时间
            
        Returns:
            str: RFC 822格式的日期字符串
        """
        if not date:
            return datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # 转换为本地时区并格式化为RFC 822格式
        return date.strftime("%a, %d %b %Y %H:%M:%S %z")
    
    def _extract_image_url(self, content: str) -> str:
        """从文章内容中提取图片URL
        
        Args:
            content: 文章内容
            
        Returns:
            str: 图片URL，如果没有找到则返回空字符串
        """
        if not content:
            return ""
        
        import re
        
        # 查找HTML img标签
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        img_match = re.search(img_pattern, content, re.IGNORECASE)
        if img_match:
            return img_match.group(1)
        
        # 查找Markdown图片语法 ![alt](url)
        md_img_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
        md_img_match = re.search(md_img_pattern, content)
        if md_img_match:
            return md_img_match.group(1)
        
        # 查找纯URL链接（可能是图片）
        url_pattern = r'https?://[^\s<>"\']+\.(jpg|jpeg|png|gif|webp|bmp)'
        url_match = re.search(url_pattern, content, re.IGNORECASE)
        if url_match:
            return url_match.group(0)
        
        return ""
    
    async def get_site_rss_data(self, limit: int = 20) -> Dict[str, Any]:
        """获取全站RSS数据
        
        Args:
            limit: 文章数量限制
            
        Returns:
            Dict[str, Any]: RSS数据
        """
        # 获取最新发布的文章（暂时不限制任何条件）
        articles = await self.project_item_repo.get_recent_articles(limit)
        
        rss_items = []
        for article in articles:
            # 获取作者信息
            author_name = "未知作者"
            if article.get("userid"):
                user = await self.user_repo.get_by_id(article["userid"])
                if user:
                    author_name = user.name or "未知作者"
            
            # 获取博客信息
            project_name = "未知博客"
            if article.get("projectid"):
                project = await self.project_repo.get_by_id(article["projectid"])
                if project:
                    project_name = project.name or "未知博客"
            
            # 生成摘要
            summary = self._generate_summary(article.get("comment", ""))
            
            rss_items.append({
                "title": article.get("name", "无标题"),
                "link": f"/article/{article.get('id', 0)}",
                "description": summary,
                "author": author_name,
                "category": project_name,
                "pub_date": self._format_rss_date(article.get("createtime")),
                "guid": f"/article/{article.get('id', 0)}",
                "content": summary,
                "image_url": self._extract_image_url(article.get("comment", ""))
            })
        
        return {
            "title": "BlogN2 - 全站最新文章",
            "link": "/",
            "description": "聚合所有博客的最新文章",
            "language": "zh-CN",
            "last_build_date": self._format_rss_date(datetime.now()),
            "items": rss_items
        }
    
    async def get_blog_rss_data(self, project_id: int, limit: int = 20) -> Dict[str, Any]:
        """获取指定博客的RSS数据
        
        Args:
            project_id: 博客ID
            limit: 文章数量限制
            
        Returns:
            Dict[str, Any]: RSS数据
        """
        # 获取博客信息
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError("博客不存在")
        
        # 获取该博客下的最新文章（暂时不限制任何条件）
        articles = await self.project_item_repo.get_articles_by_project(project_id, limit)
        
        rss_items = []
        for article in articles:
            # 获取作者信息
            author_name = "未知作者"
            if article.get("userid"):
                user = await self.user_repo.get_by_id(article["userid"])
                if user:
                    author_name = user.name or "未知作者"
            
            # 生成摘要
            summary = self._generate_summary(article.get("comment", ""))
            
            rss_items.append({
                "title": article.get("name", "无标题"),
                "link": f"/article/{article.get('id', 0)}",
                "description": summary,
                "author": author_name,
                "category": "文章",
                "pub_date": self._format_rss_date(article.get("createtime")),
                "guid": f"/article/{article.get('id', 0)}",
                "content": summary,
                "image_url": self._extract_image_url(article.get("comment", ""))
            })
        
        return {
            "title": f"{project.name or '未知博客'} - RSS订阅",
            "link": f"/blog/{project_id}",
            "description": project.comment or "博客RSS订阅",
            "language": "zh-CN",
            "last_build_date": self._format_rss_date(datetime.now()),
            "items": rss_items
        }
