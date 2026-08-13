"""Streamlit movie recommender application.

The recommender builds a sparse bag-of-words representation from the tags
already stored in movie_dict.pkl. It calculates similarities only for the
selected movie, so no similarity.pkl download or Google Drive access is needed.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "movie_dict.pkl"
PLACEHOLDER_POSTER = BASE_DIR / "assets" / "poster-placeholder.svg"
REQUIRED_COLUMNS = {"movie_id", "title", "tags"}


st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide",
)


def get_tmdb_api_key() -> str:
    """Read the TMDB key from Streamlit secrets or an environment variable."""
    try:
        key = str(st.secrets.get("TMDB_API_KEY", "")).strip()
    except (FileNotFoundError, KeyError):
        key = ""
    return key or os.getenv("TMDB_API_KEY", "").strip()


@st.cache_resource(show_spinner="Preparing the movie catalogue...")
def load_movies_and_vectors() -> tuple[pd.DataFrame, object]:
    """Load the movie catalogue and create a memory-efficient sparse matrix."""
    if not MOVIES_FILE.is_file():
        raise FileNotFoundError(
            "movie_dict.pkl is missing. Keep it in the same folder as app.py."
        )

    with MOVIES_FILE.open("rb") as file:
        movie_data = pickle.load(file)

    movies = pd.DataFrame(movie_data).reset_index(drop=True)
    missing_columns = REQUIRED_COLUMNS.difference(movies.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"movie_dict.pkl is missing required columns: {missing}")

    movies = movies.loc[:, ["movie_id", "title", "tags"]].copy()
    movies["title"] = movies["title"].fillna("Untitled").astype(str)
    movies["tags"] = movies["tags"].fillna("").astype(str)

    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    movie_vectors = vectorizer.fit_transform(movies["tags"])

    if movie_vectors.shape[1] == 0:
        raise ValueError("No usable movie tags were found in movie_dict.pkl.")

    return movies, movie_vectors


@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_poster(movie_id: int, api_key: str) -> str | None:
    """Return a TMDB poster URL, or None if the request is unavailable."""
    if not api_key:
        return None

    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": api_key, "language": "en-US"},
            timeout=12,
        )
        response.raise_for_status()
        poster_path = response.json().get("poster_path")
    except (requests.RequestException, ValueError):
        return None

    if not poster_path:
        return None
    return f"https://image.tmdb.org/t/p/w500{poster_path}"


def recommend(
    movie_title: str,
    movies: pd.DataFrame,
    movie_vectors: object,
    limit: int = 10,
) -> list[dict[str, object]]:
    """Find the most similar movies for the selected title."""
    matches = movies.index[movies["title"] == movie_title].tolist()
    if not matches:
        return []

    selected_index = matches[0]
    scores = cosine_similarity(
        movie_vectors[selected_index], movie_vectors
    ).ravel()
    ranked_indices = scores.argsort()[::-1]

    recommendations: list[dict[str, object]] = []
    for index in ranked_indices:
        index = int(index)
        if index == selected_index:
            continue

        recommendations.append(
            {
                "movie_id": int(movies.iloc[index]["movie_id"]),
                "title": str(movies.iloc[index]["title"]),
                "similarity": float(scores[index]),
            }
        )
        if len(recommendations) == limit:
            break

    return recommendations


try:
    MOVIES, MOVIE_VECTORS = load_movies_and_vectors()
except (FileNotFoundError, OSError, pickle.UnpicklingError, ValueError) as error:
    st.error(f"The movie catalogue could not be loaded: {error}")
    st.stop()


TMDB_API_KEY = get_tmdb_api_key()

st.title("🎬 Movie Recommender System")
st.write("Choose a movie to discover ten similar titles.")

if not TMDB_API_KEY:
    st.info(
        "Recommendations are available, but poster images require a TMDB API "
        "key in Streamlit Secrets. See README.md for setup instructions."
    )

movie_titles = sorted(MOVIES["title"].drop_duplicates().tolist())
selected_movie = st.selectbox("Select a movie", movie_titles)

if st.button("Recommend", type="primary", width="stretch"):
    with st.spinner("Finding similar movies..."):
        results = recommend(selected_movie, MOVIES, MOVIE_VECTORS)

    if not results:
        st.warning("No recommendations were found for this movie.")
    else:
        for row_start in range(0, len(results), 5):
            columns = st.columns(5)
            row_results = results[row_start : row_start + 5]

            for column, movie in zip(columns, row_results):
                with column:
                    poster_url = fetch_poster(
                        int(movie["movie_id"]), TMDB_API_KEY
                    )
                    poster = poster_url or str(PLACEHOLDER_POSTER)
                    st.image(poster, width="stretch")
                    st.markdown(f"**{movie['title']}**")
