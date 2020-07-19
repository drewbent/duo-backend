# From: https://stackabuse.com/deploying-a-flask-application-to-heroku/#disqus_thread

from flask import Flask, request, jsonify, Response
from flask.json import dumps
from flask.cli import with_appcontext
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_migrate import Migrate
from marshmallow import fields, Schema
from json import dumps as json_dumps
from dotenv import load_dotenv
from datetime import datetime
from firebase_admin import auth
import firebase_admin
import os, sys

from src.utils.auth import *
from src.utils.api_utils import *

load_dotenv()

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(compare_type=True)
migrate.init_app(app)

CORS(app)

# TODO(phil): when uncommented, this gives the error:
#   "The default Firebase app already exists."
firebase = firebase_admin.initialize_app()

# Blueprints (eventually move everything to these)
from src.api.form_api import form_api
app.register_blueprint(form_api)

from src.api.matching_api import matching_api, find_matches
app.register_blueprint(matching_api)

from src.api.online_mode_api import online_mode_api
app.register_blueprint(online_mode_api)

# Import models
from src.models import *

"""
Auth

For actual authentication, we should just use the Firebase client SDK
(for simplicity's sake); however if we ever have the need for custom 
tokens we can do it here.

Here's a node.js StackOverflow post I referenced:
https://stackoverflow.com/questions/44899658/how-to-authenticate-an-user-in-firebase-admin-in-nodejs
"""

"""
    Class Sections
"""
@app.route('/classes', methods=['GET'])
def classes():
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        ka_id = request.args.get('ka_id')
        if ka_id is not None:
            c = ClassSection.query.filter_by(ka_id=ka_id).first()
            if c is not None:
                return jsonify(c.serialize())
            else:
                return error(404, 'Class not found')
        
        classes = ClassSection.query.all()
        return jsonify([c.serialize() for c in classes])
    except Exception as e:
        return error(error=e)
        
    
