from src.models.user import db
from datetime import datetime

class ExamRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_questions = db.Column(db.Integer, default=140)
    correct_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='in_progress')  # in_progress/completed
    
    # 关系
    user = db.relationship('User', backref=db.backref('exam_records', lazy=True))
    answers = db.relationship('AnswerRecord', backref='exam', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ExamRecord {self.id}: User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_questions': self.total_questions,
            'correct_count': self.correct_count,
            'score': self.score,
            'status': self.status
        }

class AnswerRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam_record.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean, default=False)
    answer_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    question = db.relationship('Question', backref=db.backref('answer_records', lazy=True))

    def __repr__(self):
        return f'<AnswerRecord {self.id}: Exam {self.exam_id}, Question {self.question_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'question_id': self.question_id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'answer_time': self.answer_time.isoformat() if self.answer_time else None
        }

class WrongQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    wrong_count = db.Column(db.Integer, default=1)
    last_wrong_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_mastered = db.Column(db.Boolean, default=False)
    
    # 关系
    user = db.relationship('User', backref=db.backref('wrong_questions', lazy=True))
    question = db.relationship('Question', backref=db.backref('wrong_records', lazy=True))

    def __repr__(self):
        return f'<WrongQuestion {self.id}: User {self.user_id}, Question {self.question_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'wrong_count': self.wrong_count,
            'last_wrong_time': self.last_wrong_time.isoformat() if self.last_wrong_time else None,
            'is_mastered': self.is_mastered
        }

