from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Post, User, Follow, Notification
import os
import uuid
import json

post_bp = Blueprint('post', __name__)


@post_bp.route('', methods=['POST'])
@jwt_required()
def create_post():
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 处理表单数据和 JSON 数据
    content = ''
    image_urls = []

    if request.content_type and 'multipart/form-data' in request.content_type:
        content = request.form.get('content', '').strip()
        files = request.files.getlist('images')
        for file in files:
            if file and file.filename:
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                if ext in allowed_extensions:
                    filename = f"{uuid.uuid4().hex}.{ext}"
                    upload_folder = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        'app', 'static', 'uploads'
                    )
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    image_urls.append(f'/static/uploads/{filename}')
    else:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        content = data.get('content', '').strip()
        image_urls = data.get('images', [])

    # 验证内容
    if not content and not image_urls:
        return jsonify({'error': '内容或图片不能为空'}), 400

    if len(content) > 2000:
        return jsonify({'error': '内容不能超过2000字'}), 400

    # 创建帖子
    post = Post(
        user_id=user_id,
        content=content,
        images=json.dumps(image_urls) if image_urls else None
    )

    try:
        db.session.add(post)
        db.session.commit()

        # 处理 @提及 通知
        mentions = [word[1:] for word in content.split() if word.startswith('@') and len(word) > 1]
        for username in mentions:
            mentioned_user = User.query.filter_by(username=username).first()
            if mentioned_user and mentioned_user.id != user_id:
                notification = Notification(
                    user_id=mentioned_user.id,
                    type='mention',
                    content=f'{user.nickname or user.username} 在微博中提到了你',
                    source_user_id=user_id,
                    source_post_id=post.id
                )
                db.session.add(notification)
        db.session.commit()

        return jsonify({
            'message': '发布成功',
            'post': post.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '发布失败，请稍后重试'}), 500


@post_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    return jsonify({'post': post.to_dict()}), 200


@post_bp.route('/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    user_id = int(get_jwt_identity())
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    if post.user_id != user_id:
        return jsonify({'error': '无权限修改此帖子'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': '内容不能为空'}), 400

    if len(content) > 2000:
        return jsonify({'error': '内容不能超过2000字'}), 400

    post.content = content

    try:
        db.session.commit()
        return jsonify({
            'message': '更新成功',
            'post': post.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新失败'}), 500


@post_bp.route('/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()
    post = Post.query.filter_by(id=post_id).first()

    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    # 允许帖子作者或管理员删除帖子
    if post.user_id != user_id and (not user or user.role != 'admin'):
        return jsonify({'error': '无权限删除此帖子'}), 403

    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500


@post_bp.route('/timeline', methods=['GET'])
@jwt_required()
def get_timeline():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 获取关注用户的 ID
    following_ids = [f.following_id for f in Follow.query.filter_by(follower_id=user_id).all()]
    following_ids.append(user_id)  # 包含自己的帖子

    # 查询关注用户的帖子
    posts = Post.query.filter(Post.user_id.in_(following_ids))\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'posts': [p.to_dict() for p in posts.items],
        'total': posts.total,
        'page': posts.page,
        'pages': posts.pages
    }), 200


@post_bp.route('/discover', methods=['GET'])
def get_discover():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 获取热门帖子（按点赞数和评论数排序）
    posts = Post.query.order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'posts': [p.to_dict() for p in posts.items],
        'total': posts.total,
        'page': posts.page,
        'pages': posts.pages
    }), 200


@post_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    posts = Post.query.filter_by(user_id=user_id)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'posts': [p.to_dict() for p in posts.items],
        'total': posts.total,
        'page': posts.page,
        'pages': posts.pages
    }), 200
