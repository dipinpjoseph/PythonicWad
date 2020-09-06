from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__, static_url_path='')
app.config["APPLICATION_ROOT"] = "/irithm"
app.config['SECRET_KEY'] = "Please don't copy. Just an exp"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://user_irithm:biridb@localhost/db_irithm'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)

from app import routes
