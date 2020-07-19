from app import app
import enum
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, Enum, Integer, String, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy(app)

class KASkillCompletionSource(enum.Enum):
    teacher_dashboard = 0
    unit_view = 1
    unit_view_task = 2
    lesson_view_task = 3
    

class ClassSectionStudent(db.Model):
    __tablename__ = 'class_section_student'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    email = Column(String, index=True, unique=True)
    firebase_id = Column(String)
    signed_up_at = Column(DateTime)
    class_section_id = Column(Integer, ForeignKey('class_section.id'), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    archived_at = Column(DateTime)
    
    def __init__(self, name, email, class_section_id):
        self.name = name
        self.email = email
        self.class_section_id = class_section_id
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'firebase_id': self.firebase_id,
            'signed_up_at': self.signed_up_at,
            'class_section_id': self.class_section_id,
            'created_at': self.created_at,
            'archived_at': self.archived_at
        }    
    
    def set_firebase_id(self, id):
        self.firebase_id = id
        self.signed_up_at = datetime.datetime.utcnow()


class StudentHeartbeat(db.Model):
    __tablename__ = 'student_heartbeat'
    __table_args__ = (
        Index('student_device_index', 'student_id', 'device_id'), 
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('class_section_student.id'), nullable=False, index=True)
    device_id = Column(String, nullable=False)
    skill = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)

    def init(self, student_id, device_id, skill):
        self.student_id = student_id
        self.device_id = device_id
        self.skill = skill
    
    def serialize(self):
        return {
            'student_id': self.student_id,
            'skill': self.skill,
            'time': self.time
        }

    def repeat(self):
        self.last_updated = datetime.datetime.utcnow()


class KASkillCompletion(db.Model):
    __tablename__ = 'ka_skill_completion'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('class_section_student.id'), index=True, nullable=False)
    course = Column(String)
    unit = Column(String)
    skill = Column(String, index=True, nullable=False)
    questions_correct = Column(Integer)
    questions_out_of = Column(Integer)
    mastery_category = Column(String)
    mastery_points = Column(Integer)
    mastery_points_out_of = Column(Integer)
    recorded_from = Column(Enum(KASkillCompletionSource), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    
    def __init__(
        self, 
        student_id, 
        course, 
        unit, 
        skill, 
        questions_correct, 
        questions_out_of,
        mastery_category,
        mastery_points,
        mastery_points_out_of,
        recorded_from
    ):
        self.student_id = student_id
        self.course = course
        self.unit = unit
        self.skill = skill
        self.questions_correct = questions_correct
        self.questions_out_of = questions_out_of
        self.mastery_category = mastery_category
        self.mastery_points = mastery_points
        self.mastery_points_out_of = mastery_points_out_of
        self.recorded_from = recorded_from
    
    def serialize(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course': self.course,
            'unit': self.unit,
            'skill': self.skill,
            'questions_correct': self.questions_correct,
            'questions_out_of': self.questions_out_of,
            'mastery_category': self.mastery_category,
            'mastery_points': self.mastery_points,
            'mastery_points_out_of': self.mastery_points_out_of,
            'recorded_from': self.recorded_from.name,
            'created_at': self.created_at
        }

    def is_struggling(self):
        # Only based on the question data (at least for now)
        return self.questions_out_of - self.questions_correct >= 2


class ClassSection(db.Model):
    __tablename__ = 'class_section'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    ka_id = Column(String, unique=True, index=True)

    def __init__(self, name, ka_id):
        self.name = name
        self.ka_id = ka_id
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'ka_id': self.ka_id
        }


class SessionRequestStatus(enum.Enum):
    not_applicable = 0
    pending = 1
    accepted = 2
    rejected = 3
    cancelled = 4


