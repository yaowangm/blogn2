# BlogN2 数据库表结构（数据字典）

## 概述

本文档详细描述了BlogN2博客系统的数据库表结构，包括所有表的字段定义、数据类型、约束条件和备注说明。

## 表结构说明

### 1. 用户表 (users)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，用户ID |
| name | VARCHAR(50) | NOT NULL | - | 用户名 |
| password | VARCHAR(60) | NOT NULL | - | 密码（加密存储） |
| state | INTEGER | NOT NULL | 1 | 用户状态：1=正常，0=冻结，10=管理员 |
| email | VARCHAR(50) | NOT NULL | - | 邮箱地址 |
| regtime | DATETIME | NOT NULL | - | 注册时间 |
| iplog | VARCHAR(15) | NULL | NULL | IP日志 |
| point | INTEGER | NULL | 0 | 用户积分 |
| lastupdate | DATETIME | NULL | NULL | 最后更新时间 |
| intropiid | INTEGER | NULL | NULL | 介绍文章ID |
| projectid | INTEGER | NULL | NULL | 项目ID（继承自ProjectMixin） |

### 2. 项目表 (project)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，项目ID |
| name | VARCHAR(100) | NOT NULL | - | 项目名称 |
| comment | TEXT | NULL | NULL | 项目描述 |
| recordcount | INTEGER | NULL | NULL | 记录数量 |
| lastitem | INTEGER | NULL | NULL | 最后条目ID |
| state | INTEGER | NULL | 0 | 博客状态：`0`=正常（`ProjectStatus.ACTIVE`），`1`=禁用（`ProjectStatus.DISABLED`）。生产库均为 `0`。与 `users.state`、`status` 字段的 `1=正常` 约定不同，代码中请使用 `ProjectStatus` 常量 |
| createtime | DATETIME | NULL | NULL | 创建时间（继承自TimestampMixin） |
| updatetime | DATETIME | NULL | NULL | 更新时间（继承自TimestampMixin） |
| userid | INTEGER | NULL | NULL | 用户ID（继承自UserMixin） |
| folderid | INTEGER | NULL | NULL | 文件夹ID（继承自FolderMixin） |
| accesscount | INTEGER | NULL | 0 | 访问次数（继承自CountMixin） |
| commentcount | INTEGER | NULL | 0 | 评论数量（继承自CountMixin） |

### 3. 项目条目表 (projectitem)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，条目ID |
| name | VARCHAR(100) | NOT NULL | - | 条目名称 |
| comment | TEXT | NULL | NULL | 条目内容 |
| itemtype | INTEGER | NULL | NULL | 条目类型 |
| itemsize | INTEGER | NULL | NULL | 条目大小（字节） |
| attachment | VARCHAR(200) | NULL | NULL | 附件路径 |
| linkstr | VARCHAR(200) | NULL | NULL | 链接字符串 |
| lastmodifytime | DATETIME | NULL | NULL | 最后修改时间 |
| allowpost | INTEGER | NULL | NULL | 是否允许评论：1=允许，2=仅登录用户，3=不允许 |
| createtime | DATETIME | NULL | NULL | 创建时间（继承自TimestampMixin） |
| updatetime | DATETIME | NULL | NULL | 更新时间（继承自TimestampMixin） |
| status | INTEGER | NULL | 1 | 状态：1=正常，0=禁用（继承自StatusMixin） |
| userid | INTEGER | NULL | NULL | 用户ID（继承自UserMixin） |
| folderid | INTEGER | NULL | NULL | 文件夹ID（继承自FolderMixin） |
| projectid | INTEGER | NULL | NULL | 项目ID（继承自ProjectMixin） |
| accesscount | INTEGER | NULL | 0 | 访问次数（继承自CountMixin） |
| commentcount | INTEGER | NULL | 0 | 评论数量（继承自CountMixin） |

