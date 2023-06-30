from database import get_db


class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get_user_by_username(username):
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = c.fetchone()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None


class Recipe:
    def __init__(self, id, category, name, user_id):
        self.id = id
        self.category = category
        self.name = name
        self.user_id = user_id

    @staticmethod
    def get_recipes_by_category(category):
        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM recipes WHERE category=?", (category,))
        recipes_data = c.fetchall()
        recipes = []
        for recipe_data in recipes_data:
            recipes.append(Recipe(recipe_data[0], recipe_data[1], recipe_data[2], recipe_data[3]))
        return recipes