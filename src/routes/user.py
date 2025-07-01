from flask import Blueprint, jsonify, request, session
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

def require_login():
    """检查登录状态"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    return None

def require_admin():
    """检查管理员权限"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    if session.get('role') != 'ADMIN':
        return jsonify({'error': '需要管理员权限'}), 403
    return None

@user_bp.route('/users', methods=['GET'])
def get_users():
    """获取用户列表（管理员功能）"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = User.query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    })

@user_bp.route('/users', methods=['POST'])
def create_user():
    """创建用户（管理员功能）"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.json
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在
        if data.get('email') and User.query.filter_by(email=data['email']).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        user = User(
            username=data['username'], 
            email=data.get('email'),
            role=data.get('role', 'USER')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': '用户创建成功',
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户详情"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    # 只有管理员或用户本人可以查看
    if session.get('role') != 'ADMIN' and session.get('user_id') != user_id:
        return jsonify({'error': '权限不足'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    # 只有管理员或用户本人可以修改
    if session.get('role') != 'ADMIN' and session.get('user_id') != user_id:
        return jsonify({'error': '权限不足'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        # 检查用户名是否被其他用户占用
        if 'username' in data and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': '用户名已存在'}), 400
            user.username = data['username']
        
        # 检查邮箱是否被其他用户占用
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': '邮箱已存在'}), 400
            user.email = data['email']
        
        # 只有管理员可以修改角色
        if 'role' in data and session.get('role') == 'ADMIN':
            user.role = data['role']
        
        db.session.commit()
        
        return jsonify({
            'message': '用户信息更新成功',
            'user': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户（管理员功能）"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        user = User.query.get_or_404(user_id)
        
        # 不能删除自己
        if user.id == session.get('user_id'):
            return jsonify({'error': '不能删除自己的账户'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': '用户删除成功'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/change-password', methods=['POST'])
def change_password():
    """修改自己的密码"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    try:
        data = request.json
        user = User.query.get(session['user_id'])
        
        # 验证旧密码
        if not user.check_password(data['old_password']):
            return jsonify({'error': '旧密码错误'}), 400
        
        # 设置新密码
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': '密码修改成功'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
def reset_password(user_id):
    """重置用户密码（管理员功能）"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.json
        user = User.query.get_or_404(user_id)
        
        # 设置新密码
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': '密码重置成功'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/profile', methods=['GET'])
def get_profile():
    """获取当前用户信息"""
    auth_check = require_login()
    if auth_check:
        return auth_check
    
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())
