import sys
import os
from flask import Blueprint, jsonify, request

from ..utils.api_utils import *
from ..utils.auth import *
from ..models import *

matching_api = Blueprint('matching_api', __name__)

"""
  Algorithms
"""
@matching_api.route('/matching-algorithms', methods=['GET'])
def get_matching_algorithms():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    algorithms = MatchingAlgorithm.query.all()
    return jsonify([a.serialize() for a in algorithms])
  except Exception as e:
    return error(error=e)


@matching_api.route('/matching-algorithms', methods=['POST'])
def create_matching_algorithm():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    name, description, query, = get_values(json, ['name', 'description', 'sql_query'])
    algorithm = MatchingAlgorithm(
      name=name,
      description=description,
      sql_query=query,
      args=json.get('args')
    )
    db.session.add(algorithm)
    db.session.commit()
    return jsonify(algorithm.serialize())
  except Exception as e:
    return error(error=e)


@matching_api.route('/matching-algorithms/<int:algorithm_id>', methods=['PATCH'])
def update_matching_algorithm(algorithm_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    alg = MatchingAlgorithm.query.get(algorithm_id)
    if alg is None:
      return error(404, message='This matching algorith does not exist')

    json = request.get_json()
    
    name = json.get('name')
    if name is not None:
      alg.name = name

    desc = json.get('description')
    if desc is not None:
      alg.description = desc

    query = json.get('sql_query')
    if query is not None:
      alg.sql_query = query

    args = json.get('args')
    if args is not None:
      alg.args = args

    db.session.commit()
    return jsonify(alg.serialize())
  except Exception as e:
    return error(error=e)

  
@matching_api.route('/matching-algorithms/<int:algorithm_id>', methods=['GET'])
def get_matching_algorithm(algorithm_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    alg = MatchingAlgorithm.query.get(algorithm_id)
    if alg is None:
      return error(404, message='This matching algorithm does not exist')
    return jsonify(alg.serialize())
  except Exception as e:
    return error(error=e)


"""
  Active Algorithms
"""
@matching_api.route('/active-matching-algorithms', methods=['POST'])
def create_active_matching_algorithm():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    key, algorithm_id = get_values(json, ['key', 'matching_algorithm_id'])

    # Returns all algorithms that changed
    currents = ActiveMatchingAlgorithm.disable_current(key)

    active = ActiveMatchingAlgorithm(
      matching_algorithm_id=algorithm_id,
      key=key
    )
    db.session.add(active)
    currents.append(active.serialize())
    db.session.commit()
    return jsonify(currents)
  except Exception as e:
    return error(error=e)


@matching_api.route('/active-matching-algorithms', methods=['GET'])
def get_active_matching_algorithms():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    actives = ActiveMatchingAlgorithm.query.all()
    return jsonify([a.serialize() for a in actives])
  except Exception as e:
    return error(error=e)


"""
  Find Matches
"""
@matching_api.route('/students/<int:student_id>/find-matches', methods=['GET'])
def get_matches_for_student(student_id):
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    student = ClassSectionStudent.query.get(student_id)
    if student is None:
      return error(404, message='This student does not exist')

    algorithm_id = request.args.get('algorithm_id')
    if algorithm_id is None:
      raise ValueError('Must provide an algorithm ID')

    algorithm = MatchingAlgorithm.query.get(algorithm_id)
    if algorithm is None:
      return error(404, message='This algorithm does not exist')

    matches = _find_matches(student, algorithm, request.args)
    return jsonify([dict(m) for m in matches])
  except Exception as e:
    return error(error=e)


@matching_api.route('/students/<int:student_id>/find-matches/<string:key>', methods=['GET'])
def get_matches_for_student_with_active_algorithm(student_id, key):
  try:
    verify_user()
  except Exception as e:
    return error(403, error=e)
  
  try:
    student = ClassSectionStudent.query.get(student_id)
    if student is None:
      return error(404, message='This student does not exist')

    result = {
      'matches': [dict(m) for m in find_matches(student, key, request.args)],
      'is_online': OnlineMode.get().is_online
    }
    return result
  except Exception as e:
    return error(error=e)


def find_matches(student, key, reqArgs):
  active = ActiveMatchingAlgorithm.query \
    .filter_by(key=key) \
    .filter(ActiveMatchingAlgorithm.archived_at.is_(None)) \
    .first()

  if active is None:
    raise ValueError('No matching algorithm active for key %s', key)

  algorithm = MatchingAlgorithm.query.get(active.matching_algorithm_id)
  return _find_matches(student, algorithm, reqArgs)


def _find_matches(student, algorithm, reqArgs):
  args = []
  # Build arguments
  for arg in algorithm.args:
    if arg['type'] == 'field':
      args.append(getattr(student, arg['field']))
    elif arg['type'] == 'raw':
      val = reqArgs.get(arg['field'])
      if val is None:
        raise ValueError('Must provide %s' % arg['field'])
      else:
        args.append(val)

  # Return query results
  query = algorithm.sql_query % tuple(args)
  return db.session.execute(query)