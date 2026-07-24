from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User
import os
import uuid

user_bp = Blueprint('user', __name__)


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/username/<username>', methods=['GET'])
def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    # 更新字段
    if 'nickname' in data:
        user.nickname = data['nickname'].strip()
    if 'bio' in data:
        user.bio = data['bio'].strip()

    try:
        db.session.commit()
        return jsonify({
            'message': '更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新失败'}), 500


@user_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if 'avatar' not in request.files:
        return jsonify({'error': '请选择要上传的图片'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    # 检查文件扩展名
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': '不支持的图片格式'}), 400

    # 生成唯一文件名
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)

    try:
        file.save(filepath)
        # 更新用户头像路径
        user.avatar = f'/static/uploads/{filename}'
        db.session.commit()
        return jsonify({
            'message': '上传成功',
            'avatar': user.avatar
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '上传失败'}), 500


@user_bp.route('/search', methods=['GET'])
def search_users():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({'users': []}), 200

    users = User.query.filter(
        (User.username.like(f'%{keyword}%')) |
        (User.nickname.like(f'%{keyword}%'))
    ).limit(20).all()

    return jsonify({'users': [u.to_dict() for u in users]}), 200


# ============ 管理员功能 ============

@user_bp.route('/admin/list', methods=['GET'])
@jwt_required()
def admin_list_users():
    """管理员：获取所有用户列表"""
    user_id = int(get_jwt_identity())
    current_user = User.query.filter_by(id=user_id).first()
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = User.query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': [u.to_dict() for u in users.items],
        'total': users.total,
        'page': users.page,
        'pages': users.pages
    }), 200


@user_bp.route('/admin/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(target_user_id):
    """管理员：删除用户"""
    user_id = int(get_jwt_identity())
    current_user = User.query.filter_by(id=user_id).first()
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403
    
    # 不能删除自己
    if target_user_id == user_id:
        return jsonify({'error': '不能删除自己的账号'}), 400
    
    target_user = User.query.filter_by(id=target_user_id).first()
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 不能删除其他管理员
    if target_user.role == 'admin':
        return jsonify({'error': '不能删除管理员账号'}), 403
    
    try:
        db.session.delete(target_user)
        db.session.commit()
        return jsonify({'message': '用户已删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500


@user_bp.route('/admin/<int:target_user_id>/role', methods=['PUT'])
@jwt_required()
def admin_update_user_role(target_user_id):
    """管理员：修改用户角色"""
    user_id = int(get_jwt_identity())
    current_user = User.query.filter_by(id=user_id).first()
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403
    
    target_user = User.query.filter_by(id=target_user_id).first()
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    if not data or 'role' not in data:
        return jsonify({'error': '请提供角色'}), 400
    
    new_role = data['role']
    if new_role not in ['user', 'admin']:
        return jsonify({'error': '无效的角色'}), 400
    
    # 不能修改自己的角色
    if target_user_id == user_id:
        return jsonify({'error': '不能修改自己的角色'}), 400
    
    target_user.role = new_role
    try:
        db.session.commit()
        return jsonify({
            'message': '角色已更新',
            'user': target_user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新失败'}), 500
