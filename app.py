""" The main app module.
This is the main app module and contains the WSGI handler.

This app also exposes routes which are registered under

"""

from flask import Flask, jsonify, request, redirect, url_for, session, flash, send_from_directory
from flask_cors import CORS

from modules.cases import cases
from modules.case_info import case_info
from modules.admins import admins
from modules.clinicians import clinicians, requires_clinician
from modules.event_log import event_log, log_event
from modules.extensions import mysql, check_database_
from modules.chat_messages import chat_messages


app = Flask(__name__, static_folder="static")
app.config.from_pyfile("app.conf")
CORS(app)
mysql.init_app(app)

app.register_blueprint(cases)
app.register_blueprint(case_info, url_prefix="/case<info_table>")
app.register_blueprint(clinicians, url_prefix="/clinicians")
app.register_blueprint(admins, url_prefix="/admins/")
app.register_blueprint(event_log, url_prefix="/event_log")
app.register_blueprint(chat_messages, url_prefix="/chat_messages")


@app.route("/")
def index():
    """ Default endpoint.

    """
    return app.send_static_file('noauth.html')
    # Changed to HTML page
    # if check_database_():
    #     return jsonify({"success": True})
    # else:
    #     return jsonify({"success": False, "error_type": "database"}), 500


@app.route("/version/", methods=(["GET"]))
def get_version():
    version = app.config.get("VERSION")
    if version:
        return jsonify({"success": True, "version": version})
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "error_type": "version",
                    "debugmsg": "Version not specified",
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
