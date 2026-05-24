import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
import pickle
from typing import Optional, List
from deep_translator import GoogleTranslator

class BookRecommender:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.tfidf_matrix = None
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=50000,
            ngram_range=(1, 2)
        )
        self.load_and_clean_data()

    def clean_text(self, text) -> str:
        if not isinstance(text, str):
            return ""
        # Remove special characters and numbers, keep spaces
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = text.lower().strip()
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text

    def load_and_clean_data(self):
        if not os.path.exists(self.csv_path):
            print(f"[ERROR] Data file not found at: {self.csv_path}")
            return

        cache_file = self.csv_path.replace('.csv', '_cache.pkl')
        if os.path.exists(cache_file):
            print(f"[INFO] Loading cached TF-IDF from: {cache_file}")
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    self.df = cached_data['df']
                    self.tfidf_matrix = cached_data['matrix']
                    self.vectorizer = cached_data['vectorizer']
                print("[INFO] Cache loaded successfully.")
                return
            except Exception as e:
                print(f"[WARNING] Failed to load cache: {e}. Rebuilding from raw CSV...")

        print(f"[INFO] Loading dataset from: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)

        # Ensure required columns exist
        required_cols = ['Book', 'Author', 'Description', 'Genres', 'Avg_Rating', 'URL', 'Image_URL']
        for col in required_cols:
            if col not in self.df.columns:
                print(f"[WARNING] Column '{col}' not found in dataset.")
                self.df[col] = ''

        # Fill missing values
        self.df['Description'] = self.df['Description'].fillna('')
        self.df['Book'] = self.df['Book'].fillna('Unknown Title')
        self.df['Author'] = self.df['Author'].fillna('Unknown Author')
        self.df['Genres'] = self.df['Genres'].fillna('')
        self.df['Avg_Rating'] = pd.to_numeric(self.df['Avg_Rating'], errors='coerce').fillna(0.0)
        self.df['URL'] = self.df['URL'].fillna('#')
        self.df['Image_URL'] = self.df['Image_URL'].fillna('')

        # Clean the description for recommendation
        self.df['cleaned_description'] = self.df['Description'].apply(self.clean_text)

        # Combine Book title, Author and Genres into the content for better matching
        self.df['content'] = (
            self.df['cleaned_description'] + " " +
            self.df['Book'].apply(self.clean_text) + " " +
            self.df['Author'].apply(self.clean_text) + " " +
            self.df['Genres'].apply(lambda x: self.clean_text(str(x)))
        )

        # Fit and transform the TF-IDF matrix
        print(f"[INFO] Building TF-IDF matrix for {len(self.df)} books...")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['content'])
        print(f"[INFO] Done! TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        print(f"[INFO] Saving TF-IDF cache to: {cache_file}")
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'df': self.df,
                'matrix': self.tfidf_matrix,
                'vectorizer': self.vectorizer
            }, f)

    def recommend(
        self,
        description: str,
        top_n: int = 5,
        genre_filter: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> List[dict]:
        if self.df is None or self.tfidf_matrix is None:
            return []

        # Start with the full index set
        working_df = self.df
        working_matrix = self.tfidf_matrix

        # Apply genre filter
        if genre_filter:
            genre_lower = genre_filter.lower()
            mask = self.df['Genres'].apply(lambda g: genre_lower in str(g).lower())
            if mask.any():
                working_df = self.df[mask].reset_index(drop=True)
                working_matrix = self.tfidf_matrix[mask.values]
            else:
                return []

        # Apply rating filter
        if min_rating is not None:
            rating_mask = working_df['Avg_Rating'] >= min_rating
            if rating_mask.any():
                working_matrix = working_matrix[rating_mask.values]
                working_df = working_df[rating_mask].reset_index(drop=True)
            else:
                return []

        if len(working_df) == 0:
            return []

        # Auto-translate Vietnamese (or any language) to English
        if description and description.strip():
            try:
                print(f"[INFO] Translating query: '{description}'")
                description = GoogleTranslator(source='auto', target='en').translate(description)
                print(f"[INFO] Translated to: '{description}'")
            except Exception as e:
                print(f"[WARNING] Translation failed: {e}")

        # Clean the input description
        cleaned_input = self.clean_text(description)

        if not cleaned_input:
            # If no description, just sort by rating
            sorted_df = working_df.sort_values(by='Avg_Rating', ascending=False)
            actual_top_n = min(top_n, len(sorted_df))
            recommendations = []
            for i in range(actual_top_n):
                book = sorted_df.iloc[i]
                desc = str(book['Description'])
                short_desc = desc[:300] + "..." if len(desc) > 300 else desc
                genres_raw = str(book['Genres'])
                genres_list = [g.strip() for g in genres_raw.split(',') if g.strip() and g.strip() != 'nan']
                recommendations.append({
                    "title": str(book['Book']),
                    "author": str(book['Author']),
                    "description": short_desc,
                    "genres": genres_list,
                    "rating": round(float(book['Avg_Rating']), 2),
                    "url": str(book['URL']),
                    "image_url": str(book['Image_URL']),
                    "score": 1.0
                })
            return recommendations

        # Vectorize the input using the already-fitted vectorizer
        input_vector = self.vectorizer.transform([cleaned_input])

        # Calculate cosine similarity
        similarity_scores = cosine_similarity(input_vector, working_matrix).flatten()

        # Get indices of top_n matches
        actual_top_n = min(top_n, len(working_df))
        top_indices = similarity_scores.argsort()[-actual_top_n:][::-1]
        
        # Filter out books with 0 similarity score
        top_indices = [idx for idx in top_indices if similarity_scores[idx] > 0.0]

        # Build the result list
        recommendations = []
        for idx in top_indices:
            book = working_df.iloc[idx]
            desc = str(book['Description'])
            short_desc = desc[:300] + "..." if len(desc) > 300 else desc

            genres_raw = str(book['Genres'])
            genres_list = [g.strip() for g in genres_raw.split(',') if g.strip() and g.strip() != 'nan']

            recommendations.append({
                "title": str(book['Book']),
                "author": str(book['Author']),
                "description": short_desc,
                "genres": genres_list,
                "rating": round(float(book['Avg_Rating']), 2),
                "url": str(book['URL']),
                "image_url": str(book['Image_URL']),
                "score": round(float(similarity_scores[idx]), 4)
            })

        return recommendations

    def get_genres(self) -> List[str]:
        """Returns a sorted list of unique genres from the dataset."""
        if self.df is None:
            return []

        genre_set = set()
        for genres_str in self.df['Genres'].dropna():
            for g in str(genres_str).split(','):
                g = g.strip()
                if g and g.lower() != 'nan' and len(g) > 1:
                    genre_set.add(g)

        return sorted(list(genre_set))[:100]  # Return top 100 unique genres


# Initialize the recommender with the correct relative path
_dir = os.path.dirname(os.path.abspath(__file__))
_data_path = os.path.join(_dir, '..', 'data', 'goodreads_data.csv')
recommender = BookRecommender(_data_path)
