-- 数据库索引优化脚本
-- 基于src/repositories目录下的查询模式分析
-- 为每个常用查询创建合适的索引以提高性能

-- ==============================================
-- 1. PROJECT 表索引
-- ==============================================

-- 按用户ID查询项目（一对一关系）
CREATE INDEX IF NOT EXISTS idx_project_userid ON project(userid);

-- 按状态查询项目（用于获取正常状态的项目）
CREATE INDEX IF NOT EXISTS idx_project_state ON project(state);

-- 按访问量排序（用于热门项目查询）
CREATE INDEX IF NOT EXISTS idx_project_accesscount ON project(accesscount DESC);

-- 按创建时间排序（用于最新项目查询）
CREATE INDEX IF NOT EXISTS idx_project_createtime ON project(createtime DESC);

-- 复合索引：状态+访问量（用于获取正常状态的热门项目）
CREATE INDEX IF NOT EXISTS idx_project_state_accesscount ON project(state, accesscount DESC);

-- 复合索引：状态+创建时间（用于获取正常状态的最新项目）
CREATE INDEX IF NOT EXISTS idx_project_state_createtime ON project(state, createtime DESC);

-- ==============================================
-- 2. PROJECTITEM 表索引
-- ==============================================

-- 按项目ID查询文章
CREATE INDEX IF NOT EXISTS idx_projectitem_projectid ON projectitem(projectid);

-- 按用户ID查询文章
CREATE INDEX IF NOT EXISTS idx_projectitem_userid ON projectitem(userid);

-- 按分类ID查询文章
CREATE INDEX IF NOT EXISTS idx_projectitem_folderid ON projectitem(folderid);

-- 按状态查询文章（用于获取正常状态的文章）
CREATE INDEX IF NOT EXISTS idx_projectitem_status ON projectitem(status);

-- 按创建时间排序（用于最新文章查询）
CREATE INDEX IF NOT EXISTS idx_projectitem_createtime ON projectitem(createtime DESC);

-- 按访问量排序（用于热门文章查询）
CREATE INDEX IF NOT EXISTS idx_projectitem_accesscount ON projectitem(accesscount DESC);

-- 复合索引：项目ID+状态（用于获取指定项目的正常文章）
CREATE INDEX IF NOT EXISTS idx_projectitem_projectid_status ON projectitem(projectid, status);

-- 复合索引：项目ID+分类ID+状态（用于获取指定项目指定分类的文章）
CREATE INDEX IF NOT EXISTS idx_projectitem_projectid_folderid_status ON projectitem(projectid, folderid, status);

-- 复合索引：项目ID+创建时间（用于获取指定项目的最新文章）
CREATE INDEX IF NOT EXISTS idx_projectitem_projectid_createtime ON projectitem(projectid, createtime DESC);

-- 复合索引：状态+创建时间（用于获取所有正常状态的最新文章）
CREATE INDEX IF NOT EXISTS idx_projectitem_status_createtime ON projectitem(status, createtime DESC);

-- 复合索引：项目ID+状态+创建时间（用于分页查询）
CREATE INDEX IF NOT EXISTS idx_projectitem_projectid_status_createtime ON projectitem(projectid, status, createtime DESC);

-- ==============================================
-- 3. FOLDERS 表索引
-- ==============================================

-- 按项目ID查询分类
CREATE INDEX IF NOT EXISTS idx_folders_projectid ON folders(projectid);

-- 按项目ID+ID排序（用于获取指定项目的分类列表）
CREATE INDEX IF NOT EXISTS idx_folders_projectid_id ON folders(projectid, id DESC);

-- ==============================================
-- 4. POST 表索引
-- ==============================================

-- 按项目项ID查询评论（最常用的查询）
CREATE INDEX IF NOT EXISTS idx_post_projectitemid ON post(projectitemid);

-- 按用户ID查询评论
CREATE INDEX IF NOT EXISTS idx_post_userid ON post(userid);

