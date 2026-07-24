from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Comment, Post, User, Notification

comment_bp = Blueprint('comment', __name__)


@comment_bp.route('', methods=['POST'])
@jwt_required()
def create_comment():
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    post_id = data.get('post_id')
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id')

    if not post_id:
        return jsonify({'error': '帖子ID不能为空'}), 400

    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400

    if len(content) > 500:
        return jsonify({'error': '评论内容不能超过500字'}), 400

    # 检查帖子是否存在
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    # 检查父评论是否存在
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if not parent_comment or parent_comment.post_id != post_id:
            return jsonify({'error': '无效的父评论'}), 400

    # 创建评论
    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id
    )

    try:
        db.session.add(comment)
        db.session.commit()

        # 给帖子作者发送通知
        if post.user_id != user_id:
            notification = Notification(
                user_id=post.user_id,
                type='comment',
                content=f'{user.nickname or user.username} 评论了你的微博',
                source_user_id=user_id,
                source_post_id=post_id,
                source_comment_id=comment.id
            )
            db.session.add(notification)
            db.session.commit()

        return jsonify({
            'message': '评论成功',
            'comment': comment.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '评论失败，请稍后重试'}), 500


@comment_bp.route('/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404
    return jsonify({'comment': comment.to_dict()}), 200


@comment_bp.route('/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = int(get_jwt_identity())
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    if comment.user_id != user_id:
        return jsonify({'error': '无权限删除此评论'}), 403

    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500


@comment_bp.route('/post/<int:post_id>', methods=['GET'])
def get_post_comments(post_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    # 获取顶级评论（无 parent_id）
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None)\
        .order_by(Comment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # 为每个评论获取回复
    result = []
    for comment in comments.items:
        comment_data = comment.to_dict()
        replies = Comment.query.filter_by(parent_id=comment.id)\
            .order_by(Comment.created_at.asc()).all()
        comment_data['replies'] = [r.to_dict() for r in replies]
        result.append(comment_data)

    return jsonify({
        'comments': result,
        'total': comments.total,
        'page': comments.page,
        'pages': comments.pages
    }), 200
