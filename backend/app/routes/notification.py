from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Notification, User

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = Notification.query.filter_by(user_id=user_id)

    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # 获取未读数量
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications.items],
        'total': notifications.total,
        'page': notifications.page,
        'pages': notifications.pages,
        'unread_count': unread_count
    }), 200


@notification_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    user_id = int(get_jwt_identity())
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({'unread_count': count}), 200


@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    user_id = int(get_jwt_identity())

    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': '通知不存在'}), 404

    if notification.user_id != user_id:
        return jsonify({'error': '无权限'}), 403

    notification.is_read = True

    try:
        db.session.commit()
        return jsonify({'message': '标记已读成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '操作失败'}), 500


@notification_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    user_id = int(get_jwt_identity())

    try:
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'message': '全部已读'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '操作失败'}), 500


@notification_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    user_id = int(get_jwt_identity())

    notification = Notification.query.get(notification_id)
    if not notification:
        return jsonify({'error': '通知不存在'}), 404

    if notification.user_id != user_id:
        return jsonify({'error': '无权限'}), 403

    try:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500
