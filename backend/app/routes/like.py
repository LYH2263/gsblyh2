from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Like, Post, Comment, User, Notification

like_bp = Blueprint('like', __name__)


@like_bp.route('/post/<int:post_id>', methods=['POST'])
@jwt_required()
def like_post(post_id):
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    post = Post.query.filter_by(id=post_id).first()
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    # 检查是否已点赞
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    if existing_like:
        return jsonify({'error': '已点赞'}), 400

    like = Like(user_id=user_id, post_id=post_id)

    try:
        db.session.add(like)
        db.session.commit()

        # 给帖子作者发送通知
        if post.user_id != user_id:
            notification = Notification(
                user_id=post.user_id,
                type='like',
                content=f'{user.nickname or user.username} 赞了你的微博',
                source_user_id=user_id,
                source_post_id=post_id
            )
            db.session.add(notification)
            db.session.commit()

        return jsonify({'message': '点赞成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '点赞失败'}), 500


@like_bp.route('/post/<int:post_id>', methods=['DELETE'])
@jwt_required()
def unlike_post(post_id):
    user_id = int(get_jwt_identity())

    like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    if not like:
        return jsonify({'error': '未点赞'}), 404

    try:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': '取消点赞成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '取消点赞失败'}), 500


@like_bp.route('/post/<int:post_id>/status', methods=['GET'])
@jwt_required()
def get_post_like_status(post_id):
    user_id = int(get_jwt_identity())
    like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()

    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    return jsonify({
        'liked': like is not None,
        'likes_count': post.likes.count()
    }), 200


@like_bp.route('/comment/<int:comment_id>', methods=['POST'])
@jwt_required()
def like_comment(comment_id):
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    comment = Comment.query.filter_by(id=comment_id).first()
    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    # 检查是否已点赞
    existing_like = Like.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    if existing_like:
        return jsonify({'error': '已点赞'}), 400

    like = Like(user_id=user_id, comment_id=comment_id)

    try:
        db.session.add(like)
        db.session.commit()

        # 给评论作者发送通知
        if comment.user_id != user_id:
            notification = Notification(
                user_id=comment.user_id,
                type='like',
                content=f'{user.nickname or user.username} 赞了你的评论',
                source_user_id=user_id,
                source_comment_id=comment_id
            )
            db.session.add(notification)
            db.session.commit()

        return jsonify({'message': '点赞成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '点赞失败'}), 500


@like_bp.route('/comment/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def unlike_comment(comment_id):
    user_id = int(get_jwt_identity())

    like = Like.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    if not like:
        return jsonify({'error': '未点赞'}), 404

    try:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': '取消点赞成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '取消点赞失败'}), 500


@like_bp.route('/comment/<int:comment_id>/status', methods=['GET'])
@jwt_required()
def get_comment_like_status(comment_id):
    user_id = int(get_jwt_identity())
    like = Like.query.filter_by(user_id=user_id, comment_id=comment_id).first()

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    return jsonify({
        'liked': like is not None,
        'likes_count': comment.likes.count()
    }), 200
