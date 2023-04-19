
import json 
from configparser import ConfigParser
from pathlib import Path

basedir = Path(__file__).parent.parent
config = ConfigParser()
config.read(Path(basedir, "config.ini"))

basedir = Path(__file__).parent
DEBUG = json.loads(str(config.get('base', 'DEBUG')).lower())

class Config(object):
    DEBUG = DEBUG 
    SECRET_KEY = config.get('base', 'secret_key')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 360
    SERVER_BASE_URL = config.get("base", "server_base_url")

    PROJECT_NAME = config.get('base', 'project_name')
    PROJECT_VERSION = config.get('base', 'project_version')
    API_VERSION = "v1"

    # database configs
    DB_NAME = config.get('database', 'name')
    DB_USERNAME = config.get('database', 'user')
    DB_PASSWORD = config.get('database', 'password')
    DB_HOST = config.get('database', 'host', fallback='localhost')
    DB_PORT = config.get('database', 'port', fallback=3306)

    SQLALCHEMY_DATABASE_URI = f'mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

    # mongodb database configs
    MONGODB_NAME = config.get('mongodb', 'name')
    MONGODB_USERNAME = config.get('mongodb', 'user')
    MONGODB_PASSWORD = config.get('mongodb', 'password')
    MONGODB_HOST = config.get('mongodb', 'host', fallback='localhost')
    MONGODB_PORT = config.get('mongodb', 'port', fallback=27017)

    MONGODB_DATABASE_URI = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/?authSource={MONGODB_NAME}"

    STAGGING_MONGODB_NAME = config.get('mongodb', 'stagging_name')
    MONGODB_STAGGING_DATABASE_URI = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/?authSource={STAGGING_MONGODB_NAME}"

    BASE_DIR = basedir
    VERIFICATION_URL = config.get('base', 'verification_url')
    PASSWORD_RESET_URL = config.get('base', 'password_reset_url')

    # email configurations
    MAIL_SENDER_NAME = config.get('mail', 'mail_sender_name')
    MAIL_SERVER = config.get('mail', 'mail_server')
    MAIL_USERNAME = config.get('mail', 'mail_username')
    MAIL_PASSWORD = config.get('mail', 'mail_password')
    MAIL_PORT = config.get('mail', 'mail_port')
    MAIL_USE_TLS = json.loads(str(config.get('mail', 'mail_use_tls')).lower())

    # Media Settings
    IMAGE_FORMATS = config.get('media', 'image_formats')
    MEDIA_BASE_URL = f"{SERVER_BASE_URL}/cdn"

    # gearman
    GEARMAN_CLIENT_HOST_LIST = config.get('server', 'gearman_client_host_list').replace(" ", "").split(',')
    GEARMAN_WORKER_HOST_LIST = config.get('server', 'gearman_worker_host_list').replace(" ", "").split(',')

    # redis
    REDIS_SERVER_HOST = config.get('server', 'redis_server_host')
    REDIS_SERVER_PORT = config.get('server', 'redis_server_port')
    REDIS_DEFAULT_DB = config.get('server','redis_default_db')


settings = Config()