@app.route('/classes', methods=['POST'])
def create_class():
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        json = request.get_json()
        name = json.get('name')
        if name is None:
            return error(message='Must provide a new name.')
        
        newClass = ClassSection(
            name=name,
            ka_id=json.get('ka_id')
        )
        db.session.add(newClass)
        db.session.commit()
        return jsonify(newClass.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>', methods=['GET'])
def get_class_section(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=3)
    
    try:
        class_section = ClassSection.query.get(class_id)
        if class_section is None:
            return error(404, message='This class does not exist.')
        
        return jsonify(class_section.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>', methods=['DELETE'])
def delete_class_section(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
        
    try:
        class_section = ClassSection.query.get(class_id)
        if class_section is None:
            return error(404, message='This class does not exist.')
        
        db.session.delete(class_section)
        db.session.commit()
        return ('', 204)
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>', methods=['PATCH'])
def update_class_section(class_id):
    try:
        verify_admin()
        
        class_section = ClassSection.query.get(class_id)
        if class_section is None:
            return error(404, message='This class does not exist.')

        json = request.get_json()
        
        name = json.get('name')
        if name is not None:
            class_section.name = name
        
        ka_id = json.get('ka_id')
        if ka_id is not None:
            class_section.ka_id = ka_id

        db.session.commit()
        return jsonify(class_section.serialize())
    except Exception as e:
        return error(403, error=e)

"""
    Class Section Students
"""
@app.route('/students', methods=['GET'])
def get_students():
    try:
        email = request.args.get('email')
        if email is not None:
            # Just a single user by email: accessibly publicly
            if is_admin(email):
                return jsonify({
                    'email': email,
                    'is_admin': True
                })
            
            student = ClassSectionStudent.query.filter_by(email=email).first()
            if student is not None:
                # Get the firebase user information
                data = student.serialize()
                
                try:
                    firebase_user = auth.get_user_by_email(email)
                    data['signed_up'] = True
                except:
                    data['signed_up'] = False
                    
                data['is_admin'] = False
                return jsonify(data)
            else:
                return error(404, message='This student does not exist.')
        else:
            # To fetch all users: must be an admin
            try:
                verify_admin()
            except Exception as e:
                return error(403, error=e)
                
            students = ClassSectionStudent.query.all()
            return jsonify([s.serialize() for s in students])
    except Exception as e:
        print(str(e))
        return error(error=e)
    
    
@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
            return error(404, 'This student does not exist.')
        
        return jsonify(student.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>/students', methods=['POST'])
def create_class_section_student(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        json = request.get_json()
        email = json.get('email')
        if email is None:
            return error(message='Must provide an email.')
        
        name = json.get('name')
        if name is None:
            return error(message='Must provide a name.')
        
        student = ClassSectionStudent(
            name=name,
            email=email, 
            class_section_id=class_id
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.serialize())
    except Exception as e:
        return error(error=e)
    
    
@app.route('/classes/<int:class_id>/students', methods=['GET'])
def get_class_section_students(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        name = request.args.get('name')
        if name is not None:
            student = ClassSectionStudent.filter_by(name).first()
            if student is None:
                return error(404, message='Student not found.')
            else:
                return jsonify(student.serialize())
        
        students = ClassSectionStudent.query.filter_by(class_section_id=class_id)
        return jsonify([s.serialize() for s in students])
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>/students/create-multiple', methods=['POST'])
def create_students(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)

    try:
        json = request.get_json()
        studentsData = json.get('students')
        if studentsData is None:
            return error(message='Must provide students')

        students = []  
        for studentData in studentsData:  
            if 'email' not in studentData or 'name' not in studentData:
                return error(message='Must provide a name and email for each student.')
            
            student = ClassSectionStudent(
                name=studentData['name'],
                email=studentData['email'], 
                class_section_id=class_id
            )
            students.append(student)
        
        db.session.add_all(students)
        db.session.commit()
        return jsonify([s.serialize() for s in students])
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/heartbeat', methods=['POST'])
def student_heartbeat(student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
            return error(404, message='This student does not exist')

        json = request.get_json()
        device_id = json.get('device_id')
        if device_id is None:
            raise ValueError('Must provide a device ID')

        prev_heartbeat = StudentHeartbeat.query \
            .filter_by(student_id=student_id) \
            .filter_by(device_id=device_id) \
            .order_by(StudentHeartbeat.last_updated.desc()) \
            .first()
        
        skill = json.get('skill')
        if prev_heartbeat is None or prev_heartbeat.skill != skill:
            heartbeat = StudentHeartbeat(
                student_id=student_id,
                device_id=device_id,
                skill=json.get('skill')
            )
            db.session.add(heartbeat)
            db.session.commit()

            print('New heartbeat:')
            print(heartbeat.serialize())

            return jsonify(heartbeat.serialize())
        else:
            prev_heartbeat.repeat()
            db.session.commit()
            print('Updating previous heartbeat')
            return jsonify(prev_heartbeat.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
def delete_class_section_student(class_id, student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)

    try:
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
            return error(404, message='This student does not exist.')
        
        db.session.delete(student)
        db.session.commit()
        return ('', 204)
    except Exception as e:
        return error(error=e)
    
@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['GET'])
def get_class_section_student(class_id, student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)

    try:
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
            return error(404, message='This student does not exist.')
        
        return jsonify(student.serialize())
    except Exception as e:
        return error(error=e)
    
@app.route('/classes/<int:class_id>/students/<int:student_id>', methods=['PATCH'])
def update_class_section_student(class_id, student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
            return error(404, message='This student does not exist.')
        
        json = request.get_json()
        student.name = json.get('name')
        db.session.commit()
        return jsonify(student.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/sign-up', methods=['POST'])
def sign_up(student_id):
    try:
        # Verify that we have all required fields
        json = request.get_json(force=True)
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
          return error(404, message='This student does not exist.')
        
        email = json.get('email')
        if email is None or email != student.email: 
            raise error(403, 'Failed to authenticate sign up.')
            
        password = json.get('password')
        if password is None:
          raise ValueError('Must provide a password.')
          
        # Create the user in firebase (this will check if account already created)
        firebase_user = auth.create_user(
            email=email,
            email_verified=False,
            password=password
        )
        
        student.set_firebase_id(firebase_user.uid)
        db.session.commit()
        return jsonify(student.serialize())
    except Exception as e:
        return error(error=e)
    
@app.route('/students/<int:student_id>/find-guides', methods=['GET'])
def find_guide(student_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    student = ClassSectionStudent.query.get(student_id)
    if student is None:
        return error(404, message='This student does not exist.')

    try:
        skill = request.args.get('skill')
        if skill is None:
            raise ValueError('Must provide a skill.')

        result = _find_guides(student_id, student.class_section_id, skill)        
        return jsonify([dict(r) for r in result])
    except Exception as e:
        return error(error=e)


def _find_guides(student_id, class_id, skill):
    query = """
        select distinct s.* from 
            class_section_student s,
            (
                select * from ka_skill_completion
                    where
                        skill = '%s'
                    and (
                        mastery_category = 'mastered' 
                        or mastery_category = 'proficient'
                        or questions_correct = questions_out_of
                    )
            ) as c
        where
            s.id != %d
            and s.class_section_id = %d
            and s.id = c.student_id
    """ % (skill.lower(), student_id, class_id)

    return db.session.execute(query)


"""
    KA Skill Completion
"""
@app.route('/ka-skill-completion', methods=['POST'])
def create_ka_skill_completion():
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)

    try:
        json = request.get_json(force=True)
        
        user_id = json.get('user_id')
        if user_id is None:
            raise ValueError('Must provide a user ID.')
        
        skill = json.get('skill')
        if skill is None:
            raise ValueError('Must provide a skill.')
        
        recorded_from = json.get('recorded_from')
        if recorded_from is None:
            raise ValueError('Must provide recorded_from.')
            
        completion = KASkillCompletion(
            user_id=user_id,
            course=json.get('course'),
            unit=json.get('unit'),
            skill=skill.lower(),
            questions_correct=json.get('questions_correct'),
            questions_out_of=json.get('questions_out_of'),
            mastery_category=json.get('mastery_category'),
            mastery_points=json.get('mastery_points'),
            mastery_points_out_of=json.get('mastery_points_out_of'),
            recorded_from=json.get('recorded_from')
        )
        db.session.add(completion)
        db.session.commit()
        return jsonify(completion.serialize())
    except Exception as e:
        return error(error=e)
    

@app.route('/ka-skill-completion/create-multiple-by-student-name', methods=['POST'])
def create_multi_ka_skill_completion_by_name():
    """
    Expects a payload containing a mapping of studentName => completion[]. This method
    will fill in the user IDs, commit the data to the database, then return the following
    data:
    
    {
        unrecognized_students: string[],
        completions: completion[]
    }
    
    This is intended for use with the teacher dashboard.
    """
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        json = request.get_json()
        new_completions = []
        unrecognized_students = []
        for name, completions in json.items():
            student = ClassSectionStudent.query.filter_by(name=name).first()
            if student is None:
                unrecognized_students.append(name)
                continue
            
            for completion_dict in completions:
                completion_dict['student_id'] = student.id
                completion = _completion_from_dict(completion_dict)
                new_completions.append(completion)
        
        db.session.add_all(new_completions)
        db.session.commit()
        return jsonify({
            'completions': [c.serialize() for c in new_completions],
            'unrecognized_students': unrecognized_students
        })
    except Exception as e:
        return error(error=e)


def _completion_from_dict(d):
    return KASkillCompletion(
        student_id=d.get('student_id'),
        course=d.get('course'),
        unit=d.get('unit'),
        skill=d.get('skill').lower(),
        questions_correct=d.get('questions_correct'),
        questions_out_of=d.get('questions_out_of'),
        mastery_category=d.get('mastery_category'),
        mastery_points=d.get('mastery_points'),
        mastery_points_out_of=d.get('mastery_points_out_of'),
        recorded_from=KASkillCompletionSource[d.get('recorded_from')]
    )


@app.route('/students/<int:student_id>/ka-skill-completions', methods=['GET'])
def get_ka_skill_completions_for_student(student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        completions = KASkillCompletion.query.filter_by(student_id=student_id)
        return jsonify([c.serialize() for c in completions])
    except Exception as e:
        return error(error=e)
    

@app.route('/ka-skill-completion', methods=['GET'])
def get_ka_skill_completions():
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        start_time = request.args.get('start_time')
        if start_time is not None:
            time = datetime.datetime.utcfromtimestamp(int(start_time))
            completions = KASkillCompletion.query.filter(KASkillCompletion.created_at >= time)
            return jsonify([c.serialize() for c in completions])
        
        return jsonify([c.serialize() for c in KASkillCompletion.query.all()])
    except Exception as e:
        return error(error=e)
    

@app.route('/ka-skill-completion/<int:id>', methods=['GET'])
def get_ka_skill_completion(id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)

    try:
        completion = KASkillCompletion.query.get(id)
        if completion is None:
            return error(404, 'This skill completion does not exist.')
        
        return jsonify(completion.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/ka-skill-completions', methods=['POST'])
def create_ka_skill_completion_for_student(student_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        student = ClassSectionStudent.query.get(student_id)
        if student is None:
            return error(404, message='This student does not exist.')

        json = request.get_json(force=True)
        if json is None:
            return error(message='Must provide a JSON payload.')

        json['student_id'] = student_id
        completion = _completion_from_dict(json)

        response_data = {}
        if completion.is_struggling():
            result = find_matches(student, 'e4n', {'skill': completion.skill})
            response_data['guides'] = [dict(r) for r in result]

        online_mode = OnlineMode.get()
        response_data['is_online'] = online_mode.is_online

        db.session.add(completion)
        db.session.commit()
        response_data['completion'] = completion.serialize()
        return jsonify(response_data)
    except Exception as e:
        return error(error=e)


"""
    Tutoring Sessions
"""
@app.route('/tutoring-sessions', methods=['POST'])
def create_tutoring_session():
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        json = request.get_json()

        guide_id = json.get('guide_id')
        if guide_id is None:
            raise ValueError('Must provide a guide')
        
        learner_id = json.get('learner_id')
        if learner_id is None:
            raise ValueError('Must provide a learner')

        guide = ClassSectionStudent.query.get(guide_id)
        if guide is None:
            raise ValueError('This guide does not exist')

        # Check if the learner or guide is currently in a session
        # ERROR MESSAGES ASSUME THE SESSION IS ALWAYS CREATED BY THE LEARNER
        learner_session = TutoringSession.query \
            .filter(TutoringSession.end_time.is_(None)) \
            .filter(or_(TutoringSession.learner_id == learner_id, TutoringSession.guide_id == learner_id)) \
            .first()
        if learner_session is not None:
            raise ValueError('You are already in a session. Please refresh.')

        guide_session = TutoringSession.query \
            .filter(TutoringSession.end_time.is_(None)) \
            .filter(or_(TutoringSession.learner_id == guide_id, TutoringSession.guide_id == guide_id)) \
            .first()
        if guide_session is not None:
            raise ValueError('Guide is already in a session. Please select another guide.')

        skill = json.get('skill')
        if skill is None:
            raise ValueError('Must provide a skill')

        learner = ClassSectionStudent.query.get(learner_id)
        if learner is None:
            raise ValueError('This learner does not exist')

        is_online = OnlineMode.get().is_online
        conference_link = json.get('conference_link')
        if is_online and (conference_link is None or conference_link == ''):
            raise ValueError('Must provide a conference link.')

        session = TutoringSession(
            guide_id=guide_id,
            learner_id=learner_id,
            skill=skill.lower(),
            manually_requested=json.get('manually_requested'),
            online_mode=is_online,
            conference_link=conference_link
        )
        db.session.add(session)
        db.session.commit()
        return jsonify(session.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions', methods=['GET'])
def get_all_tutoring_sessions():
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)

    try:
        sessions = TutoringSession.query.all()
        return jsonify([s.serialize() for s in sessions])
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>', methods=['GET'])
def get_tutoring_session(session_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist.')

        return jsonify(session.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/tutoring-sessions/current-learning', methods=['GET'])
def get_current_student_tutoring_session(student_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        session = TutoringSession.query \
            .filter_by(learner_id=student_id) \
            .filter(TutoringSession.end_time.is_(None)) \
            .first()

        if session is None:
            return ('', 204)
        
        guide = ClassSectionStudent.query.get(session.guide_id)
        return jsonify({
            'guide': guide.serialize(),
            'session': session.serialize()
        })
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/tutoring-sessions/current-guide-online', methods=['GET'])
def get_current_guide_online_session(student_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)
    
    try:
        session = TutoringSession.query \
            .filter_by(guide_id=student_id) \
            .filter(TutoringSession.end_time.is_(None)) \
            .filter(TutoringSession.conference_link.isnot(None)) \
            .filter_by(request_status=SessionRequestStatus.accepted) \
            .first()

        if session is None:
            return ('', 204)
        
        learner = ClassSectionStudent.query.get(session.learner_id)
        return jsonify({
            'learner': learner.serialize(),
            'session': session.serialize()
        })
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/tutoring-sessions/pending-guide', methods=['GET'])
def get_pending_sessions_for_guide(student_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)
    
    try:
        session = TutoringSession.query \
            .filter_by(guide_id=student_id) \
            .filter_by(request_status='pending') \
            .first()

        if session is None:
            return ('', 204)

        learner = ClassSectionStudent.query.get(session.learner_id)
        return jsonify({
            'learner': learner.serialize(),
            'session': session.serialize()
        })
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/cancellation-reasons', methods=['GET'])
def get_cancellation_reasons():
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)
    
    try:
        return jsonify([
            {'value': 'guide_unavailable', 'title': 'Guide Unavailable'},
            {'value': 'wrong_guide', 'title': 'Wrong Guide'}
        ])
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>/cancel', methods=['POST'])
def cancel_tutoring_session(session_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        json = request.get_json()
        reason = json.get('cancellation_reason')
        if reason is None:
            raise ValueError('Must provide a reason')

        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist.')
        
        session.cancel(reason)
        db.session.commit()
        return jsonify(session.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>/accept', methods=['POST'])
def accept_tutoring_session(session_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)
    
    try:
        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist')

        session.accept()
        db.session.commit()
        return ('', 204)
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>/reject', methods=['POST'])
def reject_tutoring_session(session_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist')

        json = request.get_json()
        note = json.get('note')
        if note is None:
            raise ValueError('Must provide a rejection note')

        print(session.serialize())
        session.reject(note)
        db.session.commit()
        return ('', 204)
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>/finish', methods=['POST'])
def finish_tutoring_session(session_id):
    try:
        verify_user()
    except Exception as e:
        return error(403, error=e)

    try:
        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist.')
        
        session.finish()
        db.session.commit()
        return jsonify(session.serialize())
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>/completion-before', methods=['GET'])
def get_completion_before_session(session_id):
    try:
        verify_admin()
    except Exception as e:
        return error(error=e)

    try:
        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist.')

        query = """
            select * from ka_skill_completion
            where 
                created_at < '%s'
                and skill = '%s'
                and (recorded_from = 'unit_view_task' or recorded_from = 'lesson_view_task')
            order by created_at desc
            limit 1
        """ % (session.start_time, session.skill)

        result = db.session.execute(query).first()
        if result is None:
            return ('', 204)
        else:
            return jsonify(dict(result))
    except Exception as e:
        return error(error=e)


@app.route('/tutoring-sessions/<int:session_id>/completion-after', methods=['GET'])
def get_completion_after_session(session_id):
    try:
        verify_admin()
    except Exception as e:
        return error(error=e)

    try:
        session = TutoringSession.query.get(session_id)
        if session is None:
            return error(404, message='This session does not exist.')

        date = session.end_time if session.end_time else session.start_time
        query = """
            select * from ka_skill_completion
            where 
                created_at > '%s'
                and skill = '%s'
                and (recorded_from = 'unit_view_task' or recorded_from = 'lesson_view_task')
            order by created_at asc
            limit 1
        """ % (date, session.skill)

        result = db.session.execute(query).first()
        if result is None:
            return ('', 204)
        else:
            return jsonify(dict(result))
    except Exception as e:
        return error(error=e)


@app.route('/classes/<int:class_id>/tutoring-sessions', methods=['GET'])
def get_tutoring_sessions_for_class(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        query = """
            select distinct t.* from
                class_section_student s,
                tutoring_session t,
                class_section c
            where
                t.guide_id = s.id 
                and s.class_section_id = c.id 
        """
        result = db.session.execute(query)
        return jsonify([dict(r) for r in result])
    except Exception as e:
        return error(error=e)


@app.route('/students/<int:student_id>/tutoring-sessions', methods=['GET'])
def get_sessions_for_student(student_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        sessions = TutoringSession.query.filter(
            (TutoringSession.guide_id == student_id) | (TutoringSession.learner_id == student_id)
        )
        return jsonify([s.serialize() for s in sessions])
    except Exception as e:
        return error(error=e)


"""
    Skills
"""
@app.route('/classes/<int:class_id>/skills', methods=['GET'])
def get_skills_for_class(class_id):
    try:
        verify_admin()
    except Exception as e:
        return error(403, error=e)
    
    try:
        query = """
            select distinct skill from
                ka_skill_completion c,
                class_section_student s
            where
                c.student_id = s.id
                and s.class_section_id = %d
        """ % (class_id)
        result = db.session.execute(query)
        return jsonify([r[0] for r in result])
    except Exception as e:
        return error(error=e)