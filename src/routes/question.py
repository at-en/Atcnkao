from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.question import Question
import pandas as pd
import io
import random
import re

question_bp = Blueprint('question', __name__)

def require_admin():
    """检查管理员权限"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    if session.get('role') != 'ADMIN':
        return jsonify({'error': '需要管理员权限'}), 403
    return None

def clean_text(text):
    """清理文本内容"""
    if pd.isna(text) or text is None:
        return ""
    text = str(text).strip()
    # 去除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    return text

def detect_question_type(question_text):
    """根据题目内容检测题型"""
    question_text = question_text.lower()
    
    # 判断题关键词
    judge_keywords = ['判断', '对错', '正确', '错误', '是否', '√', '×', 'true', 'false', '（判断）', '(判断)']
    if any(keyword in question_text for keyword in judge_keywords):
        return 'judge'
    
    # 多选题关键词
    multiple_keywords = ['多选', '选择', '（多选）', '(多选)', '以下哪些', '包括哪些']
    if any(keyword in question_text for keyword in multiple_keywords):
        return 'multiple'
    
    # 默认为单选题
    return 'single'

def parse_options(row, start_col=1, end_col=5):
    """解析选项"""
    options = {}
    option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
    
    for i, label in enumerate(option_labels[:end_col-start_col]):
        col_index = start_col + i
        if col_index < len(row):
            option_text = clean_text(row[col_index])
            if option_text:
                options[f'option_{label.lower()}'] = option_text
    
    return options

def parse_correct_answer(answer_text):
    """解析正确答案"""
    if pd.isna(answer_text) or answer_text is None:
        return 'A'
    
    answer_text = str(answer_text).strip().upper()
    
    # 处理多种答案格式
    if ',' in answer_text or '，' in answer_text:
        # 多选题答案
        return answer_text.replace('，', ',')
    elif len(answer_text) == 1 and answer_text in 'ABCDEF':
        return answer_text
    elif '正确' in answer_text or '对' in answer_text or '√' in answer_text:
        return '正确'
    elif '错误' in answer_text or '错' in answer_text or '×' in answer_text:
        return '错误'
    else:
        return answer_text

@question_bp.route('/admin/import-excel', methods=['POST'])
def import_excel():
    """导入Excel题库"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': '只支持Excel文件(.xlsx, .xls)'}), 400
        
        # 读取Excel文件
        file_content = file.read()
        
        # 尝试读取所有工作表
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        imported_count = 0
        error_count = 0
        sheets_processed = []
        
        for sheet_name in excel_file.sheet_names:
            try:
                # 读取工作表
                df = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_name, header=None)
                
                # 寻找题目开始行
                start_row = 0
                for i, row in df.iterrows():
                    if i > 50:  # 避免检查太多行
                        break
                    
                    # 检查是否包含题目标识
                    row_text = ' '.join([str(cell) for cell in row if pd.notna(cell)])
                    if any(keyword in row_text for keyword in ['题目', '试题', '第1题', '1.', '1、']):
                        start_row = i
                        break
                
                sheet_count = 0
                
                # 从找到的起始行开始处理
                for index, row in df.iterrows():
                    if index < start_row:
                        continue
                    
                    # 检查第一列是否有内容（题目）
                    question_text = clean_text(row[0])
                    if not question_text or len(question_text) < 10:
                        continue
                    
                    try:
                        # 检测题型
                        question_type = detect_question_type(question_text)
                        
                        # 解析选项
                        options = parse_options(row.values)
                        
                        # 解析答案（通常在最后几列）
                        correct_answer = 'A'
                        for col_index in range(len(row)-1, max(4, len(row)-5), -1):
                            if col_index < len(row) and pd.notna(row[col_index]):
                                potential_answer = clean_text(row[col_index])
                                if potential_answer and len(potential_answer) <= 10:
                                    correct_answer = parse_correct_answer(potential_answer)
                                    break
                        
                        # 创建题目对象
                        question = Question(
                            question_text=question_text,
                            question_type=question_type,
                            option_a=options.get('option_a'),
                            option_b=options.get('option_b'),
                            option_c=options.get('option_c'),
                            option_d=options.get('option_d'),
                            correct_answer=correct_answer,
                            difficulty=1
                        )
                        
                        # 检查是否重复
                        existing = Question.query.filter_by(question_text=question_text).first()
                        if not existing:
                            db.session.add(question)
                            sheet_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        continue
                
                if sheet_count > 0:
                    sheets_processed.append(f"{sheet_name}: {sheet_count}题")
                    imported_count += sheet_count
            
            except Exception as e:
                continue
        
        # 提交所有更改
        db.session.commit()
        
        return jsonify({
            'message': f'导入完成！成功导入 {imported_count} 道题目',
            'imported_count': imported_count,
            'error_count': error_count,
            'sheets_processed': sheets_processed
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'导入失败: {str(e)}'}), 500

