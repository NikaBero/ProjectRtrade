import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, g, flash
import hashlib
import openai
import requests
import json




app = Flask(__name__)
app.secret_key = 'HelloBTU'
DATABASE = 'userdata.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def home():
    if 'username' in session:
        notification = session.pop('notification', None)
        return render_template('index.html', username=session['username'], notification=notification)
    else:
        return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        c = db.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = c.fetchone()
        if existing_user:
            return render_template('register.html', error='Username already exists. Please choose a different username.')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        db.commit()

        session['username'] = username
        return redirect('/')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        c = db.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user:
            stored_password = user[2]

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == stored_password:
                session['username'] = username
                return redirect('/')

        return render_template('login.html', error='Invalid username or password.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')




@app.route('/recipe/<category>')
def recipe(category):
    if 'username' in session:
        db = get_db()
        c = db.cursor()

        c.execute(f"SELECT * FROM {category}")
        recipes_data = c.fetchall()

        recipe_comments = {}
        for recipe in recipes_data:
            recipe_id = recipe[0]
            c.execute("SELECT * FROM comments WHERE recipe_id=?", (recipe_id,))
            comments = c.fetchall()
            recipe_comments[recipe_id] = comments

        recipe_categories = {category: recipes_data}

        return render_template('recipe.html', recipe_categories=recipe_categories, recipe_comments=recipe_comments)
    else:
        return redirect('/login')


@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        category = request.form['category']
        recipe_name = request.form['recipe_name']
        recipe_description = request.form['recipe_description']
        user_name = session['username']
        db = get_db()
        c = db.cursor()

        if category not in ['salad', 'pizza', 'cake']:
            return redirect('/')

        table_name = category

        c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      recipe_name TEXT,
                      recipe_description TEXT,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                      user_name TEXT)''')


        c.execute(f"INSERT INTO {table_name} (recipe_name, recipe_description, user_name) VALUES (?, ?, ?)",
                  (recipe_name, recipe_description, user_name))


        c.execute(f"SELECT * FROM {table_name} WHERE recipe_name=? AND recipe_description=? AND user_name=?",
                  (recipe_name, recipe_description, user_name))
        recipe = c.fetchone()

        if recipe:
            recipe_id = recipe[0]


            c.execute(f"INSERT INTO users_recipes (recipe_name, recipe_description, user_name, recipe_id) VALUES (?, ?, ?, ?)",
                      (recipe_name, recipe_description, user_name, recipe_id))
            db.commit()
            flash('New recipe added', 'success')
            return redirect('/')

    return render_template('add_recipe.html')



@app.route('/my_recipes')
def my_recipes():
    if 'username' in session:
        user_name = session['username']
        db = get_db()
        c = db.cursor()

        c.execute("SELECT * FROM users_recipes WHERE user_name=?", (user_name,))
        recipes = c.fetchall()

        return render_template('my_recipes.html', recipes=recipes)
    else:
        return redirect('/login')


@app.route('/delete_recipe', methods=['POST'])
def delete_recipe():
    recipe_id = request.form['recipe_id']

    db = get_db()
    c = db.cursor()


    c.execute("SELECT * FROM users_recipes WHERE id=?", (recipe_id,))
    recipe = c.fetchone()

    if recipe:
        recipe_name = recipe[1]
        recipe_description = recipe[2]
        created_at = recipe[3]
        recipe_aidi = recipe[5]

        c.execute("DELETE FROM users_recipes WHERE id=? and recipe_description=? and created_at=?",
                  (recipe_id, recipe_description, created_at))

        c.execute("DELETE FROM comments WHERE recipe_id=?", (recipe_aidi,))

        c.execute("DELETE FROM cake WHERE recipe_name=? AND recipe_description=? AND created_at=?",
                  (recipe_name, recipe_description, created_at))
        c.execute("DELETE FROM salad WHERE recipe_name=? AND recipe_description=? AND created_at=?",
                  (recipe_name, recipe_description, created_at))

        c.execute("DELETE FROM pizza WHERE recipe_name=? AND recipe_description=? AND created_at=?",
                  (recipe_name, recipe_description, created_at))

        db.commit()
        flash("Recipe deleted successfully.", 'success')
    else:
        flash("Recipe not found.", 'error')

    return redirect('/my_recipes')



@app.route('/add_comment', methods=['POST'])
def add_comment():
    recipe_id = request.form['recipe_id']
    comment = request.form['comment']
    username = session['username']
    if 'username' in session:
        db = get_db()
        c = db.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS comments
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             recipe_id INTEGER,
                             comment TEXT,
                             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                             username TEXT,
                             FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id))''')

        c.execute("INSERT INTO comments (recipe_id, comment, username) VALUES (?, ?, ?)", (recipe_id, comment, username))

        db.commit()

    flash("Comment uploaded successfully.", 'success')


    referring_url = request.referrer


    return redirect(referring_url or url_for('index'))


