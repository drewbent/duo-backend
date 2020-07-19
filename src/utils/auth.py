from flask import request
from firebase_admin import auth

admin_emails = []

def verify_admin():
  auth_header = request.headers.get('Authorization')
  token = __parseAuthHeader(auth_header)
  decoded_token = auth.verify_id_token(token)
  
  if not is_admin(decoded_token['email']):
    raise ValueError('Invalid Email')
  

def is_admin(email):
  return email in admin_emails

  
def verify_user():
  auth_header = request.headers.get('Authorization')
  token = __parseAuthHeader(auth_header)
  auth.verify_id_token(token)
  

def __parseAuthHeader(string):
  """
  Returns the token given an input of 'Bearer <token>'
  """
  components = string.split(' ')
  if len(components) != 2:
    raise ValueError('Invalid authorization header.')

  return components[1]