### 4. 评论/帖子表 (post)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，评论ID |
| rootid | INTEGER | NULL | NULL | 根评论ID |
| subject | VARCHAR(200) | NULL | NULL | 主题 |
| content | TEXT | NULL | NULL | 内容 |
| size | INTEGER | NULL | NULL | 内容大小（字节） |
| hits | INTEGER | NULL | NULL | 点击数 |
| posttime | DATETIME | NULL | NULL | 发布时间 |
| lastreplytime | DATETIME | NULL | NULL | 最后回复时间 |
| lastreplyid | INTEGER | NULL | NULL | 最后回复ID |
| projectitemid | INTEGER | NULL | NULL | 项目条目ID：0表示留言本，>0表示博文评论 |
| replycount | INTEGER | NULL | NULL | 回复数量 |
| userip | VARCHAR(15) | NULL | NULL | 用户IP地址 |
| status | INTEGER | NULL | 1 | 状态：1=正常，0=禁用（继承自StatusMixin） |
| userid | INTEGER | NULL | NULL | 用户ID（继承自UserMixin） |
| folderid | INTEGER | NULL | NULL | 文件夹ID（继承自FolderMixin） |

### 5. 文件夹表 (folders)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，文件夹ID |
| name | VARCHAR(100) | NOT NULL | - | 文件夹名称 |
| parent | INTEGER | NULL | NULL | 父文件夹ID（外键：folders.id） |
| projectid | INTEGER | NULL | NULL | 项目ID（外键：project.id） |
| recordcount | INTEGER | NULL | NULL | 记录数量 |
| postcount | INTEGER | NULL | NULL | 帖子数量 |

### 6. 附件表 (attachment)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | BIGINT | NOT NULL | - | 主键，附件ID |
| parentid | BIGINT | NOT NULL | - | 关联的文章ID |
| amtype | INTEGER | NULL | NULL | 附件类型 |
| comment | VARCHAR(200) | NULL | NULL | 图片注释/描述 |
| linkstr | VARCHAR(200) | NOT NULL | - | 图片链接路径 |
| createtime | DATETIME | NULL | NULL | 创建时间 |
| updatetime | DATETIME | NULL | NULL | 更新时间 |

### 7. 全局变量表 (glovar)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，变量ID |
| varname | VARCHAR(50) | NOT NULL | - | 变量名 |
| varvalue | INTEGER | NULL | 0 | 变量值 |

### 8. 链接表 (urllink)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，链接ID |
| subject | VARCHAR(200) | NOT NULL | - | 链接标题 |
| linkstr | VARCHAR(200) | NOT NULL | - | 链接地址 |
| projectid | INTEGER | NULL | NULL | 项目ID |
| ordernum | INTEGER | NULL | 0 | 排序号 |

### 9. 注册码表 (regkey)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，注册码ID |
| name | VARCHAR(25) | NOT NULL | - | 注册码 |
| ownerid | INTEGER | NOT NULL | - | 申请者用户ID |
| userid | INTEGER | NULL | NULL | 使用者用户ID |
| status | INTEGER | NOT NULL | 1 | 状态：1为未使用，2为已使用 |
| createtime | DATETIME | NOT NULL | NOW() | 创建时间 |

### 10. 密码重置令牌表 (password_reset_tokens)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | SERIAL | NOT NULL | - | 主键 |
| user_id | INTEGER/BIGINT | NOT NULL | - | 用户 ID（外键：users.id，ON DELETE CASCADE） |
| token | VARCHAR(64) | NOT NULL | - | 一次性令牌，唯一索引 |
| expires_at | TIMESTAMP | NOT NULL | - | 过期时间 |
| created_at | TIMESTAMP | NULL | - | 创建时间 |

### 11. 用户认证安全状态表 (user_auth_security_state)

用于登录防爆破、密码重置与注册等接口的**按用户、按操作类型**限流状态（PostgreSQL）。详见 `doc/AUTH_SECURITY_USER_STATE_DB_DESIGN.md`。

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | BIGSERIAL | NOT NULL | - | 主键 |
| user_id | BIGINT | NOT NULL | - | 用户 ID（外键：users.id，ON DELETE CASCADE） |
| opt_type | VARCHAR(32) | NOT NULL | - | 操作类型：login / forgot_password / validate_reset_token / reset_password / register 等 |
| fail_count | INTEGER | NOT NULL | 0 | 当前窗口内失败或广义计数（≥0） |
| window_start | TIMESTAMPTZ | NOT NULL | now() | 当前计数窗口起点 |
| next_allowed_at | TIMESTAMPTZ | NOT NULL | now() | 该操作类型下最早允许再请求的 UTC 时间 |

