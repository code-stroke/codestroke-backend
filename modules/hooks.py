""" For "hooks" into different functions.

This module contains functions that produce desirable side-effects (e.g.
notifications and filters).

"""


import datetime
from pytz import timezone

import modules.notify as notify
import modules.filters as filters


def fetch(result, table):
    filtered_rows = filters.fetch_filter(result, table)
    return filtered_rows


def put(info_table, case_id, new_data, prior_data):

    edited_data, edited_keys, additional_data = filters.put_filter(
        info_table, case_id, new_data, prior_data
    )

    if "status" in edited_keys:

        if edited_data["status"] == "active":
            edited_data["active_timestamp"] = time_now()
            notify.add_message("case_arrived", case_id, additional_data)

        if edited_data["status"] == "completed":
            edited_data["completed_timestamp"] = time_now()
            notify.add_message("case_completed", case_id, additional_data)

    if "likely_lvo" in edited_keys and edited_data["likely_lvo"]:
        notify.add_message("likely_lvo", case_id, additional_data)

    if info_table == "case_radiologies":
        if (
            "ct_available" in edited_keys
            and "ct_available_loc" in edited_keys
            and edited_data["ct_available"]
        ):
            additional_data["ct_available_loc"] = edited_data.get("ct_available_loc")
            notify.add_message("ct_available", case_id, additional_data)

        if "ct_complete" in edited_keys and edited_data["ct_complete"]:
            notify.add_message("ctb_completed", case_id, additional_data)

        if "do_cta_ctp" in edited_keys and edited_data["do_cta_ctp"]:
            notify.add_message("do_cta_ctp", case_id, additional_data)

        if "cta_ctp_complete" in edited_keys and edited_data["cta_ctp_complete"]:
            notify.add_message("cta_ctp_complete", case_id, additional_data)

        if (
            "large_vessel_occlusion" in edited_keys
            and edited_data["large_vessel_occlusion"]
        ):
            notify.add_message("large_vessel_occlusion", case_id, additional_data)

    if info_table == "case_managements":

        if "ecr" in edited_keys and edited_data["ecr"]:
            notify.add_message("ecr_activated", case_id, additional_data)

    return edited_data


def time_now():
    # TODO Make more flexible in the future
    return datetime.datetime.now(timezone("Australia/Melbourne")).strftime(
        "%Y-%m-%d %H:%M"
    )
