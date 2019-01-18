""" Script to scan the schema file.

One-off script to scan and generate text for the API blueprint.

"""

import re

matches = []

with open("../resources/schema.sql") as schema_file:
    schema = schema_file.read().splitlines()

schema = [s.strip() for s in schema]

in_table = False
all_tables = []
current_table = ""
current_fields = []

for line in schema:
    if line.startswith("CREATE TABLE"):
        in_table = True
        current_fields = []
        current_table = re.search(r"`(\w+)`", line)[1]
    elif line.startswith("`"):
        if in_table:
            groups = re.search(r"`(.*?)`\s(.*?)\s(.*)", line)
            current_fields.append((groups[1], groups[2], groups[3]))
    elif line.startswith(")"):
        in_table = False
        all_tables.append((current_table, current_fields))

with open("../docs/api.apib", "a") as api_file:
    api_file.write("## Data Structures\n\n")

    for table in all_tables:
        api_file.write("### {}\n\n".format(table[0].upper()))
        for field in table[1]:
            if "PRIMARY KEY" in field[2]:
                continue
            api_file.write("+ {} ({}".format(field[0], field[1]))
            if "NOT NULL" in field[2]:
                api_file.write(", required")
            if "DEFAULT" in field[2]:
                api_file.write(", optional)\n    + Default: {}\n".format(field[2].split("DEFAULT ")[1].lower().strip(",")))
                continue
            api_file.write(")\n")
        api_file.write("\n\n")
