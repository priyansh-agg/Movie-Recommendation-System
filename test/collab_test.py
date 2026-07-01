from recommendation.collaborative.recommender import recommend

movies = recommend(1)

for movie in movies:
    print(movie)