from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import User


def admin_required(fn):
    """装饰器：要求管理员权限"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
        
        return fn(*args, **kwargs)
    return wrapper
