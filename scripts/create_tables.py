from app.models.base import db

from app.models.user import *
from app.models.course import *
from app.models.assignment import *
from app.models.learning_data import *
from app.models.knowledge_base import *
from app.models.chat import *

from app import create_app

app = create_app()

tables = [
            User, Role, UserRole,
            Course, StudentCourse,
            Assignment, StudentAssignment, Question, QuestionOption, StudentResponse,
            LearningActivity, KnowledgePoint, StudentKnowledgePoint, AssignmentKnowledgePoint, KnowledgeBaseKnowledgePoint,
            KnowledgeBase,
            Chat, ChatMessage
        ]

# db.drop_tables(tables)
# db.create_tables(tables)
#db.drop_tables([StudentAssignment])
#db.create_tables([StudentAssignment])
#db.create_tables([AssignmentKnowledgePoint, KnowledgeBaseKnowledgePoint])
# db.create_tables([Chat, ChatMessage])