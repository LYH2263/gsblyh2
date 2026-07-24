# 微博系统

一个功能完整的类似微博的社交媒体网站，采用前后端分离架构开发。

## 功能特性

- **用户系统**: 用户注册、登录、个人资料管理（头像、昵称、简介）
- **内容发布**: 支持发布文字、图片微博
- **内容浏览**: 时间线、发现页、个人主页
- **互动功能**: 评论、点赞
- **社交关系**: 关注/粉丝机制
- **消息通知**: 被关注、被评论、被点赞通知

## 技术栈

- **后端**: Flask + MySQL 8.0
- **前端**: Vue 3 + Element Plus + Vite
- **部署**: Docker Compose

## How to Run

```bash
docker compose up
```

## Verification

启动后访问以下地址进行验证：

1. **前端页面**: http://localhost:3002
2. **后端API**: http://localhost:8000/api/posts/discover
3. **测试流程**:
   - 访问前端注册新用户（首次使用必须先注册）
   - 登录后发布微博
   - 注册另一用户进行评论、点赞、关注
   - 查看通知中心

## Services

- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **MySQL**: localhost:3309 (如遇端口冲突)

## 默认账户

| 用户名 | 密码 | 备注 |
|--------|------|------|
| web | 123456 | 系统用户 |
| user1 | 123456 | 测试用户1 |
| user2 | 123456 | 测试用户2 |
| user3 | 123456 | 测试用户3 |

## 项目结构

```
.
├── docker-compose.yml      # Docker Compose 配置
├── backend/               # Flask 后端
│   ├── app/              # 应用代码
│   │   ├── models/      # 数据模型
│   │   ├── routes/      # API 路由
│   │   └── __init__.py
│   ├── config.py        # 配置文件
│   ├── run.py          # 入口文件
│   ├── requirements.txt # 依赖
│   └── Dockerfile
└── frontend/            # Vue.js 前端
    ├── src/
    │   ├── api/        # API 调用
    │   ├── components/ # 组件
    │   ├── views/      # 页面视图
    │   ├── stores/     # 状态管理
    │   └── router/     # 路由配置
    ├── package.json
    ├── vite.config.js
    └── Dockerfile
```

## API 接口文档

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户

### 用户
- `GET /api/users/:id` - 获取用户信息
- `PUT /api/users/profile` - 更新个人资料
- `POST /api/users/avatar` - 上传头像

### 微博
- `POST /api/posts` - 发布微博
- `GET /api/posts/timeline` - 获取时间线
- `GET /api/posts/discover` - 发现页
- `GET /api/posts/user/:id` - 用户微博列表
- `PUT /api/posts/:id` - 编辑微博
- `DELETE /api/posts/:id` - 删除微博

### 评论
- `POST /api/comments` - 发表评论
- `GET /api/comments/post/:id` - 获取微博评论

### 点赞
- `POST /api/likes/post/:id` - 点赞
- `DELETE /api/likes/post/:id` - 取消点赞

### 关注
- `POST /api/follows/:id` - 关注
- `DELETE /api/follows/:id` - 取消关注

### 通知
- `GET /api/notifications` - 通知列表
- `PUT /api/notifications/:id/read` - 标记已读
