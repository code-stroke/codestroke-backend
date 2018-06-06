"""
This script will generate users (e.g. clin0001) with password hashes to be stored
in the codestroke database. This script REQUIRES that the database has been created
using the corresponding app.py route. 

For v1, the usernames and passwords are ALSO exported to a file so that they can be 
distributed to users. This is FOR TESTING ONLY and IS NOT SECURE.
"""

import MySQLdb, os, getpass, math, random, itertools, datetime
import sys
from passlib.hash import pbkdf2_sha256

options_file = input('''\nSpecify the path to your options file containing random words to select from for passwords.
Consult the Diceware or EFF word lists. The file should be plain text, one word per line\n\n''')
master_file = input('''\nNow specify the path to the output master file containing usernames and passwords.
FOR INITIAL DISTRIBUTION OF USERNAMES AND PASSWORDS TO USERS ONLY.
This is NOT a safe file and should be used for TESTING ONLY.\n\n''')

# Access codestroke database
dbpasswd = getpass.getpass('DB Password: ')
try:
    db = MySQLdb.connect(host='localhost',
                         user='root',
                         passwd=dbpasswd,
                         db='codestroke')
except:
    print('ERROR')
    print('Make sure you have created the codestroke database from the main script in app.py:')
    print('Run `python app.py` in the main directory, then head to localhost:5000/create_db')
    print(sys.exc_info())

cursor = db.cursor()

def gen_options(infile):
    # Generate list of password random word options from input file
    # File should be simple list, one word on each new line
    with open(infile) as words:
        pw_options = words.read().splitlines()
    return pw_options

# User generation functions
def gen_users(prefix, n, options_file, master_file):
    # Generate list of dictionaries containing username and pwhash keys
    # n users are generated with username in format `prefixXXXX`
    # Also exports a master list for distribution of usernames and passwords (v1 ONLY!)
    
    num_digits = int(math.log(n, 10)) + 1
    # Max 9 digits here, definitely enough for real life. 
    format_str = '{:0' + str(num_digits) + 'd}'

    pw_options = gen_options(options_file)
    
    master = []
    user_list = []
    
    for i in range(0, n):
        pw = '_'.join(random.sample(pw_options, 2))
        username = prefix + format_str.format(i)
        pwhash = pbkdf2_sha256.hash(pw)
        
        user_info = {}
        user_info['username'] = username
        user_info['pwhash'] = pwhash

        master_entry = username + '\t' + pw
        
        user_list.append(user_info)
        master.append(master_entry)

    return (master, user_list)
        
# Run script
(paras_master, paras_db) = gen_users('para', 100, options_file, master_file)
(clins_master, clins_db) = gen_users('clin', 100, options_file, master_file)

for user in itertools.chain(paras_db, clins_db):
    # placeholders for now as these are required fields, probably require change on first login
    first_name = 'FirstName' 
    last_name = 'LastName'
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    username = user['username']
    pwhash = user['pwhash']
    insert_query = '''insert into clinicians (first_name, last_name, 
                      username, pwhash, creation_date, linked)
                      values (%s, %s, %s, %s, %s, %s)'''
    insert_args = (first_name, last_name, username, pwhash, date, '0')
    cursor.execute(insert_query, insert_args)

db.commit()

cursor.close()
db.close()

paras_text = '\n'.join(paras_master)
clins_text = '\n'.join(clins_master)
users_text = paras_text + '\n' + clins_text
with open(master_file, 'w') as f:
    f.write(users_text)



