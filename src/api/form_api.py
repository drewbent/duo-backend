import sys
import os
from flask import Blueprint, jsonify, request

from ..utils.api_utils import *
from ..utils.auth import *
from ..models import *

form_api = Blueprint('form_api', __name__)

"""
  Questions
"""
@form_api.route('/question-types', methods=['GET'])
def get_question_types():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)

  return jsonify([t.name for t in QuestionType])


@form_api.route('/questions', methods=['GET'])
def get_questions():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)

  try:
    arg_num_responses = request.args.get('num_responses')
    include_num_responses = arg_num_responses is None or arg_num_responses == 'true'

    questions = Question.query.all()

    question_data = []
    for question in questions:
      data = question.serialize(include_num_responses)
      question_data.append(data)

    return jsonify(question_data)
  except Exception as e:
    return error(error=e)


@form_api.route('/questions', methods=['POST'])
def create_question():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)

  try:
    json = request.get_json()
    question = get_question(json)
    db.session.add(question)
    db.session.commit()
    return jsonify(question.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/questions/<int:question_id>', methods=['PATCH'])
def update_question(question_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    question = Question.query.get(question_id)
    if question is None:
      return error(404, message='This question does not exist')

    json = request.get_json()

    if json.get('archive') is not None:
      question.archive(json.get('archive'))

    # To edit the question or options, there must be no responses to this question
    name = json.get('name')
    options = json.get('options')
    if name is not None or options is not None:
      if question.num_responses() > 0:
        raise ValueError('Cannot update a question if it has responses.')
      
      question.name = name
      question.options = options

    db.session.commit()
    return jsonify(question.serialize())
  except Exception as e:
    return error(error=e)


"""
  Forms
"""
@form_api.route('/forms', methods=['POST'])
def create_form():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    name = get_values(json, ['name'])
    form = Form(name=name)
    db.session.add(form)
    db.session.commit()
    return jsonify(form.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/forms', methods=['GET'])
def get_forms():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    forms = Form.query.all()
    return jsonify([f.serialize() for f in forms])
  except Exception as e:
    return error(error=e)


# Date should be formatted yyyy-mm-dd
@form_api.route('/forms/current', methods=['GET'])
def get_current_form():
  try: 
    verify_user()
  except Exception as e:
    return error(403, error=e)

  try:
    class_id = request.args.get('class_id')
    if class_id is None:
      raise ValueError('Must provide a class ID')

    date = request.args.get('date')
    if date is None:
      raise ValueError('Must provide a date')

    distribution = FormDistribution.query \
      .filter_by(applicable_date=date) \
      .filter_by(class_section_id=int(class_id)) \
      .first()

    if distribution is None:
      return ('', 204)

    form = Form.query.get(distribution.form_id)

    form_questions = FormQuestion.query \
      .filter_by(form_id=form.id) \
      .filter(FormQuestion.archived_at.is_(None)) \
      .order_by(FormQuestion.index_in_form)
    
    questions = [
      {
        'form_question': fq.serialize(), 
        'question': Question.query.get(fq.question_id).serialize()
      }
      for fq in form_questions
    ]

    return jsonify({
      'distribution': distribution.serialize(),
      'form': form.serialize(),
      'questions': questions 
    })
  except Exception as e:
    return error(error=e)


@form_api.route('/forms/<int:form_id>', methods=['PATCH'])
def update_form(form_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    form = Form.query.get(form_id)
    if form is None:
      return error(404, message='This form does not exist')

    json = request.get_json()
    name = json.get('name')
    if name is not None:
      form.name = name

    db.session.commit()
    return jsonify(form.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/forms/<int:form_id>', methods=['GET'])
def get_form(form_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    form = Form.query.get(form_id)
    if form is None:
      return error(404, message='This form does not exist')

    return jsonify(form.serialize())
  except Exception as e:
    return error(error=e)


"""
  Form Questions
"""
@form_api.route('/form-questions', methods=['GET'])
def get_form_questions():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    form_questions = FormQuestion.query.all()
    return jsonify([fq.serialize() for fq in form_questions])
  except Exception as e:
    return error(error=e)


@form_api.route('/form-questions/<int:form_question_id>', methods=['PATCH'])
def update_form_question(form_question_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    form_question = FormQuestion.query.get(form_question_id)
    if form_question is None:
      return error(404, message='This form question does not exist')
    
    json = request.get_json()
    if json.get('archive') == True:
      form_question.archive()

    required = json.get('required')
    if required is not None:
      form_question.required = required

    db.session.commit()
    return jsonify(form_question.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/forms/<int:form_id>/form-questions', methods=['GET'])
def get_form_questions_for_form(form_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)

  try:
    form_questions = FormQuestion.query.filter_by(form_id=form_id)
    return jsonify([fq.serialize() for fq in form_questions])
  except Exception as e:
    return error(error=e)


@form_api.route('/form-questions', methods=['POST'])
def create_form_question():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    form_id, question_id = get_values(json, ['form_id', 'question_id'])
    form = Form.query.get(form_id)
    if form is None:
      raise ValueError('Form %d does not exist' % form_id)

    index = max(0, form.num_questions() - 1)
    form_question = FormQuestion(
      form_id=form_id,
      question_id=question_id,
      index_in_form=index
    )
    db.session.add(form_question)
    db.session.commit()
    return jsonify(form_question.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/form-questions/<int:form_question_id>/index', methods=['POST'])
def update_form_question_index(form_question_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()

    form_question = FormQuestion.query.get(form_question_id)
    if form_question is None:
      return error(404, message='This form question does not exist')

    index = json.get('index_in_form')
    if index is None:
      raise ValueError('Must provide a new index')

    form = Form.query.get(form_question.form_id)
    if index >= form.num_questions(): # Max index
      index = form.num_questions() - 1

    if index < 0: # Min index
      index = 0

    old_index = form_question.index_in_form
    if old_index == index:
      return jsonify([form_question.serialize()])

    updated_questions = [form_question]
    if index < old_index:
      # Moving it DOWN; move indices between new and old index UP
      questions = FormQuestion.query \
        .filter_by(form_id=form_question.form_id) \
        .filter(FormQuestion.index_in_form >= index) \
        .filter(FormQuestion.index_in_form < old_index)

      for question in questions:
        question.index_in_form += 1
        updated_questions.append(question)
    else:
      # Moving it UP; move indices between new and old index DOWN
      questions = FormQuestion.query \
        .filter_by(form_id=form_question.form_id) \
        .filter(FormQuestion.index_in_form <= index) \
        .filter(FormQuestion.index_in_form > old_index)
      
      for question in questions:
        question.index_in_form -= 1
        updated_questions.append(question)

    form_question.index_in_form = index
    db.session.commit()
    return jsonify([fq.serialize() for fq in updated_questions])
  except Exception as e:
    return error(error=e)

  
@form_api.route('/forms/<int:form_id>/create-question', methods=['POST'])
def create_question_for_form(form_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    question = get_question(json)
    db.session.add(question)
    db.session.commit()

    form = Form.query.get(form_id)
    if form is None:
      return error(404, message='This form does not exist')

    index = json.get('index_in_form')
    if index is None:
      index = form.num_questions()

    form_question = FormQuestion(
      form_id=form_id,
      question_id=question.id,
      index_in_form=index
    )

    db.session.add(form_question)
    db.session.commit()
    return jsonify({
      'form_question': form_question.serialize(),
      'question': question.serialize()
    })
  except Exception as e:
    return error(error=e)


"""
  Form Distributions
"""
@form_api.route('/form-distributions', methods=['GET'])
def get_distributions():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    distributions = FormDistribution.query.all()
    return jsonify([d.serialize() for d in distributions])
  except Exception as e:
    return error(error=e)


@form_api.route('/form-distributions', methods=['POST'])
def create_form_distribution():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    form_id, class_section_id, applicable_date = get_values(json, ['form_id', 'class_section_id', 'applicable_date'])
    distribution = FormDistribution(
      form_id=form_id,
      class_section_id=class_section_id,
      applicable_date=applicable_date,
    )
    db.session.add(distribution)
    db.session.commit()
    return jsonify(distribution.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/form-distributions/<int:distribution_id>', methods=['DELETE'])
def delete_form_distribution(distribution_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    distribution = FormDistribution.query.get(distribution_id)
    if distribution is None:
      return error(404, message='This distribution does not exist.')
    
    if distribution.num_responses() > 0:
      return error(message='You may not delete a distribution that has been responded to.')

    db.session.delete(distribution)
    db.session.commit()
    return ('', 204)
  except Exception as e:
    return error(error=e)


@form_api.route('/form-distributions/<int:form_distribution_id>', methods=['GET'])
def get_form_distribution(form_distribution_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    distribution = FormDistribution.query.get(form_distribution_id)
    if distribution is None:
      return error(404, message='This distribution does not exist.')
    
    return jsonify(distribution.serialize())
  except Exception as e:
    return error(error=e)


@form_api.route('/forms/<int:form_id>/form-distributions', methods=['GET'])
def get_distributions_for_form(form_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    distributions = FormDistribution.query.filter_by(form_id=form_id)
    return jsonify([d.serialize() for d in distributions])
  except Exception as e:
    return error(error=e)


"""
  Form Responses
"""
@form_api.route('/sessions/<int:session_id>/form-responses', methods=['GET'])
def get_responses_for_session(session_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)

  try:
    responses = FormResponse.query.filter_by(session_id=session_id)
    return jsonify([r.serialize() for r in responses])
  except Exception as e:
    return error(error=e)


@form_api.route('/form-distributions/<int:distribution_id>/form-responses', methods=['GET'])
def get_responses_for_distribution(distribution_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    responses = FormResponse.query.filter_by(form_distribution_id=distribution_id)
    return jsonify([r.serialize() for r in responses])
  except Exception as e:
    return error(error=e)


# Remote method for uploading all responses for a given student, session, and distribution
@form_api.route('/form-responses/feedback', methods=['POST'])
def create_responses_for_distribution():
  try:
    verify_user()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    session_id, student_id, distribution_id, responses = get_values(json, ['session_id', 'student_id', 'distribution_id', 'responses'])
    
    distribution = FormDistribution.query.get(distribution_id)
    if distribution is None:
      raise ValueError('No distribution found for this ID')

    # Check that all required questions are answered
    required_questions = FormQuestion.query \
      .filter_by(form_id=distribution.form_id) \
      .filter(FormQuestion.archived_at.is_(None)) \
      .filter_by(required=True)
    for required_question in required_questions:
      if str(required_question.id) not in responses:
        raise ValueError('Must answer question %s' % required_question.id)

    # Create FormResponse objects
    form_responses = []
    for form_question_id, response in responses.items():
      form_question = FormQuestion.query.get(form_question_id)

      # Make sure this question is part of this distribution
      if form_question.form_id != distribution.form_id:
        raise ValueError('Form question %d is not part of distribution %d' % (form_question_id, distribution_id))
      
      response = FormResponse(
        form_question_id=form_question_id,
        form_distribution_id=distribution_id,
        class_section_student_id=student_id,
        session_id=session_id,
        original_question_index=form_question.index_in_form,
        response=response
      )
      form_responses.append(response)

    db.session.add_all(form_responses)
    db.session.commit()
    return jsonify([fr.serialize() for fr in form_responses])
  except Exception as e:
    return error(error=e)


"""
  Private Methods
"""
def get_question(json):
  question_text, question_type = get_values(json, ['question', 'question_type'])
  return Question(
    question=question_text,
    question_type=question_type,
    options=json.get('options')
  )