-- 按根评论ID查询回复（用于获取评论的回复）
CREATE INDEX IF NOT EXISTS idx_post_rootid ON post(rootid);

-- 按状态查询评论
CREATE INDEX IF NOT EXISTS idx_post_status ON post(status);

-- 按发布时间排序（用于获取最新评论）
CREATE INDEX IF NOT EXISTS idx_post_posttime ON post(posttime DESC);

-- 复合索引：项目项ID+发布时间（用于分页查询评论）
CREATE INDEX IF NOT EXISTS idx_post_projectitemid_posttime ON post(projectitemid, posttime DESC);

-- 复合索引：项目项ID+状态+发布时间（用于获取正常状态的最新评论）
CREATE INDEX IF NOT EXISTS idx_post_projectitemid_status_posttime ON post(projectitemid, status, posttime DESC);

-- 复合索引：根评论ID+发布时间（用于获取回复按时间排序）
CREATE INDEX IF NOT EXISTS idx_post_rootid_posttime ON post(rootid, posttime ASC);

-- 复合索引：项目项ID>0+发布时间（用于获取非留言本的评论）
CREATE INDEX IF NOT EXISTS idx_post_projectitemid_gt0_posttime ON post(projectitemid, posttime DESC) WHERE projectitemid > 0;

-- 复合索引：项目项ID=0+根评论ID=0+发布时间（用于获取留言本主贴）
CREATE INDEX IF NOT EXISTS idx_post_guestbook_main ON post(projectitemid, rootid, posttime DESC) WHERE projectitemid = 0 AND rootid = 0;

-- 复合索引：项目项ID=0+根评论ID+发布时间（用于获取留言本回复）
CREATE INDEX IF NOT EXISTS idx_post_guestbook_replies ON post(projectitemid, rootid, posttime ASC) WHERE projectitemid = 0;

-- ==============================================
-- 5. USERS 表索引
-- ==============================================

-- 按邮箱查询用户（用于登录验证）
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 按用户名查询用户（用于登录验证）
CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);

-- 按状态查询用户（用于获取活跃用户）
CREATE INDEX IF NOT EXISTS idx_users_state ON users(state);

-- 按注册时间排序（用于获取最新用户）
CREATE INDEX IF NOT EXISTS idx_users_regtime ON users(regtime DESC);

-- 按积分排序（用于获取热门用户）
CREATE INDEX IF NOT EXISTS idx_users_point ON users(point DESC);

-- 复合索引：状态+积分（用于获取活跃用户按积分排序）
CREATE INDEX IF NOT EXISTS idx_users_state_point ON users(state, point DESC);

-- 复合索引：状态+注册时间（用于获取活跃用户按注册时间排序）
CREATE INDEX IF NOT EXISTS idx_users_state_regtime ON users(state, regtime DESC);

-- 复合索引：用户名模糊查询（用于搜索用户）
CREATE INDEX IF NOT EXISTS idx_users_name_lower ON users(LOWER(name));

-- ==============================================
-- 6. SUBSC 表索引（订阅表）
-- ==============================================

-- 按项目ID查询订阅
CREATE INDEX IF NOT EXISTS idx_subsc_projectid ON subsc(projectid);

-- 按文章ID查询订阅
CREATE INDEX IF NOT EXISTS idx_subsc_piid ON subsc(piid);

-- 复合索引：项目ID+文章ID（用于检查是否已订阅）
CREATE INDEX IF NOT EXISTS idx_subsc_projectid_piid ON subsc(projectid, piid);

-- ==============================================
-- 7. RELATION 表索引
-- ==============================================

-- 按项目ID查询关系
CREATE INDEX IF NOT EXISTS idx_relation_projectid ON relation(projectid);

-- 按对象ID查询关系
CREATE INDEX IF NOT EXISTS idx_relation_objectid ON relation(objectid);

-- 按活动类型查询关系
CREATE INDEX IF NOT EXISTS idx_relation_acttype ON relation(acttype);

