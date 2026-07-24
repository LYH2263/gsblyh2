#!/usr/bin/env python3
"""创建测试数据脚本（使用原始SQL）"""
import sys
sys.path.insert(0, '/app')

from app import create_app, db
from app.models import User, Post, Comment, Like, Follow, Notification
from datetime import datetime

def create_test_data():
    app = create_app()
    with app.app_context():
        # 直接使用SQL删除数据
        db.session.execute(db.text('DELETE FROM likes'))
        db.session.execute(db.text('DELETE FROM comments'))
        db.session.execute(db.text('DELETE FROM posts'))
        db.session.execute(db.text('DELETE FROM notifications'))
        db.session.execute(db.text('DELETE FROM follows'))
        db.session.commit()
        
        print("数据已清理")
        
        # 获取用户ID
        users = User.query.all()
        user_ids = {u.username: u.id for u in users}
        print(f"用户ID: {user_ids}")
        
        # 创建关注关系
        follows = [
            (user_ids['user1'], user_ids['user2']),
            (user_ids['user1'], user_ids['web']),
            (user_ids['user2'], user_ids['user1']),
            (user_ids['user3'], user_ids['web']),
            (user_ids['user2'], user_ids['web']),
        ]
        
        for follower_id, following_id in follows:
            db.session.execute(
                db.text('INSERT INTO follows (follower_id, following_id, created_at) VALUES (:follower, :following, :now)'),
                {'follower': follower_id, 'following': following_id, 'now': datetime.utcnow()}
            )
        
        db.session.commit()
        
        # 创建帖子
        posts = [
            (user_ids['web'], "欢迎大家来到微博系统！这是一个功能完整的社交媒体平台"),
            (user_ids['user1'], "今天天气真好，适合出门踏青！"),
            (user_ids['user1'], "学习Flask开发中，感觉很有成就感！"),
            (user_ids['user2'], "新买了一个键盘，打字手感超级棒！"),
            (user_ids['user2'], "今天看了一本好书，推荐给大家：《活着》"),
            (user_ids['user3'], "周末去爬了山，累但是很开心"),
        ]
        
        for user_id, content in posts:
            db.session.execute(
                db.text('INSERT INTO posts (user_id, content, created_at) VALUES (:uid, :content, :now)'),
                {'uid': user_id, 'content': content, 'now': datetime.utcnow()}
            )
        
        db.session.commit()
        
        # 获取帖子ID
        post_list = db.session.execute(db.text('SELECT id, user_id FROM posts ORDER BY id')).fetchall()
        post_ids = [p[0] for p in post_list]
        
        # 创建评论
        comments = [
            (post_ids[0], user_ids['user1'], "系统看起来很不错！"),
            (post_ids[0], user_ids['user2'], "支持一下！"),
            (post_ids[1], user_ids['user2'], "天气确实很好！"),
            (post_ids[1], user_ids['user3'], "可以约一起出去玩"),
            (post_ids[2], user_ids['user2'], "加油！"),
            (post_ids[3], user_ids['user1'], "什么牌子的键盘？"),
        ]
        
        for post_id, user_id, content in comments:
            db.session.execute(
                db.text('INSERT INTO comments (post_id, user_id, content, created_at) VALUES (:pid, :uid, :content, :now)'),
                {'pid': post_id, 'uid': user_id, 'content': content, 'now': datetime.utcnow()}
            )
        
        db.session.commit()
        
        # 创建点赞
        likes = [
            (user_ids['user2'], post_ids[0]),
            (user_ids['user3'], post_ids[0]),
            (user_ids['user2'], post_ids[1]),
            (user_ids['user1'], post_ids[2]),
            (user_ids['user1'], post_ids[3]),
            (user_ids['user1'], post_ids[4]),
            (user_ids['user1'], post_ids[5]),
            (user_ids['user2'], post_ids[5]),
            (user_ids['user3'], post_ids[5]),
        ]
        
        for user_id, post_id in likes:
            db.session.execute(
                db.text('INSERT INTO likes (user_id, post_id, created_at) VALUES (:uid, :pid, :now)'),
                {'uid': user_id, 'pid': post_id, 'now': datetime.utcnow()}
            )
        
        db.session.commit()
        
        # 创建通知
        notifications = [
            (user_ids['user2'], 'follow', f'user1 关注了你', user_ids['user1'], None, None),
            (user_ids['web'], 'follow', f'user1 关注了你', user_ids['user1'], None, None),
            (user_ids['user1'], 'follow', f'user2 关注了你', user_ids['user2'], None, None),
            (user_ids['web'], 'follow', f'user3 关注了你', user_ids['user3'], None, None),
            (user_ids['web'], 'follow', f'user2 关注了你', user_ids['user2'], None, None),
            (user_ids['user1'], 'comment', f'user2 评论了你的微博', user_ids['user2'], post_ids[1], None),
            (user_ids['user1'], 'like', f'user2 赞了你的微博', user_ids['user2'], post_ids[1], None),
            (user_ids['web'], 'comment', f'user1 评论了你的微博', user_ids['user1'], post_ids[0], None),
        ]
        
        for user_id, notif_type, content, source_user_id, source_post_id, source_comment_id in notifications:
            db.session.execute(
                db.text('''INSERT INTO notifications 
                    (user_id, type, content, source_user_id, source_post_id, source_comment_id, is_read, created_at) 
                    VALUES (:uid, :type, :content, :src_uid, :src_pid, :src_cid, 0, :now)'''),
                {'uid': user_id, 'type': notif_type, 'content': content, 'src_uid': source_user_id, 
                 'src_pid': source_post_id, 'src_cid': source_comment_id, 'now': datetime.utcnow()}
            )
        
        db.session.commit()
        
        print("\n测试数据创建完成！")
        print(f"- 用户数: {User.query.count()}")
        print(f"- 帖子数: {Post.query.count()}")
        print(f"- 评论数: {Comment.query.count()}")
        print(f"- 点赞数: {Like.query.count()}")
        print(f"- 关注数: {Follow.query.count()}")
        print(f"- 通知数: {Notification.query.count()}")

if __name__ == '__main__':
    create_test_data()
