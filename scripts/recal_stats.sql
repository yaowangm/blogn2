-- 重新计算统计字段的SQL语句
-- 注意：这些UPDATE语句会修改数据，请谨慎执行

-- 1. 更新 post.replycount - 评论的回复数
UPDATE post 
SET replycount = (
    SELECT COUNT(*)
    FROM post p2 
    WHERE p2.rootid = post.id
);

-- 2. 更新 projectitem.commentcount - 博客文章的评论数
UPDATE projectitem 
SET commentcount = (
    SELECT COUNT(*) 
    FROM post 
    WHERE post.projectitemid = projectitem.id
);

-- 3. 更新 folders.recordcount - 当前分类的博客文章数
UPDATE folders 
SET recordcount = (
    SELECT COUNT(*) 
    FROM projectitem 
    WHERE projectitem.folderid = folders.id
);

-- 4. 更新 folders.postcount - 当前分类的评论数
UPDATE folders 
SET postcount = (
    SELECT COUNT(*) 
    FROM post 
    LEFT JOIN projectitem ON post.projectitemid = projectitem.id 
    WHERE projectitem.folderid = folders.id
);

-- 5. 更新 project.recordcount - 博客中所有的博客文章数
UPDATE project 
SET recordcount = (
    SELECT COUNT(*) 
    FROM projectitem 
    WHERE projectitem.projectid = project.id
);

-- 6. 更新 project.accesscount - 博客中所有的博客文章的点击总数
UPDATE project 
SET accesscount = (
    SELECT COALESCE(SUM(accesscount), 0) 
    FROM projectitem 
    WHERE projectitem.projectid = project.id
);

-- 7. 更新 project.commentcount - 博客中所有的博客文章的评论总数
UPDATE project 
SET commentcount = (
    SELECT COUNT(*) 
    FROM post 
    LEFT JOIN projectitem ON post.projectitemid = projectitem.id 
    WHERE projectitem.projectid = project.id
);

-- 8. 更新 glovar.usercount - 所有用户的数量
UPDATE glovar 
SET varvalue = (SELECT COUNT(*) FROM users) 
WHERE varname = 'usercount';

-- 9. 更新 glovar.projectcount - 所有博客的数量
UPDATE glovar 
SET varvalue = (SELECT COUNT(*) FROM project) 
WHERE varname = 'projectcount';

-- 10. 更新 glovar.projectitemcount - 所有博客文章的数量
UPDATE glovar 
SET varvalue = (SELECT COUNT(*) FROM projectitem) 
WHERE varname = 'projectitemcount';