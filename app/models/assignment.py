from peewee import *
from app.models.base import BaseModel
from app.models.course import Course
from app.models.user import User

class Assignment(BaseModel):
    title = CharField(max_length=100)
    description = TextField()
    course = ForeignKeyField(Course, backref='assignments')
    due_date = DateTimeField()
    total_points = FloatField(default=100.0)
    
    def __repr__(self):
        return f'<Assignment {self.title} for {self.course.code}>'

class QuestionType:
    MULTIPLE_CHOICE = 'multiple_choice'
    FILL_IN_BLANK = 'fill_in_blank'
    SHORT_ANSWER = 'short_answer'

class Question(BaseModel):
    assignment = ForeignKeyField(Assignment, backref='questions')
    question_text = TextField()
    question_type = CharField(max_length=20)  # multiple_choice, fill_in_blank, short_answer
    points = FloatField(default=10.0)
    order = IntegerField(default=0)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:30]}>'

class QuestionOption(BaseModel):
    question = ForeignKeyField(Question, backref='options')
    option_text = TextField()
    is_correct = BooleanField(default=False)
    order = IntegerField(default=0)
    
    def __repr__(self):
        return f'<Option {self.id}: {self.option_text[:30]}>'

class StudentAssignment(BaseModel):
    student = ForeignKeyField(User, backref='assignments')
    assignment = ForeignKeyField(Assignment, backref='submissions')
    answer = TextField(null=True)  # 保留原有字段用于向后兼容
    feedback = TextField(null=True)
    score = FloatField(null=True)
    submitted_at = DateTimeField(null=True)
    attempts = IntegerField(default=0)
    completed = BooleanField(default=False)
    
    class Meta:
        indexes = (
            (('student', 'assignment'), True),  # 确保学生-作业组合唯一
        )

class StudentResponse(BaseModel):
    student_assignment = ForeignKeyField(StudentAssignment, backref='responses')
    question = ForeignKeyField(Question, backref='responses')
    answer_text = TextField(null=True)  # For fill-in-blank and short answer
    selected_option = ForeignKeyField(QuestionOption, backref='selections', null=True)  # For multiple choice
    score = FloatField(null=True)
    feedback = TextField(null=True)
    
    class Meta:
        indexes = (
            (('student_assignment', 'question'), True),  # 确保学生作业-问题组合唯一
        )
