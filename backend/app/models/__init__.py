from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(80))
    avatar = db.Column(db.String(256), default='/static/uploads/default-avatar.png')
    bio = db.Column(db.Text)
    role = db.Column(db.String(20), default='user')  # user: 普通用户, admin: 管理员
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    # 关注关系 - followers: 关注此用户的用户列表
    # follower_id 是关注者的ID，following_id 是被关注者的ID
    # 所以 followers 关系应该关联到 following_id（被关注者的粉丝列表）
    followers = db.relationship('Follow',
                                foreign_keys='Follow.following_id',
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    # following: 此用户关注的用户列表
    following = db.relationship('Follow',
                                foreign_keys='Follow.follower_id',
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname or self.username,
            'avatar': self.avatar,
            'bio': self.bio,
            'role': self.role,
            'is_admin': self.role == 'admin',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'followers_count': self.followers.count(),
            'following_count': self.following.count(),
            'posts_count': self.posts.count()
        }

    def is_admin(self):
        return self.role == 'admin'


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text)  # JSON array of image URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_author=True):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'images': self.images,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count()
        }
        if include_author:
            data['author'] = self.author.to_dict()
        return data


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 自引用关系
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    likes = db.relationship('Like', backref='comment', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_author=True):
        data = {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'likes_count': self.likes.count()
        }
        if include_author:
            data['author'] = self.author.to_dict()
        return data


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
        db.UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),
    )


class Follow(db.Model):
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
    )


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # follow, comment, like, mention
    content = db.Column(db.Text, nullable=False)
    source_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    source_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic'))
    source_user = db.relationship('User', foreign_keys=[source_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'content': self.content,
            'source_user_id': self.source_user_id,
            'source_user': self.source_user.to_dict() if self.source_user else None,
            'source_post_id': self.source_post_id,
            'source_comment_id': self.source_comment_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
