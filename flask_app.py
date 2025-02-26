from core import app
from sys import platform
from c import secret_key
app.static_url_path="core/static/"
app.secret_key = secret_key


if __name__ == "__main__" and platform == "win32":
    app.run()
