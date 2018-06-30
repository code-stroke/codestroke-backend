import MySQLdb, os, getpass, math, random, itertools, string
import sys
from passlib.hash import pbkdf2_sha256

master_file = input('''\nSpecify the path to the output master file containing usernames and passwords.
FOR INITIAL DISTRIBUTION OF USERNAMES AND PASSWORDS TO USERS ONLY.
This is NOT a safe file and should be used for TESTING ONLY.\n''')

host = input('\nInput host:\n')
user = input('\nUser:\n')
dbpasswd = getpass.getpass('\nDB Password: ')
try:
    db = MySQLdb.connect(host=host,
                         user=user,
                         passwd=dbpasswd,
                         db='codestroke$codestroke')
except:
    print('ERROR')
    print('Make sure you have created the codestroke database from the main script in app.py:')
    print('Run `python app.py` in the main directory, then head to localhost:5000/create_db')
    print(sys.exc_info())

cursor = db.cursor()

# User generation functions
def gen_users(prefix, role, n):
    # Generate list of dictionaries containing username and pwhash keys
    # n users are generated with username in format `prefixXXXX`
    # Also exports a master list for distribution of usernames and passwords (v1 ONLY!)
    
    num_digits = int(math.log(n, 10)) + 1
    # Max 9 digits here, definitely enough for real life. 
    format_str = '{:0' + str(num_digits) + 'd}'

    master = []
    user_list = []
    
    for i in range(0, n):
        pw = ''.join(random.choice(string.digits) for x in range(4))
        username = prefix + format_str.format(i)
        pwhash = pbkdf2_sha256.hash(pw)
        
        user_info = {}
        user_info['username'] = username
        user_info['pwhash'] = pwhash
        user_info['role'] = role

        master_entry = username + '\t' + pw
        
        user_list.append(user_info)
        master.append(master_entry)

    return (master, user_list)
        
# Run script
user_types = ['paramedic', 'ed_clinician', 'radiographer', 'stroke_team', 'radiologist', 'stroke_ward', 'neuroint', 'angio_nurse', 'anaesthetist']
users = []
users_master = []
for user_type in user_types:
    master, users_db = gen_users(user_type, user_type, 10)
    users_master.extend(master)
    users.extend(users_db)

for user in users:
    # placeholders for now as these are required fields, probably require change on first login
    username = user['username']
    pwhash = user['pwhash']
    role = user['role']
    insert_query = '''insert into clinicians (username, pwhash, role) 
                      values (%s, %s, %s)'''
    insert_args = (username, pwhash, role)
    cursor.execute(insert_query, insert_args)

db.commit()

cursor.close()
db.close()

users_text = '\n'.join(users_master)
with open(master_file, 'w') as f:
    f.write(users_text)



