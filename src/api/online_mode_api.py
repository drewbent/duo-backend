import sys
import os
from flask import Blueprint, jsonify, request

from ..utils.api_utils import *
from ..utils.auth import *
from ..models import *

online_mode_api = Blueprint('online_mode_api', __name__)

@online_mode_api.route('/online-mode', methods=['POST'])
def set_online_mode():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    json = request.get_json()
    is_online = json.get('is_online')
    if is_online is None:
      raise ValueError('Must provide is_online')

    OnlineMode.set_online(is_online)
    db.session.commit()
    return ('', 204)
  except Exception as e:
    return error(error=e)


@online_mode_api.route('/online-mode', methods=['GET'])
def get_online_mode():
  try:
    verify_admin()
  except Exception as e:
    return error(403, error=e)
  
  try:
    return jsonify(OnlineMode.get().serialize())
  except Exception as e:
    return error(error=e)