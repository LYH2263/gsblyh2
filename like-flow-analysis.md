# 「用户点赞一条微博」完整链路分析

## 一、链路概览

用户点击点赞按钮后，请求在系统中流经以下环节：

```
前端点击 → API拦截器注入JWT → 后端@jwt_required()校验 → 查询用户 → 查询帖子
→ 查询是否已点赞 → 写入Like记录(commit#1) → 判断是否给自己点赞 → 写入Notification(commit#2)
→ 返回响应 → 前端更新本地 liked/likeCount 状态
```

---

## 二、后端链路逐段解析

### 2.1 登录态校验

**入口**：[like.py#L9-L11](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/like.py#L9-L11)

```python
@like_bp.route('/post/<int:post_id>', methods=['POST'])
@jwt_required()
def like_post(post_id):
    user_id = int(get_jwt_identity())
```

- 路由挂载了 `@jwt_required()` 装饰器，由 Flask-JWT-Extended 在函数体执行前完成 Token 校验
- 若请求未携带 Token、Token 过期或签名非法，框架直接拦截，返回 `401 Unauthorized` 或 `422 Unprocessable Entity`
- 校验通过后，通过 `get_jwt_identity()` 取出 Token 中的 `user_id`（字符串），转为整型

### 2.2 用户存在性校验

**代码**：[like.py#L13-L16](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/like.py#L13-L16)

```python
user = User.query.filter_by(id=user_id).first()
if not user:
    return jsonify({'error': '用户不存在'}), 404
```

- 二次校验：即使 JWT 合法，仍要查库确认用户未被删除
- 此处 `user` 对象后续仅用于通知消息中取 `nickname`/`username`

### 2.3 帖子存在性判断

**代码**：[like.py#L18-L20](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/like.py#L18-L20)

```python
post = Post.query.filter_by(id=post_id).first()
if not post:
    return jsonify({'error': '帖子不存在'}), 404
```

- 使用 `filter_by(id=post_id).first()` 而非 `get()` 查帖子
- 当前数据模型 [models/__init__.py#L63-L75](file:///d:/Asolo4/众测723/gsblyh2/backend/app/models/__init__.py#L63-L75) 中 `Post` 没有 `is_deleted` 软删除字段，删除即物理删除（`db.session.delete(post)`），所以不存在"帖子已被软删但查得到"的情况
- 外键关系配置了 `cascade='all, delete-orphan'`（[models/__init__.py#L75](file:///d:/Asolo4/众测723/gsblyh2/backend/app/models/__init__.py#L75)），帖子被删除时其关联的 Like 记录会被级联清除

### 2.4 重复点赞处理

**代码**：[like.py#L22-L25](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/like.py#L22-L25)

```python
existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
if existing_like:
    return jsonify({'error': '已点赞'}), 400
```

- 应用层先做一次 SELECT 检查
- 数据库层也有双重保险：`UniqueConstraint('user_id', 'post_id', name='unique_user_post_like')`（[models/__init__.py#L131-L134](file:///d:/Asolo4/众测723/gsblyh2/backend/app/models/__init__.py#L131-L134)），唯一索引防止并发写入重复记录

### 2.5 点赞入库与通知写入（核心问题所在）

**代码**：[like.py#L27-L48](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/like.py#L27-L48)

```python
like = Like(user_id=user_id, post_id=post_id)
try:
    db.session.add(like)
    db.session.commit()          # ← commit #1：点赞入库

    if post.user_id != user_id:
        notification = Notification(...)
        db.session.add(notification)
        db.session.commit()      # ← commit #2：通知入库

    return jsonify({'message': '点赞成功'}), 201
except Exception as e:
    db.session.rollback()
    return jsonify({'error': '点赞失败'}), 500
```

**关键设计缺陷**：点赞与通知被拆分为**两次独立 commit**，不在同一事务中。详细影响见第四章「数据一致性分析」。

---

## 三、四种异常场景对照分析

| 场景 | 后端响应 | 通知是否产生 | 与直觉预期的差异 |
|------|----------|-------------|-----------------|
| **点赞者 = 作者本人** | `201 点赞成功` | 不产生（`post.user_id == user_id` 时跳过通知逻辑） | 符合预期。自己赞自己的微博通常不需要通知，行为合理 |
| **帖子已被删除** | `404 帖子不存在` | 不产生（在第20行即 return，未到达通知逻辑） | 符合预期。但注意：当前删除是物理删除，若未来引入软删除字段，此处需同步增加 `is_deleted` 判断 |
| **未登录** | HTTP 层面由 `@jwt_required()` 直接拦截，返回 `401` | 不产生（请求未进入函数体） | 符合预期。前端响应拦截器 [index.js#L30-L34](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/api/index.js#L30-L34) 收到 401 会清除本地 Token 并跳转 `/login` |
| **重复点赞** | `400 已点赞` | 不产生（在第25行即 return） | 符合预期。数据库唯一约束提供了并发安全的第二层保护 |

---

## 四、数据一致性深度分析：通知写入失败但点赞已提交

### 4.1 问题复现路径

代码中点赞记录与通知记录分属两次 `db.session.commit()`：

1. **commit #1**（第31行）执行成功 → Like 记录已**持久化**到数据库，事务已提交不可回滚
2. **commit #2**（第43行）因任何原因抛出异常（如数据库瞬时连接错误、Notification 表字段约束冲突等）
3. 进入 `except` 块执行 `db.session.rollback()` —— 但 rollback **只能回滚当前事务中未提交的脏数据**，commit #1 的 Like 记录早已提交，无法撤回
4. 前端收到 `500 点赞失败`

### 4.2 造成的实际后果

| 维度 | 后果 |
|------|------|
| **数据库状态** | Like 记录已存在，Notification 记录不存在 |
| **前端展示** | 用户看到 ElMessage 弹出"操作失败"（[PostItem.vue#L270-L272](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/components/PostItem.vue#L270-L272)），点赞按钮仍显示空心白心🤍，计数未增加 |
| **后续操作** | 用户以为点赞失败再次点击 → 后端检查到 existing_like → 返回 `400 已点赞` → 用户困惑 |
| **博主侧** | 博主永远不会收到这条点赞通知，但实际点赞数+1 |
| **一致性等级** | **不一致**：点赞数据与通知数据分裂；前端状态与后端状态分裂 |

### 4.3 与评论模块的对比

相同的模式也存在于评论创建（[comment.py#L54-L77](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/comment.py#L54-L77)）：评论与通知同样是两次 commit。这是一个贯穿多个模块的系统性问题。

### 4.4 正确做法

应将点赞与通知放在**同一事务**中：

```python
db.session.add(like)
if post.user_id != user_id:
    db.session.add(notification)
db.session.commit()              # 单次 commit，原子提交
```

这样要么两者都成功，要么两者都回滚，保证原子性。

---

## 五、前端点赞交互链路解析

### 5.1 API 封装层

[index.js#L77-L83](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/api/index.js#L77-L83) 封装了三个点赞相关接口：

```javascript
likeAPI = {
  likePost: (postId) => api.post(`/likes/post/${postId}`),
  unlikePost: (postId) => api.delete(`/likes/post/${postId}`),
  getPostLikeStatus: (postId) => api.get(`/likes/post/${postId}/status`),
}
```

请求拦截器自动注入 `Authorization: Bearer <token>` 头（[index.js#L9-L20](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/api/index.js#L9-L20)）。

### 5.2 PostItem 组件中的点赞状态管理

[PostItem.vue#L164-L165](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/components/PostItem.vue#L164-L165) 初始化本地状态：

```javascript
const liked = ref(false)
const likeCount = ref(props.post.likes_count || 0)
```

组件挂载时（[PostItem.vue#L323-L326](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/components/PostItem.vue#L323-L326)），主动调用 `fetchLikeStatus()` 向后端请求当前用户对该帖子的点赞状态与最新计数：

```javascript
async function fetchLikeStatus() {
  const res = await likeAPI.getPostLikeStatus(props.post.id)
  liked.value = res.liked
  likeCount.value = res.likes_count
}
```

### 5.3 点赞/取消点赞操作

[PostItem.vue#L260-L273](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/components/PostItem.vue#L260-L273)：

```javascript
async function toggleLike() {
  try {
    if (liked.value) {
      await likeAPI.unlikePost(props.post.id)
      likeCount.value--
    } else {
      await likeAPI.likePost(props.post.id)
      likeCount.value++
    }
    liked.value = !liked.value
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}
```

- 采用"先请求、后更新"模式（非乐观更新），请求成功后才修改本地 `liked` 和 `likeCount`
- 请求失败时，本地状态不变，仅弹错误提示——这部分逻辑本身是正确的

---

## 六、时间线/发现页列表中的性能与竞态风险

### 6.1 N+1 查询：后端序列化时的 COUNT 风暴

[models/__init__.py#L77-L90](file:///d:/Asolo4/众测723/gsblyh2/backend/app/models/__init__.py#L77-L90) 中 `Post.to_dict()` 每次调用都会触发：

```python
'likes_count': self.likes.count(),      # SELECT COUNT(*) FROM likes WHERE post_id = ?
'comments_count': self.comments.count() # SELECT COUNT(*) FROM comments WHERE post_id = ?
```

而 `self.likes` 和 `self.comments` 被定义为 `lazy='dynamic'` 关系（[models/__init__.py#L74-L75](file:///d:/Asolo4/众测723/gsblyh2/backend/app/models/__init__.py#L74-L75)），每次 `.count()` 都会执行独立的 SQL 查询。

时间线接口一次返回 20 条帖子（[post.py#L162-L172](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/post.py#L162-L172)），每条帖子序列化时还会进一步调用 `self.author.to_dict()`，而 `User.to_dict()` 又额外触发 3 个 COUNT（[models/__init__.py#L54-L56](file:///d:/Asolo4/众测723/gsblyh2/backend/app/models/__init__.py#L54-L56)）：

```python
'followers_count': self.followers.count(),
'following_count': self.following.count(),
'posts_count': self.posts.count()
```

**单页请求产生的 SQL 数量估算**：

| 查询来源 | 数量 |
|---------|------|
| 帖子列表主查询 | 1 |
| 每条帖子的 likes COUNT | 20 |
| 每条帖子的 comments COUNT | 20 |
| 每条帖子的 author 查询（首次访问触发） | 20（但 relationship 缓存后可能合并） |
| 每个 author 的 followers/following/posts COUNT | 20 × 3 = 60 |
| **总计** | **约 121+ 条 SQL** |

这就是典型的 **N+1 查询问题**，在高并发或数据量大时会成为严重性能瓶颈。

### 6.2 前端请求风暴：N 个组件 × 1 次状态查询

时间线页 [Timeline.vue#L49-L54](file:///d:/Asolo4/众测723/gsblyh2/frontend/src/views/Timeline.vue#L49-L54) 用 `v-for` 渲染 N 个 `<PostItem>`，每个组件在 `onMounted` 中独立调用 `fetchLikeStatus()`，即向后端发起 N 个并发请求 `/likes/post/{id}/status`。

- 单页 20 条帖子 → 列表加载完成后瞬间产生 20 个 HTTP 请求
- 这些请求各自独立查库，无法批量合并
- 在弱网或服务端压力大时，容易出现部分请求超时、状态闪烁

### 6.3 竞态条件：快速双击与并发点赞

`toggleLike()` 函数缺少以下保护机制：

1. **无 loading 防抖锁**：用户快速连点两次按钮时，两次调用都会看到 `liked.value === false`，各自发起 `likePost()` 请求。第一个请求成功写入并返回 201；第二个请求到达后端时发现 `existing_like` 已存在，返回 400 "已点赞"。虽然最终结果正确（只有一条 Like 记录），但用户会看到一次错误提示。
2. **无请求取消机制**：若用户在请求飞行中点导航离开页面，组件卸载但请求仍在进行，返回后可能对已卸载组件的 ref 赋值（Vue 3 中通常不会崩溃，但属于潜在问题）。
3. **列表刷新竞态**：`toggleLike` 成功后只更新本地状态，不通知父组件。若父组件随后触发 `fetchPosts` 刷新（如删除帖子后 `emit('refresh')`），会重新拉取帖子列表，此时新数据中的 `likes_count` 是后端实时值，可能与本地 `likeCount` 存在短暂不一致（但这最终会被纠正，属于轻微问题）。

### 6.4 get_post_like_status 中的查询顺序异常

[like.py#L71-L82](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/like.py#L71-L82)：

```python
def get_post_like_status(post_id):
    user_id = int(get_jwt_identity())
    like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()  # 先查 like
    post = Post.query.get(post_id)                                          # 再查 post
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
```

查询顺序反直觉——先查了 like 才验证 post 是否存在。功能上不会出错（post 不存在时 like 必然也不存在，因为级联删除），但逻辑上应该先校验资源存在性。

### 6.5 Discover 页"热门"排序名不副实

[post.py#L187-L189](file:///d:/Asolo4/众测723/gsblyh2/backend/app/routes/post.py#L187-L189) 注释写的是"获取热门帖子（按点赞数和评论数排序）"，但实际 SQL 是：

```python
posts = Post.query.order_by(Post.created_at.desc())
```

仅按创建时间倒序排列，完全没有按点赞/评论数排序。这意味着"发现页"展示的其实是最新内容而非热门内容，与注释和用户预期不符。如果要真正实现热门排序，需要 JOIN likes/comments 并按计数排序，这又会进一步加剧查询复杂度。

---

## 七、场景 / 当前行为 / 潜在风险 汇总表

| 场景 | 当前行为 | 潜在风险 |
|------|---------|---------|
| 点赞者与作者为同一人 | 点赞入库返回 201，跳过通知写入 | 无显著风险，行为符合预期 |
| 帖子已被删除（物理删除） | 查询 Post 返回 None，返回 404 | 无显著风险；若未来引入软删除字段需同步修改此处判断 |
| 未登录用户点赞 | `@jwt_required()` 拦截返回 401，前端跳转登录页 | 无显著风险；但前端 PostItem 未在渲染层判断登录态，未登录用户仍可点击按钮后才被跳转 |
| 重复点赞 | 应用层 SELECT 检查返回 400，数据库唯一约束兜底 | 并发极端情况下应用层检查通过但唯一索引抛 IntegrateError，会被笼统 catch 为 500"点赞失败"而非"已点赞" |
| 通知写入失败但点赞已 commit | Like 持久化成功、Notification 丢失，前端收到 500 显示"点赞失败" | **数据不一致**：点赞数+1但博主无通知；前端状态与后端分裂；用户重试触发 400"已点赞"造成困惑 |
| 时间线/发现页列表加载 | 后端 to_dict() 对每条帖子触发多次 COUNT 查询 | **N+1 性能问题**：20 条帖子产生 120+ 条 SQL，高并发下数据库压力剧增 |
| PostItem 组件挂载获取点赞状态 | 每个组件 onMounted 独立调用 `/likes/post/{id}/status` | **前端请求风暴**：20 条帖子瞬间 20 个并发请求，弱网下部分超时导致状态闪烁 |
| 用户快速双击点赞按钮 | 两次请求同时发出，第二个返回 400"已点赞" | 用户看到错误弹窗；缺防抖/loading 锁 |
| Discover 页"热门"排序 | 注释声称按点赞/评论数排序，实际按时间倒序 | 功能语义与实现不符，用户发现页体验不达预期 |
| get_post_like_status 查询顺序 | 先查 Like 后查 Post 存在性 | 逻辑顺序反直觉；若未来取消级联删除可能出现引用悬空 |