-- 复合索引：项目ID+活动类型（用于获取订阅关系）
CREATE INDEX IF NOT EXISTS idx_relation_projectid_acttype ON relation(projectid, acttype);

-- 复合索引：对象ID+活动类型（用于获取订阅者）
CREATE INDEX IF NOT EXISTS idx_relation_objectid_acttype ON relation(objectid, acttype);

-- 复合索引：项目ID+活动类型+创建时间（用于分页查询订阅的博客）
CREATE INDEX IF NOT EXISTS idx_relation_projectid_acttype_created ON relation(projectid, acttype, created DESC);

-- ==============================================
-- 8. ATTACHMENT 表索引
-- ==============================================

-- 按父级ID查询附件（文章ID）
CREATE INDEX IF NOT EXISTS idx_attachment_parentid ON attachment(parentid);

-- 按创建时间排序（用于获取附件按时间排序）
CREATE INDEX IF NOT EXISTS idx_attachment_createtime ON attachment(createtime);

-- ==============================================
-- 9. URLLINK 表索引
-- ==============================================

-- 按项目ID查询友情链接
CREATE INDEX IF NOT EXISTS idx_urllink_projectid ON urllink(projectid);

-- 按排序号排序（用于获取友情链接按顺序排列）
CREATE INDEX IF NOT EXISTS idx_urllink_ordernum ON urllink(ordernum);

-- 复合索引：项目ID+排序号（用于获取指定项目的友情链接按顺序排列）
CREATE INDEX IF NOT EXISTS idx_urllink_projectid_ordernum ON urllink(projectid, ordernum);

-- ==============================================
-- 10. GLOVAR 表索引
-- ==============================================

-- 按变量名查询（用于获取全局变量）
CREATE INDEX IF NOT EXISTS idx_glovar_varname ON glovar(varname);

-- ==============================================
-- 11. 外键约束索引（如果不存在）
-- ==============================================

-- 这些索引通常由外键约束自动创建，但为了确保性能，我们显式创建

-- project.userid -> users.id
-- 已在上面创建：idx_project_userid

-- projectitem.projectid -> project.id  
-- 已在上面创建：idx_projectitem_projectid

-- projectitem.userid -> users.id
-- 已在上面创建：idx_projectitem_userid

-- projectitem.folderid -> folders.id
-- 已在上面创建：idx_projectitem_folderid

-- folders.projectid -> project.id
-- 已在上面创建：idx_folders_projectid

-- post.userid -> users.id
-- 已在上面创建：idx_post_userid

-- post.projectitemid -> projectitem.id
-- 已在上面创建：idx_post_projectitemid

-- subsc.projectid -> project.id
-- 已在上面创建：idx_subsc_projectid

-- subsc.piid -> projectitem.id
-- 已在上面创建：idx_subsc_piid

-- relation.projectid -> project.id
-- 已在上面创建：idx_relation_projectid

-- relation.objectid -> project.id
-- 已在上面创建：idx_relation_objectid

-- attachment.parentid -> projectitem.id
-- 已在上面创建：idx_attachment_parentid

-- urllink.projectid -> project.id
-- 已在上面创建：idx_urllink_projectid

-- ==============================================
-- 索引创建完成说明
-- ==============================================

-- 本脚本基于以下查询模式创建索引：
-- 1. 主键查询（通常已有主键索引）
-- 2. 外键查询（JOIN操作）
-- 3. WHERE条件查询
-- 4. ORDER BY排序查询
-- 5. 复合条件查询
-- 6. 分页查询
-- 7. 模糊查询（LIKE操作）

-- 注意事项：
-- 1. 所有索引都使用 IF NOT EXISTS 避免重复创建
-- 2. 复合索引的字段顺序基于查询的选择性和使用频率
-- 3. 部分索引使用 WHERE 条件优化特定查询
-- 4. 字符串字段的模糊查询使用 LOWER() 函数索引
-- 5. 排序字段通常使用 DESC 索引以提高倒序查询性能