class TutoringSession(db.Model):
    __tablename__ = 'tutoring_session'

    id = Column(Integer, primary_key=True)
    guide_id = Column(Integer, ForeignKey('class_section_student.id'), nullable=False, index=True)
    learner_id = Column(Integer, ForeignKey('class_section_student.id'), nullable=False, index=True)
    manually_requested = Column(Boolean, default=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    skill = Column(String, index=True)
    end_time = Column(DateTime)
    cancellation_reason = Column(String)

    # For online mode
    request_status = Column(Enum(SessionRequestStatus))
    conference_link = Column(String)
    rejection_note = Column(String)

    def __init__(
        self,
        guide_id,
        learner_id,
        skill,
        manually_requested,
        online_mode,
        conference_link
    ):
        self.guide_id = guide_id
        self.learner_id = learner_id
        self.skill = skill
        self.manually_requested = manually_requested

        if online_mode:
            if conference_link is None:
                raise ValueError('Must provide a conference link for online sessions.')

            self.conference_link = conference_link
            self.request_status = SessionRequestStatus.pending
        else:
            self.request_status = SessionRequestStatus.not_applicable

    def reject(self, note):
        self.cancellation_reason = 'request_rejected'
        self.request_status = SessionRequestStatus.rejected
        self.rejection_note = note
        self.end_time = datetime.datetime.utcnow()

    def accept(self):
        self.request_status = SessionRequestStatus.accepted

    def cancel(self, reason):
        self.end_time = datetime.datetime.utcnow()
        self.cancellation_reason = reason

        if self.request_status == SessionRequestStatus.pending:
            self.request_status = SessionRequestStatus.cancelled

    def finish(self):
        self.end_time = datetime.datetime.utcnow()

    def serialize(self):
        request_status = self.request_status.name if self.request_status is not None else None

        return {
            'id': self.id,
            'guide_id': self.guide_id,
            'learner_id': self.learner_id,
            'manually_requested': self.manually_requested,
            'skill': self.skill,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'cancellation_reason': self.cancellation_reason,
            'request_status': request_status,
            'conference_link': self.conference_link,
            'rejection_note': self.rejection_note
        }

"""
    Forms
"""
class QuestionType(enum.Enum):
    short_text = 0
    long_text = 1
    multiple_choice = 2
    linear_scale = 3


class Form(db.Model):
    __tablename__ = 'form'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    def init(self, name):
        self.name = name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }

    def num_questions(self):
        return FormQuestion.query.filter_by(form_id=self.id).count()


class Question(db.Model):
    __tablename__ = 'question'

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    options = Column(JSON)
    archived_at = Column(DateTime)

    def init(self, question, question_type, options):
        self.question = question
        self.question_type = question_type
        self.options = options

    def serialize(self, include_num_responses=True):
        data = {
            'id': self.id,
            'question': self.question,
            'question_type': self.question_type.name,
            'options': self.options,
            'archived_at': self.archived_at
        }

        if include_num_responses:
            data['num_responses'] = self.num_responses()

        return data

    def num_responses(self):
        query = """
            select count(*) from
                question q,
                form_question fq,
                form_response fr
            where
                q.id = fq.question_id
                and fq.id = fr.form_question_id
        """
        result = db.session.execute(query)
        return result.scalar()
    
    def archive(self, archive=True):
        if archive:
            self.archived_at = datetime.datetime.utcnow()
        else:
            self.archived_at = None


class Label(db.Model):
    __tablename__ = 'label'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    color = Column(String)

    def init(self, title, color):
        self.title = title
        self.color = color

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'color': self.color
        }


class QuestionLabel(db.Model):
    __tablename__ = 'question_label'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False, index=True)
    label_id = Column(Integer, ForeignKey('label.id'), nullable=False, index=True)

    def init(self, question_id, label_id):
        self.question_id = question_id
        self.label_id = label_id

    def serialize(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'label_id': self.label_id
        }


class FormQuestion(db.Model):
    __tablename__ = 'form_question'

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey('form.id'), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False, index=True)
    required = Column(Boolean, nullable=False, default=True)
    index_in_form = Column(Integer, nullable=False)
    archived_at = Column(DateTime)

    def init(self, form_id, question_id, required, index_in_form):
        self.form_id = form_id
        self.question_id = question_id
        self.required = required
        self.index_in_form = index_in_form

    def serialize(self):
        return {
            'id': self.id,
            'form_id': self.form_id,
            'question_id': self.question_id,
            'required': self.required,
            'index_in_form': self.index_in_form,
            'archived_at': self.archived_at
        }

    def archive(self):
        self.archived_at = datetime.datetime.utcnow()