唯一约束：`UNIQUE (user_id, opt_type)`。

### 12. 订阅表 (subsc)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，订阅ID |
| projectid | INTEGER | NULL | NULL | 项目ID（外键：project.id） |
| piid | INTEGER | NULL | NULL | 项目条目ID（外键：projectitem.id） |

### 13. 积分记录表 (point_logs)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，记录ID |
| user_id | INTEGER | NOT NULL | - | 用户ID |
| points | INTEGER | NOT NULL | - | 获得的积分数 |
| source | VARCHAR(50) | NOT NULL | - | 积分来源：article_create, regkey_exchange等 |
| log_date | DATETIME | NOT NULL | - | 积分记录日期（只记录日期，不记录时间） |
| created_at | DATETIME | NOT NULL | NOW() | 记录创建时间 |

### 14. 关系表 (relation)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | INTEGER | NOT NULL | - | 主键，关系ID |
| projectid | INTEGER | NULL | NULL | 发起订阅的博客项目ID |
| objectid | INTEGER | NULL | NULL | 被订阅的博客项目ID |
| created | DATETIME | NULL | NULL | 创建时间 |
| acttype | INTEGER | NULL | 1 | 关系类型，默认为1（订阅） |

## 向量搜索相关表

### 15. 文章向量表 (article_vectors)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | SERIAL | NOT NULL | - | 主键，向量ID |
| projectitem_id | INTEGER | NOT NULL | - | 项目条目ID（外键：projectitem.id，唯一） |
| title_vector | VECTOR(384) | NULL | NULL | 标题向量（384维） |
| title_text | TEXT | NULL | NULL | 标题文本 |
| content_vector | VECTOR(384) | NULL | NULL | 内容向量（384维） |
| content_text | TEXT | NULL | NULL | 内容文本 |
| segment_count | INTEGER | NULL | 1 | 片段数量 |
| vectorization_method | VARCHAR(50) | NULL | 'direct' | 向量化方法 |
| total_text_length | INTEGER | NULL | NULL | 总文本长度 |
| max_segment_length | INTEGER | NULL | NULL | 最大片段长度 |
| aggregation_weights | JSONB | NULL | NULL | 聚合权重 |
| overlap_strategy | VARCHAR(20) | NULL | 'sliding_window' | 重叠策略 |
| window_size | INTEGER | NULL | 400 | 窗口大小 |
| step_size | INTEGER | NULL | 200 | 步长 |
| avg_confidence | FLOAT | NULL | 1.0 | 平均置信度 |
| key_segment_ratio | FLOAT | NULL | 0.0 | 关键片段比例 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |

### 16. 内容片段向量表 (content_segment_vectors)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | SERIAL | NOT NULL | - | 主键，片段向量ID |
| article_vector_id | INTEGER | NOT NULL | - | 文章向量ID（外键：article_vectors.id） |
| segment_index | INTEGER | NOT NULL | - | 片段索引 |
| segment_hash | VARCHAR(64) | NULL | NULL | 片段哈希 |
| segment_text | TEXT | NULL | NULL | 片段文本 |
| segment_vector | VECTOR(384) | NULL | NULL | 片段向量（384维） |
| segment_length | INTEGER | NULL | NULL | 片段长度 |
| token_count | INTEGER | NULL | NULL | 令牌数量 |
| word_count | INTEGER | NULL | NULL | 单词数量 |
| start_char_pos | INTEGER | NULL | NULL | 起始字符位置 |
| end_char_pos | INTEGER | NULL | NULL | 结束字符位置 |
| start_token_pos | INTEGER | NULL | NULL | 起始令牌位置 |
| end_token_pos | INTEGER | NULL | NULL | 结束令牌位置 |
| prev_overlap_chars | INTEGER | NULL | 0 | 前向重叠字符数 |
| next_overlap_chars | INTEGER | NULL | 0 | 后向重叠字符数 |
| overlap_ratio | FLOAT | NULL | 0.0 | 重叠比例 |
| confidence_score | FLOAT | NULL | 1.0 | 置信度分数 |
| semantic_density | FLOAT | NULL | NULL | 语义密度 |
| keyword_density | FLOAT | NULL | NULL | 关键词密度 |
| is_key_segment | BOOLEAN | NULL | FALSE | 是否关键片段 |
| segment_type | VARCHAR(20) | NULL | 'body' | 片段类型 |
| contains_title | BOOLEAN | NULL | FALSE | 是否包含标题 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |

### 17. 评论向量表 (comment_vectors)

| 字段名 | 数据类型 | 是否为空 | 默认值 | 备注 |
|--------|----------|----------|--------|------|
| id | SERIAL | NOT NULL | - | 主键，评论向量ID |
| post_id | INTEGER | NOT NULL | - | 评论ID（外键：post.id，唯一） |
| title_vector | VECTOR(384) | NULL | NULL | 标题向量（384维） |
| content_vector | VECTOR(384) | NULL | NULL | 内容向量（384维） |
| title_text | TEXT | NULL | NULL | 标题文本 |
| content_text | TEXT | NULL | NULL | 内容文本 |
| segment_count | INTEGER | NULL | 1 | 片段数量 |
| vectorization_method | VARCHAR(50) | NULL | NULL | 向量化方法 |
| total_text_length | INTEGER | NULL | NULL | 总文本长度 |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | 更新时间 |

## 索引说明

### 主要索引

1. **主键索引**：所有表都有主键索引
2. **外键索引**：所有外键字段都有对应的索引
3. **唯一索引**：`users.name`、`users.email`、`article_vectors.projectitem_id`、`comment_vectors.post_id`

### 向量搜索索引

1. **HNSW索引**：
   - `article_vectors.title_vector` - 文章标题向量索引
   - `article_vectors.content_vector` - 文章内容向量索引
   - `content_segment_vectors.segment_vector` - 片段向量索引
   - `comment_vectors.title_vector` - 评论标题向量索引
   - `comment_vectors.content_vector` - 评论内容向量索引

2. **复合索引**：
   - `content_segment_vectors(article_vector_id, segment_index)` - 片段向量复合索引

## 表关系说明

### 主要关系

1. **用户相关**：
   - `users` ← `project` (一对多)
   - `users` ← `projectitem` (一对多)
   - `users` ← `post` (一对多)

2. **项目相关**：
   - `project` ← `projectitem` (一对多)
   - `project` ← `folders` (一对多)
   - `project` ← `urllink` (一对多)

3. **条目相关**：
   - `projectitem` ← `post` (一对多，通过projectitemid字段)
   - `projectitem` ← `attachment` (一对多，通过parentid字段)
   - `projectitem` ← `article_vectors` (一对一)

4. **向量搜索相关**：
   - `article_vectors` ← `content_segment_vectors` (一对多)
   - `post` ← `comment_vectors` (一对一)

5. **订阅关系**：
   - `project` ← `subsc` (一对多)
   - `projectitem` ← `subsc` (一对多)
   - `project` ← `relation` (多对多，通过projectid和objectid)

## 数据类型说明

- **INTEGER**：整数类型，用于ID和计数字段
- **BIGINT**：大整数类型，用于附件表的主键
- **VARCHAR(n)**：可变长度字符串，n为最大长度
- **TEXT**：长文本类型，用于存储文章内容等
- **DATETIME**：日期时间类型
- **TIMESTAMP**：时间戳类型
- **BOOLEAN**：布尔类型
- **FLOAT**：浮点数类型
- **JSONB**：JSON二进制类型，用于存储结构化数据
- **VECTOR(384)**：向量类型，384维向量，用于BERT向量搜索

## 注意事项

1. **字段命名**：所有字段名都使用小写字母和下划线
2. **外键约束**：部分外键关系在应用层维护，数据库层面可能没有显式的外键约束
3. **向量字段**：向量字段需要PostgreSQL的pgvector扩展支持
4. **时间字段**：大部分时间字段使用DATETIME类型，向量表使用TIMESTAMP类型
5. **默认值**：大部分可选字段都有合理的默认值
6. **`project.state` 语义**：历史生产库以 `0` 表示正常博客、`1` 表示禁用；与 `users.state` 及 `StatusMixin.status`（`1`=正常）相反，应用层统一使用 `src/constants.py` 中的 `ProjectStatus`
7. **索引优化**：向量搜索相关表有专门的HNSW索引用于高效相似度搜索
