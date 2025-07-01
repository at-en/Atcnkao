from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.question import Question
from src.models.exam import ExamRecord, AnswerRecord, WrongQuestion
from datetime import datetime
import random

exam_bp = Blueprint('exam', __name__)

def calculate_score(answers):
    """计算分数的工具函数"""
    total_questions = len(answers)
    correct_count = sum(1 for answer in answers if answer['is_correct'])
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    return score, correct_count

@exam_bp.route('/exam/start', methods=['POST'])
def start_exam():
    """开始考试"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        user_id = session['user_id']
        
        # 检查是否有未完成的考试
        ongoing_exam = ExamRecord.query.filter_by(
            user_id=user_id, 
            status='in_progress'
        ).first()
        
        if ongoing_exam:
            return jsonify({
                'error': '您有未完成的考试',
                'exam_id': ongoing_exam.id
            }), 400
        
        # 创建新的考试记录
        exam = ExamRecord(user_id=user_id)
        db.session.add(exam)
        db.session.commit()
        
        return jsonify({
            'message': '考试开始',
            'exam_id': exam.id,
            'exam': exam.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/exam/<int:exam_id>/questions', methods=['GET'])
def get_exam_questions(exam_id):
    """获取考试题目"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        exam = ExamRecord.query.get_or_404(exam_id)
        
        # 检查考试是否属于当前用户
        if exam.user_id != session['user_id']:
            return jsonify({'error': '无权访问此考试'}), 403
        
        # 检查考试状态
        if exam.status == 'completed':
            return jsonify({'error': '考试已完成'}), 400
        
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
        
        # 更新考试的总题目数
        exam.total_questions = len(selected_questions)
        db.session.commit()
        
        return jsonify({
            'exam': exam.to_dict(),
            'questions': [q.to_dict() for q in selected_questions]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/exam/<int:exam_id>/submit', methods=['POST'])
def submit_exam(exam_id):
    """提交考试答案"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        exam = ExamRecord.query.get_or_404(exam_id)
        
        # 检查考试是否属于当前用户
        if exam.user_id != session['user_id']:
            return jsonify({'error': '无权访问此考试'}), 403
        
        # 检查考试状态
        if exam.status == 'completed':
            return jsonify({'error': '考试已完成'}), 400
        
        data = request.get_json()
        answers = data.get('answers', [])
        
        correct_count = 0
        answer_records = []
        
        # 处理每个答案
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            user_answer = answer_data.get('answer')
            
            question = Question.query.get(question_id)
            if not question:
                continue
            
            # 判断答案是否正确
            is_correct = False
            if question.question_type == 'multiple':
                # 多选题需要完全匹配
                correct_answers = set(question.correct_answer.split(','))
                user_answers = set(user_answer.split(',')) if user_answer else set()
                is_correct = correct_answers == user_answers
            else:
                # 单选题和判断题
                is_correct = user_answer == question.correct_answer
            
            if is_correct:
                correct_count += 1
            else:
                # 添加到错题本
                wrong_question = WrongQuestion.query.filter_by(
                    user_id=session['user_id'],
                    question_id=question_id
                ).first()
                
                if wrong_question:
                    wrong_question.wrong_count += 1
                    wrong_question.last_wrong_time = datetime.utcnow()
                    wrong_question.is_mastered = False
                else:
                    wrong_question = WrongQuestion(
                        user_id=session['user_id'],
                        question_id=question_id
                    )
                    db.session.add(wrong_question)
            
            # 创建答题记录
            answer_record = AnswerRecord(
                exam_id=exam_id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct
            )
            answer_records.append(answer_record)
            db.session.add(answer_record)
        
        # 计算分数
        total_questions = len(answers)
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # 更新考试记录
        exam.end_time = datetime.utcnow()
        exam.correct_count = correct_count
        exam.score = score
        exam.status = 'completed'
        
        db.session.commit()
        
        return jsonify({
            'message': '考试提交成功',
            'exam': exam.to_dict(),
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/exam/<int:exam_id>/result', methods=['GET'])
def get_exam_result(exam_id):
    """获取考试结果"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        exam = ExamRecord.query.get_or_404(exam_id)
        
        # 检查考试是否属于当前用户
        if exam.user_id != session['user_id']:
            return jsonify({'error': '无权访问此考试'}), 403
        
        # 获取答题记录
        answer_records = AnswerRecord.query.filter_by(exam_id=exam_id).all()
        
        return jsonify({
            'exam': exam.to_dict(),
            'answers': [record.to_dict() for record in answer_records]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/exams', methods=['GET'])
def get_user_exams():
    """获取用户的考试记录"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        exams = ExamRecord.query.filter_by(
            user_id=session['user_id']
        ).order_by(ExamRecord.start_time.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'exams': [exam.to_dict() for exam in exams.items],
            'total': exams.total,
            'pages': exams.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/wrong-questions', methods=['GET'])
def get_wrong_questions():
    """获取错题本"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        show_mastered = request.args.get('show_mastered', 'false').lower() == 'true'
        
        query = WrongQuestion.query.filter_by(user_id=session['user_id'])
        
        if not show_mastered:
            query = query.filter_by(is_mastered=False)
        
        wrong_questions = query.order_by(
            WrongQuestion.last_wrong_time.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 获取题目详情
        result = []
        for wq in wrong_questions.items:
            question = Question.query.get(wq.question_id)
            if question:
                item = wq.to_dict()
                item['question'] = question.to_dict()
                result.append(item)
        
        return jsonify({
            'wrong_questions': result,
            'total': wrong_questions.total,
            'pages': wrong_questions.pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/wrong-questions/<int:wrong_question_id>/master', methods=['POST'])
def mark_as_mastered(wrong_question_id):
    """标记错题为已掌握"""
    try:
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        wrong_question = WrongQuestion.query.get_or_404(wrong_question_id)
        
        # 检查是否属于当前用户
        if wrong_question.user_id != session['user_id']:
            return jsonify({'error': '无权操作此错题'}), 403
        
        wrong_question.is_mastered = True
        db.session.commit()
        
        return jsonify({'message': '已标记为掌握'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

