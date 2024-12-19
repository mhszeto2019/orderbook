from util import with_db_connection

@with_db_connection
def register(cursor):
    # user input username and password
    # username = request.form.get('username')
    # password = request.form.get('password')

    # Execute SELECT query to check for existing users
    cursor.execute("SELECT * FROM users WHERE username = %s", ('brennan',))
    x = cursor.fetchall()
    print(x)

register()