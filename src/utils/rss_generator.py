from typing import Dict, Any
from datetime import datetime

class RSSGenerator:
    """RSS生成器
    
    将RSS数据转换为标准RSS 2.0 XML格式
    """
    
    def __init__(self, base_url: str = ""):
        self.base_url = base_url
    
    def _escape_xml(self, text: str) -> str:
        """转义XML特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 转义后的文本
        """
        if not text:
            return ""
        
        # XML特殊字符转义
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        
        return text
    
    def _make_absolute_url(self, url: str) -> str:
        """将相对URL转换为绝对URL
        
        Args:
            url: 相对URL
            
        Returns:
            str: 绝对URL
        """
        if not url:
            return self.base_url
        
        if url.startswith("http"):
            return url
        
        if url.startswith("/"):
            return f"{self.base_url}{url}"
        
        return f"{self.base_url}/{url}"
    
    def generate_rss_xml(self, rss_data: Dict[str, Any]) -> str:
        """生成RSS 2.0 XML内容
        
        Args:
            rss_data: RSS数据
            
        Returns:
            str: RSS XML内容
        """
        # 构建channel标签
        channel_content = f"""    <title>{self._escape_xml(rss_data.get('title', ''))}</title>
    <link>{self._make_absolute_url(rss_data.get('link', ''))}</link>
    <description>{self._escape_xml(rss_data.get('description', ''))}</description>
    <language>{rss_data.get('language', 'zh-CN')}</language>
    <lastBuildDate>{rss_data.get('last_build_date', '')}</lastBuildDate>
    <generator>BlogN2 RSS Generator</generator>
    <ttl>1440</ttl>"""
        
        # 构建item标签
        items_content = ""
        for item in rss_data.get('items', []):
            # 构建图片链接（如果有的话）
            image_content = ""
            if item.get('image_url'):
                image_content = f"""
            <enclosure url="{self._make_absolute_url(item.get('image_url'))}" type="image/jpeg" length="0" />"""
            
            item_content = f"""
        <item>
            <title>{self._escape_xml(item.get('title', ''))}</title>
            <link>{self._make_absolute_url(item.get('link', ''))}</link>
            <description>{self._escape_xml(item.get('description', ''))}</description>
            <author>{self._escape_xml(item.get('author', ''))}</author>
            <category>{self._escape_xml(item.get('category', ''))}</category>
            <pubDate>{item.get('pub_date', '')}</pubDate>
            <guid>{self._make_absolute_url(item.get('guid', ''))}</guid>{image_content}
        </item>"""
            items_content += item_content
        
        # 组装完整的RSS XML
        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
{channel_content}{items_content}
</channel>
</rss>"""
        
        return rss_xml
    
    def generate_rss_xml_with_content(self, rss_data: Dict[str, Any]) -> str:
        """生成包含完整内容的RSS 2.0 XML
        
        Args:
            rss_data: RSS数据
            
        Returns:
            str: RSS XML内容
        """
        # 构建channel标签
        channel_content = f"""    <title>{self._escape_xml(rss_data.get('title', ''))}</title>
    <link>{self._make_absolute_url(rss_data.get('link', ''))}</link>
    <description>{self._escape_xml(rss_data.get('description', ''))}</description>
    <language>{rss_data.get('language', 'zh-CN')}</language>
    <lastBuildDate>{rss_data.get('last_build_date', '')}</lastBuildDate>
    <generator>BlogN2 RSS Generator</generator>
    <ttl>1440</ttl>"""
        
        # 构建item标签（包含完整内容）
        items_content = ""
        for item in rss_data.get('items', []):
            # 构建图片链接（如果有的话）
            image_content = ""
            if item.get('image_url'):
                image_content = f"""
            <enclosure url="{self._make_absolute_url(item.get('image_url'))}" type="image/jpeg" length="0" />"""
            
            item_content = f"""
        <item>
            <title>{self._escape_xml(item.get('title', ''))}</title>
            <link>{self._make_absolute_url(item.get('link', ''))}</link>
            <description>{self._escape_xml(item.get('description', ''))}</description>
            <content:encoded><![CDATA[{item.get('content', '')}]]></content:encoded>
            <author>{self._escape_xml(item.get('author', ''))}</author>
            <category>{self._escape_xml(item.get('category', ''))}</category>
            <pubDate>{item.get('pub_date', '')}</pubDate>
            <guid>{self._make_absolute_url(item.get('guid', ''))}</guid>{image_content}
        </item>"""
            items_content += item_content
        
        # 组装完整的RSS XML
        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
{channel_content}{items_content}
</channel>
</rss>"""
        
        return rss_xml
