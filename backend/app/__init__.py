from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import os

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    from app.routes import auth_bp, user_bp, post_bp, comment_bp, like_bp, follow_bp, notification_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(post_bp, url_prefix='/api/posts')
    app.register_blueprint(comment_bp, url_prefix='/api/comments')
    app.register_blueprint(like_bp, url_prefix='/api/likes')
    app.register_blueprint(follow_bp, url_prefix='/api/follows')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')

    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 创建默认用户
        from app.models import User
        default_user = User.query.filter_by(username='web').first()
        if not default_user:
            default_user = User(
                username='web',
                email='web@example.com',
                nickname='微博管理员',
                role='admin'
            )
            default_user.set_password('123456')
            db.session.add(default_user)
            db.session.commit()
            print('Default admin user created: web / 123456')
        
        # 创建测试用户
        test_users = ['user1', 'user2', 'user3']
        for username in test_users:
            if not User.query.filter_by(username=username).first():
                user = User(
                    username=username,
                    email=f'{username}@example.com',
                    nickname=f'测试{username}',
                    role='user'
                )
                user.set_password('123456')
                db.session.add(user)
        db.session.commit()
        print('Default test users created: user1, user2, user3 / 123456')

    return app
