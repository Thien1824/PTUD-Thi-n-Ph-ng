import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
import pickle
import unicodedata
from typing import Optional, List
from deep_translator import GoogleTranslator

def remove_vietnamese_accents(text: str) -> str:
    if not isinstance(text, str):
        return ""
    # Normalize unicode to decompose characters
    nfkd_form = unicodedata.normalize('NFKD', text)
    # Filter out diacritics
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Replace manually Đ/đ
    only_ascii = only_ascii.replace('đ', 'd').replace('Đ', 'D')
    return only_ascii


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

    def load_and_clean_data(self, force_rebuild=False):
        if not os.path.exists(self.csv_path):
            print(f"[ERROR] Data file not found at: {self.csv_path}")
            return

        cache_file = self.csv_path.replace('.csv', '_cache.pkl')
        cache_valid = False
        if not force_rebuild and os.path.exists(cache_file):
            cache_valid = True
            if os.path.exists(self.csv_path):
                csv_mtime = os.path.getmtime(self.csv_path)
                cache_mtime = os.path.getmtime(cache_file)
                if csv_mtime > cache_mtime:
                    print(f"[INFO] CSV file ({self.csv_path}) is newer than cache ({cache_file}). Rebuilding cache...")
                    cache_valid = False

        if cache_valid:
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

        # Gộp thêm sách đã được duyệt từ Database
        self._load_approved_from_db()

        # Fit and transform the TF-IDF matrix
        print(f"[INFO] Building TF-IDF matrix for {len(self.df)} books...")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['content'])
        print(f"[INFO] Done! TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        
        print(f"[INFO] Saving TF-IDF cache to: {cache_file}")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'df': self.df,
                    'matrix': self.tfidf_matrix,
                    'vectorizer': self.vectorizer
                }, f)
        except Exception as e:
            print(f"[WARNING] Could not save TF-IDF cache: {e}")

    def _load_approved_from_db(self):
        """Load sách đã được duyệt từ database và gộp vào self.df"""
        try:
            from database import SessionLocal, UploadedBook
            db = SessionLocal()
            try:
                custom_books = db.query(UploadedBook).filter(
                    UploadedBook.status == 'approved'
                ).all()
                if custom_books:
                    custom_data = [{
                        'Book': b.title,
                        'Author': b.author,
                        'Description': b.description or '',
                        'Genres': b.genres or '',
                        'Avg_Rating': b.avg_rating or 0.0,
                        'URL': b.url or '#',
                        'Image_URL': b.image_url or ''
                    } for b in custom_books]
                    custom_df = pd.DataFrame(custom_data)
                    # Áp dụng tiền xử lý giống mắc định
                    custom_df['Description'] = custom_df['Description'].fillna('')
                    custom_df['Book'] = custom_df['Book'].fillna('Unknown Title')
                    custom_df['Author'] = custom_df['Author'].fillna('Unknown Author')
                    custom_df['Genres'] = custom_df['Genres'].fillna('')
                    custom_df['Avg_Rating'] = pd.to_numeric(custom_df['Avg_Rating'], errors='coerce').fillna(0.0)
                    custom_df['cleaned_description'] = custom_df['Description'].apply(self.clean_text)
                    custom_df['content'] = (
                        custom_df['cleaned_description'] + " " +
                        custom_df['Book'].apply(self.clean_text) + " " +
                        custom_df['Author'].apply(self.clean_text) + " " +
                        custom_df['Genres'].apply(lambda x: self.clean_text(str(x)))
                    )
                    # Lọc những sách trong custom_df chưa tồn tại trong self.df để tránh bị trùng, nhưng không lọc bỏ trùng lặp vốn có của CSV gốc
                    existing_books = set(zip(self.df['Book'].str.lower().str.strip(), self.df['Author'].str.lower().str.strip()))
                    custom_df['is_duplicate'] = custom_df.apply(
                        lambda r: (str(r['Book']).lower().strip(), str(r['Author']).lower().strip()) in existing_books,
                        axis=1
                    )
                    custom_df = custom_df[~custom_df['is_duplicate']].drop(columns=['is_duplicate'])
                    
                    if not custom_df.empty:
                        self.df = pd.concat([self.df, custom_df], ignore_index=True)
                        print(f"[INFO] Merged {len(custom_df)} new approved uploaded books into dataset.")
                    else:
                        print("[INFO] No new custom approved books to merge.")
            finally:
                db.close()
        except Exception as e:
            print(f"[WARNING] Could not load approved books from DB: {e}")

    def reload_data(self):
        """Xóa cache và tải lại toàn bộ dữ liệu (CSV + DB approved books)"""
        print("[INFO] Reloading recommender data...")
        # Xóa file cache cũ để buộc rebuild
        cache_file = self.csv_path.replace('.csv', '_cache.pkl')
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print("[INFO] Old cache deleted.")
            except Exception as e:
                print(f"[WARNING] Could not delete cache: {e}")
        # Reset và tải lại
        self.df = None
        self.tfidf_matrix = None
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=50000,
            ngram_range=(1, 2)
        )
        self.load_and_clean_data(force_rebuild=True)
        print("[INFO] Recommender reloaded successfully.")

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

        # Save the original query before any translation
        description_original = description if description else ""

        # Auto-translate Vietnamese (or any language) to English
        if description and description.strip():
            try:
                print(f"[INFO] Translating query: '{description}'")
                description_translated = GoogleTranslator(source='auto', target='en').translate(description)
                print(f"[INFO] Translated to: '{description_translated}'")
                description = description_translated
            except Exception as e:
                print(f"[WARNING] Translation failed: {e}")

        # Clean the input description
        cleaned_input = self.clean_text(description)

        # Vectorize the input using the already-fitted vectorizer (if we have description)
        similarity_scores = np.zeros(len(working_df))
        if cleaned_input:
            input_vector = self.vectorizer.transform([cleaned_input])
            if input_vector.nnz > 0:
                similarity_scores = cosine_similarity(input_vector, working_matrix).flatten()

        # ── Advanced Hybrid Keyword Match & Boost System ────────────────────
        # Prepare queries
        q_orig = description_original.strip().lower()
        q_orig_no_accent = remove_vietnamese_accents(q_orig)
        
        q_trans = description.strip().lower() if description else ""
        q_trans_no_accent = remove_vietnamese_accents(q_trans)

        boost = np.zeros(len(working_df))
        titles_lower = working_df['Book'].str.lower()
        authors_lower = working_df['Author'].str.lower()
        
        # Non-accent columns for matching
        titles_no_accent = titles_lower.apply(remove_vietnamese_accents)
        authors_no_accent = authors_lower.apply(remove_vietnamese_accents)

        # 1. Whole Phrase Match Boost (extremely strong signal)
        if len(q_orig) > 1:
            # Exact title matches (including accents or accentless)
            t_orig_match = (titles_lower == q_orig) | (titles_no_accent == q_orig_no_accent)
            boost += t_orig_match.values.astype(float) * 2.0  # instant top rank!
            
            # Substring title matches
            t_sub_match = titles_lower.str.contains(re.escape(q_orig), regex=True, na=False) | \
                          titles_no_accent.str.contains(re.escape(q_orig_no_accent), regex=True, na=False)
            boost += t_sub_match.values.astype(float) * 1.2
            
            # Author matches
            a_sub_match = authors_lower.str.contains(re.escape(q_orig), regex=True, na=False) | \
                          authors_no_accent.str.contains(re.escape(q_orig_no_accent), regex=True, na=False)
            boost += a_sub_match.values.astype(float) * 0.8

        if len(q_trans) > 1 and q_trans != q_orig:
            # Exact title matches on translated query
            t_trans_match = (titles_lower == q_trans) | (titles_no_accent == q_trans_no_accent)
            boost += t_trans_match.values.astype(float) * 1.5
            
            # Substring title matches on translated query
            t_trans_sub = titles_lower.str.contains(re.escape(q_trans), regex=True, na=False) | \
                          titles_no_accent.str.contains(re.escape(q_trans_no_accent), regex=True, na=False)
            boost += t_trans_sub.values.astype(float) * 0.9

        # 2. Individual Word Matches Boost
        # Gather all unique word tokens from original query
        words_orig = [w for w in re.split(r'\s+', q_orig) if len(w) > 1]
        words_trans = [w for w in re.split(r'\s+', q_trans) if len(w) > 1] if q_trans != q_orig else []
        
        all_words = list(set(words_orig + words_trans))
        for word in all_words:
            word_no_accent = remove_vietnamese_accents(word)
            
            t_w_match = titles_lower.str.contains(rf"\b{re.escape(word)}\b", regex=True, na=False) | \
                        titles_no_accent.str.contains(rf"\b{re.escape(word_no_accent)}\b", regex=True, na=False)
            a_w_match = authors_lower.str.contains(rf"\b{re.escape(word)}\b", regex=True, na=False) | \
                        authors_no_accent.str.contains(rf"\b{re.escape(word_no_accent)}\b", regex=True, na=False)
            
            boost += t_w_match.values.astype(float) * 0.8
            boost += a_w_match.values.astype(float) * 0.5

        # Combine similarity and boost
        similarity_scores = similarity_scores + boost

        # If no query was provided at all, we fall back to sorting by Avg_Rating
        if not description_original.strip():
            # If no description, just sort by rating
            sorted_df = working_df.sort_values(by='Avg_Rating', ascending=False)
            actual_top_n = min(top_n, len(sorted_df))
            recommendations = []
            for i in range(actual_top_n):
                book = sorted_df.iloc[i]
                desc = str(book['Description'])
                short_desc = desc[:300] + "..." if len(desc) > 300 else desc
                genres_raw = str(book['Genres'])
                genres_list = self.parse_genres(genres_raw)
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
            genres_list = self.parse_genres(genres_raw)

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



    def parse_genres(self, genres_raw: str) -> List[str]:
        if not genres_raw or not isinstance(genres_raw, str):
            return []
        genres_list = []
        for g in genres_raw.split(','):
            g = re.sub(r"[\[\]'\"“”‘’]", "", g).strip()
            if g and g.lower() != 'nan' and len(g) > 1:
                genres_list.append(g)
        return genres_list

    def get_genres(self) -> List[str]:
        """Returns a sorted list of unique genres from the dataset, prioritizing popular ones."""
        if self.df is None:
            return []

        from collections import Counter
        genre_counts = Counter()
        db_genres = set()
        
        # Đảm bảo các thể loại từ sách do người dùng đóng góp đã duyệt luôn xuất hiện
        try:
            from database import SessionLocal, UploadedBook
            db = SessionLocal()
            try:
                custom_books = db.query(UploadedBook).filter(
                    UploadedBook.status == 'approved'
                ).all()
                for b in custom_books:
                    for g in self.parse_genres(b.genres or ''):
                        db_genres.add(g)
            finally:
                db.close()
        except Exception as e:
            print(f"[WARNING] Failed to load db genres for categories: {e}")

        # Đếm tần suất xuất hiện của tất cả các thể loại trong DataFrame hiện tại
        for genres_str in self.df['Genres'].dropna():
            cleaned_genres = self.parse_genres(str(genres_str))
            for g in cleaned_genres:
                genre_counts[g] += 1

        # Lấy toàn bộ thể loại để đảm bảo các thể loại mới được thêm vào CSV luôn xuất hiện
        all_dataset_genres = list(genre_counts.keys())
        
        # Gộp các thể loại từ CSV với các thể loại từ cơ sở dữ liệu sách đóng góp
        combined_genres = set(all_dataset_genres).union(db_genres)
        
        return sorted(list(combined_genres))


# Initialize the recommender with the correct relative path
_dir = os.path.dirname(os.path.abspath(__file__))
_data_path = os.path.join(_dir, '..', 'data', 'goodreads_data.csv')
recommender = BookRecommender(_data_path)
