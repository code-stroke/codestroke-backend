""" For accessing and posting chat messages about a case.

Implemented with HTTP / REST + push notifications for now,
Should use XMPP / web sockets in the future.

"""

from flask import jsonify, request, Blueprint, current_app as app

from modules.clinicians import requires_clinician
from modules.case_info import case_info
import modules.extensions as ext
from modules.extensions import mysql
from modules.event_log import log_event
import modules.notify as notify
import modules.hooks as hooks
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

chat_messages = Blueprint("chat_messages", __name__)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chat_messages.route("/view/<int:case_id>", methods=(["GET"]))
@requires_clinician
def get_chat_messages(case_id):
    try:
        result = ext.select_query_result_({"case_id":case_id},
                                          "chat_messages")
        result["success"] = True
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "debug_info":str(e)}), 500

@chat_messages.route("/image/add/", methods=(["POST"]))
@requires_clinician
def upload_image():
    if 'file' not in request.files:
        return jsonify({"success":False, debug_info:"No file"}), 404
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success":False, debug_info:"No filename"}), 404
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # if file has been saved, get the metadata and URL, add it to db 
        case_id = request.form.get('case_id')
        username = request.form.get('username')
        url = request.host_url + "protected/" + filename
        return _db_add_chat_message(case_id, username, url)
    return jsonify({"success":False})

@chat_messages.route("/add/", methods=(["POST"]))
@requires_clinician
def add_chat_message():
    json = request.get_json()
    return _db_add_chat_message(json["case_id"], json["username"], json["message"])

def _db_add_chat_message(case_id, username, message):
    try:
        json = request.get_json()
        cursor = ext.connect_()
        cursor.execute("""insert into
        chat_messages(case_id, username, message, message_timestamp)
        values (%s,%s,%s,%s)""",
        (case_id, username, message, hooks.time_now()))

        case_id = cursor.lastrowid
        ext.mysql.connection.commit()
        args_event = {"message":message,
                      "username":username}

        notify_type = "chat_message_incoming"
        notified = notify.add_chat_message(args_event)
        if not notified:
            return jsonify(
                {
                    "success": True,
                    "case_id": case_id,
                    "debugmsg": "Notification not sent.",
                }
            )
        return jsonify({"success": True, "case_id":case_id})
    except Exception as e:
        return jsonify({"success": False, "debug_info": str(e)}), 500

@chat_messages.route("/delete/<int:chat_message_id>/", methods=(["DELETE"]))
@requires_clinician
def remove_chat_message():
    try:
        json = request.get_json()
        cursor = ext.connect_()
        cursor.execute("""delete from
        chat_messages where
        case_id = %s and username = %s and message = %s""",
        (json["case_id"], json["username"], json["message"]))
        ext.mysql.connection.commit()
        return jsonify({"success": True, "case_id":json["case_id"]})
    except Exception as e:
        return jsonify({"success": False, "debug_info": str(e)}), 500