@app.route('/delete_comment', methods=['POST'])
def comment_delete():
    if 'username' in session:
        comment_id = request.form['comment_id']
        username = session['username']

        db = get_db()
        c = db.cursor()


        c.execute("SELECT username FROM comments WHERE id = ?", (comment_id,))
        result = c.fetchone()
        if result and result[0] == username:
            c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            db.commit()
            flash('Comment deleted successfully.', 'success')
        else:
            flash('You are not authorized to delete this comment.', 'error')
    else:
        flash('You must be logged in to delete a comment.', 'error')

    return redirect(request.referrer)


def initialize_database():
    with app.app_context():
        conn = get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS API 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ingredients TEXT, 
                      response TEXT,
                      username TEXT, 
                      datetime DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()

@app.route('/api_recipe', methods=['GET', 'POST'])
def api_recipe():
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        username = session.get('username')

        if not ingredients:
            return redirect('/api_recipe')

        ingredients_list = [ingredient.strip() for ingredient in ingredients.split('\n')]
        ingredients_text = ', '.join(ingredients_list)

        conn = get_db()
        c = conn.cursor()


        save_recipe_to_database(ingredients_text, username)
        last_ingredients = ingredients_list[-1]
        instructions = get_recipe_instructions(last_ingredients)
        save_response_to_database(instructions, username)

    saved_data = get_saved_data()
    saved_ingredients = saved_data['ingredients']
    api_response = saved_data['response']


    recipe_data = get_recipe_data()
    recipe_titles = [recipe['title'] for recipe in recipe_data[:10]]
    recipe_ingredients = [recipe['ingredients'] for recipe in recipe_data[:10]]


    zipped_data = zip(recipe_titles, recipe_ingredients)

    return render_template('api_recipe.html', ingredients=saved_ingredients, api_response=api_response,
                           zipped_data=zipped_data)


def save_recipe_to_database(ingredients, username):
    conn = get_db()
    c = conn.cursor()
    datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    recipe_instructions = get_recipe_instructions(ingredients)

    if not recipe_instructions:
        print("No recipe instructions found for the given ingredients.")
        return


    instructions_json = json.dumps(recipe_instructions)

    c.execute('INSERT INTO API (ingredients, username, datetime, response) VALUES (?, ?, ?, ?)',
              (ingredients, username, datetime_str, instructions_json))
    conn.commit()

def get_recipe_data():
    try:
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": "chicken",
            "apiKey": "09f8b3a6ae57412980877383533ed917"
        }
        response = requests.get(url, params=params)
        data = response.json()

        recipe_data = []

        if isinstance(data, list):
            for recipe in data:
                if isinstance(recipe, dict) and 'id' in recipe and 'title' in recipe:
                    recipe_id = recipe['id']
                    recipe_title = recipe['title']

                    recipe_url = f"https://api.spoonacular.com/recipes/{recipe_id}/ingredientWidget.json"
                    recipe_params = {
                        "apiKey": "09f8b3a6ae57412980877383533ed917"
                    }
                    recipe_response = requests.get(recipe_url, params=recipe_params)
                    recipe_data_dict = recipe_response.json()

                    if isinstance(recipe_data_dict, dict) and 'ingredients' in recipe_data_dict:
                        ingredients = recipe_data_dict['ingredients']
                        recipe_data.append({'title': recipe_title, 'ingredients': ingredients})

        return recipe_data[:10]

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the Spoonacular API: {e}")

    return []



def save_response_to_database(response, username):
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE API SET response = ? WHERE id = (SELECT MAX(id) FROM API) AND username = ?',
              (json.dumps(response), username))
    conn.commit()

def get_saved_data():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT ingredients, response FROM API WHERE username = ? ORDER BY id DESC LIMIT 1',
              (session.get('username'),))
    data = c.fetchone()
    if data:
        ingredients = data[0]
        response = json.loads(data[1])
        return {'ingredients': ingredients, 'response': response}
    else:
        return {'ingredients': None, 'response': None}


def get_recipe_instructions(ingredients):
    try:
        url = f"https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            "ingredients": ingredients,
            "apiKey": "09f8b3a6ae57412980877383533ed917"
        }
        response = requests.get(url, params=params)
        data = response.json()

        recipe_instructions = []

        if isinstance(data, list):
            for recipe in data:
                if isinstance(recipe, dict) and 'id' in recipe and 'title' in recipe:
                    recipe_id = recipe['id']
                    recipe_title = recipe['title']

                    recipe_url = f"https://api.spoonacular.com/recipes/{recipe_id}/analyzedInstructions"
                    recipe_params = {
                        "apiKey": "09f8b3a6ae57412980877383533ed917"
                    }
                    recipe_response = requests.get(recipe_url, params=recipe_params)
                    recipe_data = recipe_response.json()

                    if isinstance(recipe_data, list) and len(recipe_data) > 0:
                        instructions = [step['step'] for step in recipe_data[0]['steps']]
                        recipe_instructions.append({'title': recipe_title, 'instructions': instructions})

        if recipe_instructions:
            for recipe in recipe_instructions:
                print("Title: ", recipe['title'])
                for i, instruction in enumerate(recipe['instructions'], 1):
                    print(f"{i}. {instruction}")

            return recipe_instructions

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the Spoonacular API: {e}")

    return "No Recipe Found"


if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)

