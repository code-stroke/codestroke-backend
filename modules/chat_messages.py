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

chat_messages = Blueprint("chat_messages", __name__)

@chat_messages.route("/view/<int:case_id>", methods=(["GET"]))
def get_chat_messages(case_id):
    try:
        result = ext.select_query_result_({"case_id":case_id},
                                          "chat_messages")
        result["success"] = True
        return jsonify(result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"success": False, "debug_info": str(e)}), 500

@chat_messages.route("/add/", methods=(["POST"]))
def add_chat_message():
    try:
        json = request.get_json()
        cursor = ext.connect_()
        cursor.execute("""insert into 
        chat_messages(case_id, username, message) 
        values (%s,%s,%s)""",
        (json["case_id"], json["username"], json["message"])) 

        case_id = cursor.lastrowid 
        ext.mysql.connection.commit()
        args_event = {"message":json["message"],
                      "username":json["username"]}
        
        notify_type = "chat_message_incoming"
        notified = notify.add_chat_message(_event)
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
        import traceback
        print(traceback.format_exc())
        return jsonify({"success": False, "debug_info": str(e)}), 500


@chat_messages.route("/delete/<int:chat_message_id>/", methods=(["DELETE"]))
@requires_clinician
def remove_chat_message():
    pass

