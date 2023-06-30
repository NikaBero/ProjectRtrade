import sqlite3
from flask import g


DATABASE = 'userdata.db'



def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def init_db():
    db = get_db()
    with open('schema.sql', 'r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print('Database initialized.')


def close_db():
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



def create_tables():
    conn = sqlite3.connect('userdata.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS comments
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 recipe_id INTEGER,
                                 comment TEXT,
                                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                  username TEXT,

                                 FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id))''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS salad
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          recipe_name TEXT,
                          recipe_description TEXT,
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                          user_name TEXT)''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS cake
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          recipe_name TEXT,
                          recipe_description TEXT,
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                          user_name TEXT)''')

    c.execute(f'''CREATE TABLE IF NOT EXISTS pizza
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          recipe_name TEXT,
                          recipe_description TEXT,
                          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                          user_name TEXT)''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS API 
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              ingredients TEXT, 
              response TEXT, 
              username TEXT, 
              datetime DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    c.close()

# create_tables()

# თეიბლების წაშლა მონაცემთა ბაზაში

def tableebis_washla(cvladi):
    conn = sqlite3.connect('userdata.db')
    c = conn.cursor()
    if cvladi is None:
        c.execute("drop table users")
        c.execute("drop table salad")
        c.execute("drop table pizza")
        c.execute("drop table cake")
        c.execute("drop table sqlite_sequence")
        c.execute("drop table users_recipes")

    else:
        c.execute(f"drop table {cvladi}")

    conn.commit()
    c.close


# tableebis_washla()



# მონაცემების გასუფთავება მონაცემთა ბაზაში

def clear_database():
    conn = sqlite3.connect('userdata.db')
    c = conn.cursor()
    c.execute("delete from users")
    c.execute("delete from salad")
    c.execute("delete from pizza")
    c.execute("delete from cake")
    c.execute("delete from sqlite_sequence")
    c.execute("delete from users_recipes")
    c.execute("delete from comments")
    conn.commit()
    conn.close()



# clear_database()

conn = sqlite3.connect('userdata.db')
c = conn.cursor()

c.execute("delete from API ")
conn.commit()
c.close()