from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
from app.models.user import User
from app.models.chat import Chat, ChatMessage
from app.react.agent import run
from app.ext import db
import json

ai_assistant_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai-assistant')

@ai_assistant_bp.route('/chat', methods=['GET'])
def chat():
    """渲染AI助手聊天页面"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    # 获取用户最近的聊天记录
    chats = Chat.select().where(Chat.user == user).order_by(Chat.updated_at.desc())
    
    return render_template('ai_assistant/chat.html', user=user, chats=chats)

@ai_assistant_bp.route('/chats', methods=['GET'])
def get_chats():
    """获取用户的聊天历史"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    # 修复: 使用正确的外键关系
    chats = Chat.select().where(Chat.user == user).order_by(Chat.updated_at.desc())
    
    result = []
    for chat in chats:
        result.append({
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': chat.updated_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(result)

@ai_assistant_bp.route('/chats', methods=['POST'])
def create_chat():
    """创建新的聊天会话"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    try:
        chat = Chat.create(
            user=user,
            title="新会话"  # 显式设置默认标题
        )
        
        return jsonify({
            'id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.strftime('%Y-%m-%d %H:%M')
        })
    except Exception as e:
        return jsonify({'error': f'创建聊天时出错: {str(e)}'}), 500

@ai_assistant_bp.route('/chats/<int:chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    """获取指定聊天的消息历史"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    try:
        # 修复: 使用正确的外键关系
        chat = Chat.get(Chat.id == chat_id, Chat.user == user)
        messages = ChatMessage.select().where(ChatMessage.chat == chat).order_by(ChatMessage.timestamp)
        
        result = []
        for msg in messages:
            result.append({
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify(result)
    except Chat.DoesNotExist:
        return jsonify({'error': '聊天不存在或无权访问'}), 404

@ai_assistant_bp.route('/chats/<int:chat_id>/messages', methods=['POST'])
def send_message(chat_id):
    """发送新消息并获取AI回复"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': '消息不能为空'}), 400
    
    try:
        # 使用事务确保原子性
        with db.atomic():
            # 确保聊天存在且属于当前用户
            chat = Chat.get_or_none(Chat.id == chat_id, Chat.user == user)
            
            if not chat:
                return jsonify({'error': '聊天不存在或无权访问'}), 404
            
            # 记录用户消息
            user_message = ChatMessage.create(
                chat=chat,
                role=ChatMessage.ROLE_USER,
                content=data['message']
            )
            
            history_messages = ChatMessage.select().where(ChatMessage.chat == chat).order_by(ChatMessage.timestamp)

            # 调用AI模型生成回复
            # TODO: 选择权限最高的角色
            ai_response = run(data['message'], user.roles[0].role.name, history_messages)
            
            # 记录AI回复
            ai_message = ChatMessage.create(
                chat=chat,
                role=ChatMessage.ROLE_ASSISTANT,
                content=ai_response
            )
            
            # 更新聊天标题 - 只在第一条消息时更新
            if chat.title == "新会话":
                # 使用用户的第一条消息作为聊天标题
                chat.title = data['message'][:30] + ('...' if len(data['message']) > 30 else '')
                chat.save()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            },
            'ai_message': {
                'id': ai_message.id,
                'content': ai_message.content,
                'timestamp': ai_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        print(f'处理消息时发生错误: {str(e)}')
        return jsonify({'error': f'处理消息时发生错误: {str(e)}'}), 500

@ai_assistant_bp.route('/chats/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """删除指定的聊天会话"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    user_id = session['user_id']
    user = User.get_by_id(user_id)
    
    try:
        with db.atomic():
            # 确保聊天存在且属于当前用户
            chat = Chat.get_or_none(Chat.id == chat_id, Chat.user == user)
            
            if not chat:
                return jsonify({'error': '聊天不存在或无权访问'}), 404
            
            # 删除相关的消息
            ChatMessage.delete().where(ChatMessage.chat == chat).execute()
            
            # 删除聊天
            chat.delete_instance()
            
        return jsonify({'success': True, 'message': '聊天已删除'})
    except Exception as e:
        print(f'删除聊天时发生错误: {str(e)}')
        return jsonify({'error': f'删除聊天时发生错误: {str(e)}'}), 500
