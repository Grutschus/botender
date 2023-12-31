import pandas as pd
import random

class DrinkRecommender:
    def __init__(self, dataset_path):
        self.drinks_data = pd.read_csv(dataset_path)

    def recommend_drink(self, emotion, taste_preference):
        emotion_categories = {
            'happy': ['Sweet', 'Sour', 'Milk-based'],
            'sad': ['Sweet', 'Milk-based'],
            'angry': ['Sour', 'Strong'],
            'neutral': ['Sweet', 'Sour', 'Milk-based','Strong']
        }

        # Filter for the relevant categories based on emotion
        relevant_categories = emotion_categories.get(emotion.lower(), [])
        filtered_drinks = self.drinks_data[self.drinks_data['Category_with_Scales'].str.contains('|'.join(relevant_categories))]

        # Further filter based on taste preference
        taste_filtered_drinks = filtered_drinks[filtered_drinks['Category_with_Scales'].str.contains(taste_preference)]

        # Sort by the score of the taste preference
        taste_filtered_drinks['Score'] = taste_filtered_drinks['Category_with_Scales'].apply(
            lambda x: int(x.split(f'{taste_preference}(')[-1].split(')')[0]) if f'{taste_preference}(' in x else 0
        )
        top_drinks = taste_filtered_drinks.sort_values(by='Score', ascending=False).head(10)

        # Randomly select one from the top 10
        selected_drink = top_drinks.sample(n=1)

        return selected_drink[['Cocktail', 'Ingredients', 'Category_with_Scales']]
