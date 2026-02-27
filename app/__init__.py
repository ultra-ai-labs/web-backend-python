from flask import Flask, g
from flask_cors import CORS

from app.extensions import db, migrate
from config import PYMYSQL_PROD_DB_URL
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def create_app():
    n_app = Flask(__name__)
    n_app.config['SQLALCHEMY_DATABASE_URI'] = PYMYSQL_PROD_DB_URL
    n_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



    # 配置跨域：显式允许开发常用来源并支持凭证和授权头
    CORS(n_app,
         resources={r"/*": {"origins": [
             "http://localhost:3000",
             "http://localhost:3001",
             "http://127.0.0.1:3001",
             "http://ultra-ai.site",
             "http://43.132.185.90",
             "http://43.132.185.90:3000",
             "http://43.132.185.90:3001",
             "http://43.161.246.45"
         ]}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "x-admin-password"],
         expose_headers=["Authorization"])

    # reduce noisy third-party library logging
    import logging
    for noisy in ("httpx", "qcloud_cos.cos_client", "qcloud_cos"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # 初始化拓展
    # with n_app.app_context():
    db.init_app(n_app)
    # migrate.init_app(n_app, db)
    Migrate(n_app, db)
    with n_app.app_context():
        from app import model

    # 注册蓝图
    from app.controller import register_blueprints
    register_blueprints(n_app)

    # db.create_all()
    return n_app


def create_app_with_test():
    n_app = Flask(__name__)
    n_app.config['SQLALCHEMY_DATABASE_URI'] = PYMYSQL_PROD_DB_URL
    n_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 配置跨域：显式允许开发常用来源并支持凭证和授权头
    CORS(n_app,
         resources={r"/*": {"origins": [
             "http://localhost:3000",
             "http://localhost:3001",
             "http://127.0.0.1:3001",
             "http://ultra-ai.site",
             "http://43.132.185.90",
             "http://43.132.185.90:3000",
             "http://43.132.185.90:3001",
         ]}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "x-admin-password"],
         expose_headers=["Authorization"])
    @n_app.before_request
    def handle_options_test():
        from flask import request, make_response
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin')
            allowed = [
                'http://ultra-ai.site',
                'http://43.132.185.90',
                'http://43.161.246.45',
                'http://localhost:3000',
                'http://localhost:3001',
            ]
            resp = make_response('', 204)
            if origin and origin in allowed:
                resp.headers['Access-Control-Allow-Origin'] = origin
                resp.headers['Access-Control-Allow-Credentials'] = 'true'
                resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,x-admin-password'
                resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
            else:
                resp.headers['Access-Control-Allow-Origin'] = 'null'
            return resp
        # Ensure CORS headers are always present (helps with preflight failures)
        @n_app.after_request
        def add_cors_headers(response):
            origin = response.headers.get('Access-Control-Allow-Origin')
            if not origin:
                response.headers.add('Access-Control-Allow-Origin', 'http://ultra-ai.site')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-admin-password')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
        @n_app.after_request
        def add_cors_headers_test(response):
            origin = response.headers.get('Access-Control-Allow-Origin')
            if not origin:
                response.headers.add('Access-Control-Allow-Origin', 'http://ultra-ai.site')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-admin-password')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response

    # 初始化拓展
    # with n_app.app_context():
    db.init_app(n_app)
    # migrate.init_app(n_app, db)
    Migrate(n_app, db)
    with n_app.app_context():
        from app import model

    # 注册蓝图
    from app.controller import register_blueprints_test
    register_blueprints_test(n_app)

    # db.create_all()
    return n_app
