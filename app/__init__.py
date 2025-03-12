from flask import Flask
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
csrf = CSRFProtect(app=app)
