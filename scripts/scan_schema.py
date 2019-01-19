""" Script to scan the schema file.

One-off script to scan and generate text for the API blueprint.

"""

import re
import imp

config = imp.load_source('config', '../app.conf')

# SCHEMA PARSING

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
            groups = re.search(r"`(.*?)`\s(.*?(\(.*\))?)\s(.*)", line)
            current_fields.append([groups[1], groups[2], groups[4]])
    elif line.startswith(")"):
        in_table = False
        all_tables.append((current_table, current_fields))

# API Definitions generation

with open("../resources/api_doc_template.yaml") as infile:
    main_template = infile.read()

main_template = main_template.replace("$VERSION", config.VERSION).replace("$HOST", config.BACKEND_DOMAIN)

main_template += "\n"

for table in all_tables:

    for table_type in ["POST", "GET"]:
        main_template += "  " + table[0].upper() + "_" + table_type + ":\n"
        main_template += "    type: 'object'\n"

        required = []
        field_strings = []

        for field in table[1]:

            if table_type == "POST":
                if "PRIMARY KEY" in field[2]:
                    continue
                elif any(x in field[0] for x in ["eta", "incoming_timestamp", "active_timestamp", "completed_timestamp"] ):
                    continue
                elif table[0].startswith("case") and field[0] == "case_id":
                    continue
                elif table[0] == "clinicians" and field[0] == "id":
                    continue

            if "NOT NULL" in field[2]:
                required.append(field[0])

            field_template = "      {}:\n        type: '{}'\n"

            if 'varchar' in field[1] or "text" in field[1] or "decimal" in field[1]:
                field[1] = "string"
            elif field[1] == "int" or field[1] == "tinyint":
                field[1] = "integer"
            elif field[1] == "float":
                field[1] = "number"
            elif field[1] == "bool":
                field[1] = "boolean"
            elif field[1] == 'timestamp':
                field[1] = "string"
                field_template += "        format: 'date-time'\n"
            elif field[1] == 'date':
                field[1] = "string"
                field_template += "        format: 'date'\n"
            elif "enum" in field[1]:
                choices = re.findall(r"'(.*?)'", field[1])
                field[1] = "string"
                field_template += """        enum: {}\n""".format(str(choices))

            field_strings.append(field_template.format(field[0], field[1]))

        if len(required) > 0:
            main_template += "    required:\n"
            required_str = ["      - {}".format(f) for f in required]
            main_template += "\n".join(required_str)
            main_template += "\n"

        main_template += "    properties:\n"
        for field_string in field_strings:
            main_template += field_string

with open("../docs/api.yaml", "w+") as outfile:
    outfile.write(main_template)
