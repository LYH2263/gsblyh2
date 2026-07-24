from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User
import re

auth_bp = Blueprint('auth', __name__)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    return len(username) >= 3 and len(username) <= 20 and re.match(r'^[a-zA-Z0-9_]+$', username)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # 验证必填字段
    if not username or not email or not password:
        return jsonify({'error': '用户名、邮箱和密码为必填项'}), 400

    # 验证用户名格式
    if not validate_username(username):
        return jsonify({'error': '用户名需3-20位字母、数字或下划线'}), 400

    # 验证邮箱格式
    if not validate_email(email):
        return jsonify({'error': '邮箱格式不正确'}), 400

    # 验证密码强度
    if len(password) < 6:
        return jsonify({'error': '密码长度至少6位'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已被注册'}), 400

    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 400

    # 创建用户
    user = User(
        username=username,
        email=email,
        nickname=username
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败，请稍后重试'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'error': '无效的请求数据'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '用户名和密码为必填项'}), 400

    # 支持用户名或邮箱登录
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401

    # 生成 token (identity 必须是字符串)
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    return jsonify({'user': user.to_dict()}), 200
