""" This script initialises the database and creates the first admin user.
"""

import MySQLdb
import imp
import getpass
import sys

from passlib.hash import pbkdf2_sha256

# CONFIGURE

config = imp.load_source('config', './app.conf')

db = MySQLdb.connect(user=config.MYSQL_USER,
                     passwd=config.MYSQL_PASSWORD)

cursor = db.cursor()


# INITIALISE THE DATABASE

SCHEMA_PATH= './resources/schema.sql'

def make_database(database_name):
    """Creates a codestroke database with database_name."""

    with open(SCHEMA_PATH) as schema_file:
        schema_queries = filter(lambda x: not (x == ''),
                                ' '.join(schema_file.read()\
                                            .replace('[DATABASE_NAME]',
                                                    database_name)\
                                            .splitlines())\
                                .split(';'))
    for query in schema_queries:
        cursor.execute(query)

    db.commit()

# initialise a database for running tests
make_database("test_codestroke")

# then create the proper database
make_database(config.DATABASE_NAME)


# PROMPT FOR FIRST ADMIN USER

check_query = 'select * from admins'
cursor.execute(check_query)
result = cursor.fetchall()

if len(result) > 0:
    sys.exit('Admin user already created.')

print('\nYou will now create the first administrator.\n\n')

admin_first = input('\nEnter your first name:  ')
admin_last = input('\nEnter your last name:  ')
admin_email = input('\nEnter your email address:  ')
admin_username = input('\nEnter the administrator username:  ')
admin_password = getpass.getpass(prompt='\nEnter the administrator password:  ')

admin_pwhash = pbkdf2_sha256.hash(admin_password)

admin_query = 'insert into admins (first_name, last_name, username, pwhash, email) values (%s, %s, %s, %s, %s)'

cursor.execute(admin_query, (admin_first,
                       admin_last,
                       admin_username,
                       admin_pwhash,
                       admin_email))

db.commit()

print('\n')
