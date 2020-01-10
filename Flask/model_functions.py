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
    def predict(cls, input):
        """For the input, do the predictions and return them.

        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""

        clf = cls.get_model()

        def _aggregate_vectors(movies):
            # get the vector average of the movies in the input
            movie_vec = []
            for i in movies:
                try:
                    movie_vec.append(clf[i])
                except KeyError:
                    continue
            
            return np.mean(movie_vec, axis=0)[0]

        def _similar_movies(v, n = 6):
            # extract most similar movies for the input vector
            return clf.similar_by_vector(v, topn= n+1)[1:]

        input = [[x[0].lstrip("0")] for x in input] # remove leading zeroes
        recs = _similar_movies(_aggregate_vectors(input))
        return recs