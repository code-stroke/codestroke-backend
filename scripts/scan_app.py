""" Script to scan for routes.

One-off script to scan for routes in app and convert to API blueprint.

"""

import re
import glob

matches = []

re_route = r"@.*.route.*\n@a?.*"

with open("../app.py") as app_file:
    app_matches = re.findall(re_route, app_file.read())
    matches += app_matches

for module_file in glob.glob("../modules/*.py"):
    with open(module_file) as module:
        new_matches = re.findall(re_route, module.read())
        print(new_matches)
        matches += new_matches

with open("../docs/api.apib", "w+") as outfile:
    for match in matches:
        outfile.write(match + "\n")
