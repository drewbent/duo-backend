from flask import jsonify

def error(http_error=400, message=None, error=None):
  errorMessage = 'Something went wrong.'
  if message is not None:
    errorMessage = message
  elif error is not None:
    errorMessage = str(error)
      
  return jsonify({'message': errorMessage, 'error': True}), http_error


def get_values(json, keys):
  values = []
  for key in keys:
    value = json.get(key)
    if value is None:
      raise ValueError('Must provide a %s' % key)
    else:
      values.append(value)
  
  if len(values) == 1:
    return values[0]
  else:
    return values