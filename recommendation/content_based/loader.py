import pickle
import pandas as pd

similarity = pickle.load(open("recommendation/models/similarity.pkl","rb"))
rating = pickle.load(open("recommendation/models/rating.pkl","rb"))

movie_titles = pd.read_csv(
    "recommendation/models/movie_titles.csv"
)

movie_to_index = pd.Series(
    movie_titles.index,
    index=movie_titles["title"]
).to_dict()

movie_metadata = pickle.load(open("recommendation/models/movie_metadata.pkl","rb"))