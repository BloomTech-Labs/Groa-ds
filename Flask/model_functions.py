import gensim
import numpy as np

class ScoringService(object):
    model = None                # Where we keep the model when it's loaded

    @classmethod
    def get_model(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.model == None:
            # load the gensim model
            w2v_model = gensim.models.Word2Vec.load("word2vec_2.model")
            # keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            w2v_model.init_sims(replace=True)
            # with open(os.path.join(model_path, 'decision-tree-model.pkl'), 'r') as inp:
            #     cls.model = pickle.load(inp)
            cls.model = w2v_model
        return cls.model

    @classmethod
    def get_model(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.model == None:
            # load the gensim model
            w2v_model = gensim.models.Word2Vec.load("w2v_mistakenot.model")
            # keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            w2v_model.init_sims(replace=True)
            # with open(os.path.join(model_path, 'decision-tree-model.pkl'), 'r') as inp:
            #     cls.model = pickle.load(inp)
            cls.model = w2v_model
        return cls.model

    @classmethod
    def predict(cls, input, bad_movies=[], n=20, harshness=1):
        """Returns a list of recommendations and useful metadata, given a pretrained
        word2vec model and a list of movies.

        Args:
            cls (.model object): The pretrained word2vec model.

            input (list of strings): The list of movies that the user likes.

            bad_movies (list of strings): The list of movies that the user dislikes.

            n (int): The number of recommendations to return.

        Output: A list of tuples: Title, Year, IMDb URL, Similarity score.
        """

        # get pretrained model
        clf = cls.get_model()

        def _aggregate_vectors(movies):
            """Gets the vector average of a list of movies."""
            movie_vec = []
            for i in movies:
                try:
                    movie_vec.append(clf[i]) # get the vector for each movie
                except KeyError:
                    continue
            return np.mean(movie_vec, axis=0)

        def _similar_movies(v, bad_movies=[], n = 10):
            """Takes aggregated vector of good movies,
            and optionally, a list of disliked movies.
            Subtracts disliked movies.
            Returns most similar movies for the input vector

            n: number of recommendations to return."""
            if bad_movies:
                v = _remove_dislikes(bad_movies, v, input=input, harshness=harshness)
            return clf.similar_by_vector(v, topn= n+1)[1:]

        def _remove_dupes(recs, input, bad_movies):
            """remove any recommended IDs that were in the input list"""
            all_seen = input + bad_movies
            return [x for x in recs if x[0] not in all_seen]

        def _get_info(id):
            """Takes an id string and returns the movie info with a url."""
            try:
                c.execute(f"""
                select primary_title, start_year
                from movies
                where movie_id = '{id[0]}'""")
            except:
                return f"Movie title unknown. ID:{id}"

            t = c.fetchone()
            title = tuple([t[0], t[1], f"https://www.imdb.com/title/tt{id[0]}/", id[1]])
            return title

        def _remove_dislikes(bad_movies, good_movies_vec, input=1, harshness=1):
            """Takes a list of movies that the user dislikes.
            Their embeddings are averaged,
            and subtracted from the input."""
            bad_vec = _aggregate_vectors(bad_movies)
            bad_vec = bad_vec / harshness
            return good_movies_vec - bad_vec

        recs = _aggregate_vectors(input)
        recs = _similar_movies(recs, bad_movies, n=n)
        recs = _remove_dupes(recs, input, bad_movies)
        recs = [_get_info(x) for x in recs]
        return recs
