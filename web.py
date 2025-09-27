import pickle
import streamlit as st
import requests
import re
from PIL import Image
from io import BytesIO

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="🎬 Movie Recommender",
    page_icon="🎥",
    layout="wide"
)

# ---------------------------
# Custom CSS (full)
# ---------------------------
st.markdown(
    """
    <style>
    /* Full page gradient background */
    .stApp {
        background: linear-gradient(to right, #0a1f44, #12294f, #1b3460);
        color: #ffffff;
        transition: all 0.3s ease;
    }

    /* Top navbar */
    .navbar {
        background-color: #0d1b2a;
        padding: 15px 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.4);
    }

    /* Logo & title tweaks to remove gaps and enlarge text */
    .navbar-logo {
        display: inline-flex;
        align-items: center;
        gap: 6px;               /* small gap between icon and text */
        font-size: 1.6rem;      /* base title size */
        font-weight: 700;
        color: #ffffff;
        white-space: nowrap;    /* prevent wrapping */
        letter-spacing: -0.02em;/* slightly tighten overall letter spacing */
    }

    /* Make highlight match size and pull letters closer */
    .navbar-logo .highlight {
        color: #4e89ae;
        display: inline-block;
        margin-right: -6px;     /* pull the colored letter toward following letters */
        font-size: 1.9rem;      /* enlarged M and R (approx +2 steps) */
        font-weight: 800;
        line-height: 1;
        vertical-align: middle;
    }

    .navbar-links a {
        margin: 0 15px;
        text-decoration: none;
        color: #e0f7ff;
        font-weight: bold;
        transition: color 0.3s ease;
    }
    .navbar-links a:hover {
        color: #4e89ae;
    }

    /* Button */
    .stButton>button {
        background: linear-gradient(90deg, #1b3460, #4e89ae);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5em 1.5em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #4e89ae, #1b3460);
    }

    /* Input box */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.15);
        color: #000000;
        border-radius: 8px;
        padding: 0.5em;
        border: none;
        box-shadow: 0 0 8px rgba(0, 150, 255, 0.5);
        transition: all 0.3s ease;
        font-size: 1.1em;
        font-weight: bold;
    }

    /* Label above input */
    .stTextInput label {
        font-size: 1.25em;
        color: #e0f7ff;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 0px;
    }

    /* Hover effect for posters */
    .stImage img {
        transition: transform 0.4s ease, box-shadow 0.4s ease, filter 0.4s ease !important;
        border-radius: 12px;
    }
    .stImage img:hover {
        transform: scale(1.05);
        box-shadow: 0 15px 30px rgba(0, 200, 255, 0.5);
        filter: brightness(1.15) contrast(1.05);
    }

    /* Movie card */
    .movie-card {
        background: rgba(30, 50, 80, 0.6);
        border-radius: 15px;
        padding: 10px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        backdrop-filter: blur(5px);
        color: #e0f7ff;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Header / Navbar (updated HTML)
# ---------------------------
st.markdown(
    """
    <div class="navbar">
        <div class="navbar-logo">
            <img src="https://cdn-icons-png.flaticon.com/512/3163/3163478.png" alt="logo" style="height:40px;">
            <span class="highlight">M</span>ovie<span style="margin-left:6px;"></span><span class="highlight">R</span>ecommender
        </div>
        <div class="navbar-links">
            <a href="#">Home</a>
            <a href="#">Movies</a>
            <a href="#">Latest</a>
            <a href="#">My List</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Functions
# ---------------------------
def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def fetch_poster(movie_id, api_key):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        data = requests.get(url, timeout=5).json()
    except Exception:
        return "https://via.placeholder.com/500x750?text=No+Poster"
    poster_path = data.get('poster_path')
    if poster_path:
        return "https://image.tmdb.org/t/p/w500" + poster_path
    else:
        return "https://via.placeholder.com/500x750?text=No+Poster"

def recommend(movie_title, topn=5, api_key=None):
    normalized_title = normalize_text(movie_title)
    normalized_title_nospace = normalized_title.replace(' ', '')

    matches = movies[movies['normalized_title'] == normalized_title]
    if matches.empty:
        matches = movies[movies['normalized_title_nospace'] == normalized_title_nospace]

    if matches.empty:
        st.error(f"Movie '{movie_title}' not found. Try another title or type it fully.")
        return [], []

    idx = matches.index[0]
    distances = sorted(enumerate(similarity[idx]), key=lambda x: x[1], reverse=True)

    recommended_movies_name = []
    recommended_movies_poster = []

    for i in distances[1: topn+1]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies_name.append(movies.iloc[i[0]].title)
        recommended_movies_poster.append(fetch_poster(movie_id, api_key))

    return recommended_movies_name, recommended_movies_poster

# ---------------------------
# Load Data
# ---------------------------
movies = pickle.load(open('artificats/movie_list.pkl', 'rb'))
similarity = pickle.load(open('artificats/similarity.pkl', 'rb'))

if 'normalized_title' not in movies.columns:
    movies['normalized_title'] = movies['title'].apply(normalize_text)
    movies['normalized_title_nospace'] = movies['normalized_title'].str.replace(' ', '')

api_key = "d3f2b9fd278527a66ae3a3ff81ea2e8f"

# ---------------------------
# Search Box with Label
# ---------------------------
movie_input = st.text_input("Type a movie name:", placeholder="Enter movie name...")

if st.button('Show Recommendation') and movie_input:
    recommended_movies_name, recommended_movies_poster = recommend(movie_input, api_key=api_key)

    if recommended_movies_name:
        cols = st.columns(len(recommended_movies_name))
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"<div class='movie-card'>", unsafe_allow_html=True)
                st.markdown(f"<span>{recommended_movies_name[i]}</span>", unsafe_allow_html=True)
                st.image(recommended_movies_poster[i])
                st.markdown("</div>", unsafe_allow_html=True)
