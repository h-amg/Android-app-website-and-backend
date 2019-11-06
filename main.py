import os
# from flask_script import Manager

from app.webapp import create_app

app = create_app(os.environ['APP_SETTINGS'])


if __name__ == '__main__':
    app.run(debug=False)