class FormResponse(db.Model):
    __tablename__ = 'form_response'
    __table_args__ = (
        UniqueConstraint('session_id', 'class_section_student_id', 'form_question_id', name='_session_student_response_uc'), 
    )

    id = Column(Integer, primary_key=True)
    form_question_id = Column(Integer, ForeignKey('form_question.id'), nullable=False, index=True)
    form_distribution_id = Column(Integer, ForeignKey('form_distribution.id'), nullable=False, index=True)
    class_section_student_id = Column(Integer, ForeignKey('class_section_student.id'), index=True, nullable=False)
    session_id = Column(Integer, ForeignKey('tutoring_session.id'), nullable=False, index=True)
    original_question_index = Column(Integer, nullable=False)
    response = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def init(
        self, 
        form_question_id, 
        distribution_id, 
        class_section_student_id, 
        session_id,
        original_question_index,
        response
    ):
        self.form_question_id = form_question_id
        self.form_distribution_id = distribution_id
        self.class_section_student_id = class_section_student_id
        self.session_id = session_id
        self.original_question_index = original_question_index
        self.response = response

    def serialize(self):
        return {
            'id': self.id,
            'form_question_id': self.form_question_id,
            'form_distribution_id': self.form_distribution_id,
            'session_id': self.session_id,
            'class_section_student_id': self.class_section_student_id,
            'original_question_index': self.original_question_index,
            'response': self.response,
            'created_at': self.created_at
        }


class FormDistribution(db.Model):
    __tablename__ = 'form_distribution'
    __table_args__ = (
        Index('class_date_index', 'class_section_id', 'applicable_date'), 
        UniqueConstraint('class_section_id', 'applicable_date', name='_class_date_uc')
    )

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer, ForeignKey('form.id'), nullable=False)
    class_section_id = Column(Integer, ForeignKey('class_section.id'), nullable=False)
    applicable_date = Column(Date, nullable=False)

    def init(self, form_id, class_section_id, applicable_date):
        self.form_id = form_id
        self.class_section_id = class_section_id
        self.applicable_date = applicable_date

    def serialize(self, include_num_responses=True):
        data = {
            'id': self.id,
            'form_id': self.form_id,
            'class_section_id': self.class_section_id,
            'applicable_date': self.applicable_date
        }

        if include_num_responses:
            data['num_responses'] = self.num_responses()

        return data

    def num_responses(self):
        query = """
            select count(*) from form_response where form_distribution_id = %d
        """ % (self.id)
        return db.session.execute(query).scalar()


class MatchingAlgorithm(db.Model):
    __tablename__ = 'matching_algorithm'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    sql_query = Column(String, nullable=False)
    args = Column(JSON, nullable=False, default=[])

    def init(self, name, description, sql_query, args):
        self.name = name
        self.description = description
        self.sql_query = sql_query
        self.args = args

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sql_query': self.sql_query,
            'args': self.args
        }

    def execute(self, args):
        """
            Where 'args' is a list of arguments
        """
        query = self.sql_query % tuple(args)
        return db.session.execute(query)


class ActiveMatchingAlgorithm(db.Model):
    __tablename__ = 'active_matching_algorithm'

    id = Column(Integer, primary_key=True)
    matching_algorithm_id = Column(Integer, ForeignKey('matching_algorithm.id'), nullable=False)
    key = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    archived_at = Column(DateTime, index=True)

    @staticmethod
    def disable_current(key):
        result = ActiveMatchingAlgorithm.query \
            .filter_by(key=key) \
            .filter(ActiveMatchingAlgorithm.archived_at.is_(None))
        currents = [r for r in result]
        result.update(dict(archived_at=datetime.datetime.utcnow()))
        return [c.serialize() for c in currents]

    def init(self, matching_algorithm_id, key):
        self.matching_algorithm_id = matching_algorithm_id
        self.key = key

    def serialize(self):
        return {
            'id': self.id,
            'matching_algorithm_id': self.matching_algorithm_id,
            'key': self.key,
            'created_at': self.created_at,
            'archived_at': self.archived_at
        }


class OnlineMode(db.Model):
    __tablename__ = 'online_mode'

    online_mode = Column(String, primary_key=True, default='online_mode')
    is_online = Column(Boolean, default=False, nullable=False)

    @staticmethod
    def set_online(online):
        row = OnlineMode.query.get('online_mode')

        if row is None:
            row = OnlineMode.create_default()
        
        row.is_online = online

    @staticmethod
    def get():
        row = OnlineMode.query.get('online_mode')
        if row is None:
            row = OnlineMode.create_default(commit=True)
        
        return row

    @staticmethod
    def create_default(commit=False):
        online_mode = OnlineMode()
        db.session.add(online_mode)

        if commit:
            db.session.commit()
        
        return online_mode

    def serialize(self):
        return {
            'is_online': self.is_online
        }