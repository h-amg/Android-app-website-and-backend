# app/webapp.py

# This script used as an alternative to __init__.py (in app module)
# to create the app module deployed to gooogle cloud appp engiune

import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy

login_manager = LoginManager()
bcrypt = Bcrypt()
db = SQLAlchemy()


def create_app(config):
	app = Flask(__name__, static_folder='static')
	app.config.from_object(config)


	login_manager.init_app(app)
	bcrypt.init_app(app)
	db.init_app(app)

	from app.mod_main.views import main_blueprint  # noqa: E402
	from app.mod_user.views import user_blueprint  # noqa: E402
	from app.mod_api.endpoints import api_blueprint  # noqa: E402
	from app.mod_webhook.df_fulfillment import webhook_blueprint
	from app.mod_billing.billing import billing_blueprint
	from app.mod_twilio.access_token import twilio_blueprint
	from app.mod_main.views import privacy_blueprint
	from app.mod_main.views import promo_blueprint

	app.register_blueprint(main_blueprint)
	app.register_blueprint(user_blueprint)
	app.register_blueprint(api_blueprint)
	app.register_blueprint(webhook_blueprint)
	app.register_blueprint(billing_blueprint)
	app.register_blueprint(twilio_blueprint)
	app.register_blueprint(privacy_blueprint)
	app.register_blueprint(promo_blueprint)

	from app.models import User  # noqa: E402

	login_manager.login_view = "user.login"


	@login_manager.user_loader
	def load_user(user_id):
		return User.query.filter(User.id == int(user_id)).first()

	@app.errorhandler(400)
	def bad_request(error):
		return render_template("errors/404.html"), 400
	
	@app.errorhandler(404)
	def page_not_found(error):
		return render_template("errors/404.html"), 404


	@app.errorhandler(500)
	def server_error_page(error):
		return render_template("errors/500.html"), 500


	@app.errorhandler(403)
	def forbidden_page(error):
		return render_template("errors/403.html"), 403

	return app
