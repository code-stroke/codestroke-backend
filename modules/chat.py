""" For accessing and posting chat messages about a case.

Implemented with HTTP / REST + push notifications for now, 
Should use XMPP / web sockets in the future.

"""

from flask import jsonify, request, Blueprint, current_app as app

chat_messages = Blueprint("chat_messages", __name__)

@cases.route("/chat_messages/view/", methods=(["GET"]))
@requires_clinician
def get_chat_messages(case_id):
    result = ext.select_query_result_({"case_id":case_id}, "chat_messages")
    result["success"] = True
    return jsonify(result)

@cases.route("/chat_messages/add/", methods=(["POST"]))
@requires_clinician
def add_chat_message():
    cursor = ext.connect_()
    cols_chat_messages = ext.get_cols_("chat_messages")
    args_chat_messages = ext.get_args_(cols_chat_messages, request.get_json())
    add_params = ext.add_(args_chat_messages)
    add_query = "insert into chat_messages " + add_params[0]
    cursor.execute(add_query, add_params[1])
    result = cursor.fetchall()

    args_event = {}
    notified = notify.add_message(notify_type, case_id, args_event)

@cases.route("/delete/<int:chat_message_id>/", methods=(["DELETE"]))
@requires_clinician
def remove_chat_message():
    pass

