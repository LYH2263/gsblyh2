from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Follow, User, Notification

follow_bp = Blueprint('follow', __name__)


@follow_bp.route('/<int:user_id>', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    current_user_id = int(get_jwt_identity())
    current_user = User.query.filter_by(id=current_user_id).first()

    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    if current_user_id == user_id:
        return jsonify({'error': '不能关注自己'}), 400

    target_user = User.query.filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404

    # 检查是否已关注
    existing = Follow.query.filter_by(follower_id=current_user_id, following_id=user_id).first()
    if existing:
        return jsonify({'error': '已关注'}), 400

    follow = Follow(follower_id=current_user_id, following_id=user_id)

    try:
        db.session.add(follow)

        # 发送关注通知
        notification = Notification(
            user_id=user_id,
            type='follow',
            content=f'{current_user.nickname or current_user.username} 关注了你',
            source_user_id=current_user_id
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'message': '关注成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '关注失败'}), 500


@follow_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def unfollow_user(user_id):
    current_user_id = int(get_jwt_identity())

    follow = Follow.query.filter_by(follower_id=current_user_id, following_id=user_id).first()
    if not follow:
        return jsonify({'error': '未关注'}), 404

    try:
        db.session.delete(follow)
        db.session.commit()
        return jsonify({'message': '取消关注成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '取消关注失败'}), 500


@follow_bp.route('/<int:user_id>/status', methods=['GET'])
@jwt_required()
def get_follow_status(user_id):
    current_user_id = int(get_jwt_identity())

    follow = Follow.query.filter_by(follower_id=current_user_id, following_id=user_id).first()

    target_user = User.query.filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404

    # 获取粉丝数和关注数
    followers_count = Follow.query.filter_by(following_id=user_id).count()
    following_count = Follow.query.filter_by(follower_id=user_id).count()

    return jsonify({
        'following': follow is not None,
        'followers_count': followers_count,
        'following_count': following_count
    }), 200


@follow_bp.route('/followers/<int:user_id>', methods=['GET'])
def get_followers(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    followers = Follow.query.filter_by(following_id=user_id)\
        .order_by(Follow.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for f in followers.items:
        follower = User.query.filter_by(id=f.follower_id).first()
        if follower:
            result.append(follower.to_dict())

    return jsonify({
        'followers': result,
        'total': followers.total,
        'page': followers.page,
        'pages': followers.pages
    }), 200


@follow_bp.route('/following/<int:user_id>', methods=['GET'])
def get_following(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    following = Follow.query.filter_by(follower_id=user_id)\
        .order_by(Follow.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for f in following.items:
        followed = User.query.filter_by(id=f.following_id).first()
        if followed:
            result.append(followed.to_dict())

    return jsonify({
        'following': result,
        'total': following.total,
        'page': following.page,
        'pages': following.pages
    }), 200
