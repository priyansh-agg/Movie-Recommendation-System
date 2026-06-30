from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from recommendation.content_based.loader import movie_titles
from recommendation.content_based.recommender import recommend


def _get_label(similarity):
    if similarity >= 0.60:
        label = "Excellent Match"
    elif similarity >= 0.45:
        label = "Strong Match"

    elif similarity >= 0.30:
        label = "Good Match"
    else:
        label = "Similar"
    

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommendation System")
selected_movie = st.selectbox(
    "Choose a movie",
    movie_titles["title"].values
)

if st.button("Recommend"):
    recommendations = recommend([selected_movie])

    if not recommendations:
        st.warning("No recommendations found.")
    else:
        for movie in recommendations:

            st.image(movie["poster"], width=220)

            st.subheader(movie["title"])

            st.caption(
                f"Because you liked **{movie['source_movie']}**"
            )

            st.progress(min(movie["score"], 1.0))

            st.caption(
                f"Similarity: {movie['score']:.0%}"
            )

            with st.expander("Why this recommendation?"):
                for reason in movie["explanation"]:
                    st.write(f"• {reason}")

            st.divider()