@question_bp.route('/admin/questions/stats', methods=['GET'])
def get_question_stats():
    """获取题库统计信息"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        total = Question.query.count()
        single_count = Question.query.filter_by(question_type='single').count()
        multiple_count = Question.query.filter_by(question_type='multiple').count()
        judge_count = Question.query.filter_by(question_type='judge').count()
        
        return jsonify({
            'total': total,
            'single': single_count,
            'multiple': multiple_count,
            'judge': judge_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@question_bp.route('/questions', methods=['GET'])
def get_questions():
    """获取题目列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        question_type = request.args.get('type')
        search = request.args.get('search', '')
        
        query = Question.query
        
        if question_type:
            query = query.filter_by(question_type=question_type)
        
        if search:
            query = query.filter(Question.question_text.contains(search))
        
        questions = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'questions': [q.to_dict() for q in questions.items],
            'total': questions.total,
            'pages': questions.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@question_bp.route('/questions/random', methods=['GET'])
def get_random_questions():
    """获取随机题目（用于考试）"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        # 按题型随机抽取题目：多选60题、判断20题、单选60题
        multiple_questions = Question.query.filter_by(question_type='multiple').all()
        judge_questions = Question.query.filter_by(question_type='judge').all()
        single_questions = Question.query.filter_by(question_type='single').all()
        
        selected_questions = []
        
        # 随机选择题目
        if len(multiple_questions) >= 60:
            selected_questions.extend(random.sample(multiple_questions, 60))
        else:
            selected_questions.extend(multiple_questions)
        
        if len(judge_questions) >= 20:
            selected_questions.extend(random.sample(judge_questions, 20))
        else:
            selected_questions.extend(judge_questions)
        
        if len(single_questions) >= 60:
            selected_questions.extend(random.sample(single_questions, 60))
        else:
            selected_questions.extend(single_questions)
        
        # 打乱题目顺序
        random.shuffle(selected_questions)
        
        return jsonify({
            'questions': [q.to_dict() for q in selected_questions],
            'total': len(selected_questions)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@question_bp.route('/questions', methods=['POST'])
def add_question():
    """添加题目"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        data = request.get_json()
        
        question = Question(
            question_text=data.get('question_text'),
            question_type=data.get('question_type'),
            option_a=data.get('option_a'),
            option_b=data.get('option_b'),
            option_c=data.get('option_c'),
            option_d=data.get('option_d'),
            correct_answer=data.get('correct_answer'),
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty', 1)
        )
        
        db.session.add(question)
        db.session.commit()
        
        return jsonify({
            'message': '题目添加成功',
            'question': question.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@question_bp.route('/questions/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """更新题目"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        question = Question.query.get_or_404(question_id)
        data = request.get_json()
        
        question.question_text = data.get('question_text', question.question_text)
        question.question_type = data.get('question_type', question.question_type)
        question.option_a = data.get('option_a', question.option_a)
        question.option_b = data.get('option_b', question.option_b)
        question.option_c = data.get('option_c', question.option_c)
        question.option_d = data.get('option_d', question.option_d)
        question.correct_answer = data.get('correct_answer', question.correct_answer)
        question.explanation = data.get('explanation', question.explanation)
        question.difficulty = data.get('difficulty', question.difficulty)
        
        db.session.commit()
        
        return jsonify({
            'message': '题目更新成功',
            'question': question.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@question_bp.route('/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """删除题目"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        question = Question.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'message': '题目删除成功'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@question_bp.route('/admin/questions/clear', methods=['POST'])
def clear_questions():
    """清空题库（管理员功能）"""
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    try:
        deleted_count = Question.query.delete()
        db.session.commit()
        
        return jsonify({
            'message': f'已清空题库，删除了 {deleted_count} 道题目',
            'deleted_count': deleted_count
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

