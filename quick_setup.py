""" This script initialises the database and creates the first admin user.
"""

import MySQLdb
import imp
import getpass
import sys

from passlib.hash import pbkdf2_sha256

# CONFIGURE

config = imp.load_source("config", "./app.conf")

db = MySQLdb.connect(user=config.MYSQL_USER, passwd=config.MYSQL_PASSWORD)

cursor = db.cursor()


# INITIALISE THE DATABASE

SCHEMA_PATH = "./resources/schema.sql"


def make_database(database_name):
    """Creates a codestroke database with database_name."""

    with open(SCHEMA_PATH) as schema_file:
        schema_queries = filter(
            lambda x: not (x == ""),
            " ".join(
                schema_file.read()
                .replace("[DATABASE_NAME]", database_name)
                .splitlines()
            ).split(";"),
        )
    for query in schema_queries:
        cursor.execute(query)

    db.commit()


# Convenience function


def drop_database(database_name):
    """ Drops a codestroke database with database_name."""

    cursor.execute("drop database {}".format(database_name))
    db.commit()


# Add admin user


def check_admin(database_name):
    """ Checks whether an admin user is already created."""
    check_query = "select * from admins"
    cursor.execute(check_query)
    result = cursor.fetchall()

    if len(result) > 0:
        sys.exit("Admin user already created.")


def add_admin(database_name, admin_info):
    """ Adds an admin to the specified database.

    Args:
        database_name: name of the database to add to
        admin_info: list of [first_name, last_name, username, password, email]
    """

    check_admin(database_name)

    admin_pwhash = pbkdf2_sha256.hash(admin_info[3])

    admin_info[3] = admin_pwhash

    admin_query = "insert into admins (first_name, last_name, username, pwhash, email) values (%s, %s, %s, %s, %s)"

    cursor.execute("use {}".format(database_name))
    cursor.execute(admin_query, admin_info)

    db.commit()


# only run if called directly
if __name__ == "__main__":

    # then create the proper database
    make_database(config.DATABASE_NAME)

    # and add an admin

    check_admin(config.DATABASE_NAME)

    print("\nYou will now create the first administrator.\n\n")

    admin_first = input("Enter your first name:  ")
    admin_last = input("Enter your last name:  ")
    admin_email = input("Enter your email address:  ")
    admin_username = input("Enter the administrator username:  ")
    admin_password = getpass.getpass(prompt="Enter the administrator password:  ")

    admin_info = [admin_first, admin_last, admin_username, admin_password, admin_email]

    add_admin(config.DATABASE_NAME, admin_info)

    print("\nThe setup is now complete.\n")
