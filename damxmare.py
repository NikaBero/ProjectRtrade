import requests


def get_recipe_instructions(ingredients):
    ingredient_list = ','.join(ingredients)
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients=" \
          f"{ingredient_list}&apiKey=24c129d8c433448687386ef82dd0de20"
    response = requests.get(url)
    data = response.json()

    recipe_instructions = []

    for recipe in data:
        if 'id' in recipe and 'title' in recipe:
            recipe_id = recipe['id']
            recipe_title = recipe['title']

            recipe_url = f"https://api.spoonacular.com/recipes/" \
                         f"{recipe_id}/analyzedInstructions?apiKey=24c129d8c433448687386ef82dd0de20"
            recipe_response = requests.get(recipe_url)
            recipe_data = recipe_response.json()

            if isinstance(recipe_data, list) and recipe_data:
                steps = [step['step'] for step in recipe_data[0]['steps']]
                recipe_instructions.append({'title': recipe_title, 'instructions': steps})

    return recipe_instructions


user_input = input("Enter the ingredients (comma-separated): ")
ingredients = [ingredient.strip() for ingredient in user_input.split(',') if ingredient.strip()]


if not ingredients:
    print("No ingredients provided.")
    exit()


instructions = get_recipe_instructions(ingredients)


if not instructions:
    print("No instructions found for the given ingredients.")
    exit()


for recipe in instructions:
    print(f"Recipe: {recipe['title']}")
    print("Instructions:")
    for i, step in enumerate(recipe['instructions'], 1):
        print(f"{i}. {step}")
    print()
