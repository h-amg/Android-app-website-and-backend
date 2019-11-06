# app/config_sample.py

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig(object):
    """Base configuration."""
    SECRET_KEY = 'secret_key'
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 8
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'database_uri'


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev.sqlite')
    DEBUG_TB_ENABLED = True


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 1
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class ProductionConfig(BaseConfig):
    """Production configuration."""
    SECRET_KEY = 'SECRET_KEY'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'DATABASE_URI'
    DEBUG_TB_ENABLED = False

