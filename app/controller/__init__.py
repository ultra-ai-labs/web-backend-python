
def register_blueprints(app):
    from app.controller.comment_crawler import crawler_bp
    app.register_blueprint(crawler_bp, url_prefix='')
    from app.controller.active_market import message_bp
    app.register_blueprint(message_bp, url_prefix='')
    from app.controller.comment_analysis import analysis_bp
    app.register_blueprint(analysis_bp, url_prefix='')


def register_blueprints_test(app):
    from app.controller.comment_crawler import crawler_bp
    app.register_blueprint(crawler_bp, url_prefix='/dev')
    from app.controller.active_market import message_bp
    app.register_blueprint(message_bp, url_prefix='/dev')
    from app.controller.comment_analysis import analysis_bp
    app.register_blueprint(analysis_bp, url_prefix='/dev')
