# From https://realpython.com/flask-by-example-part-1-project-setup/

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
  SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

class ProductionConfig(Config):
  DEVELOPMENT = False

class DevelopmentConfig(Config):
  DEVELOPMENT = True
