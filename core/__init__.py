from flask import Flask
import os
app = Flask(__name__, instance_path = os.path.abspath("core/"))
app.config.from_object(__name__)


from core import routes