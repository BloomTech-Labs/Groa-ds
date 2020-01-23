# This is the file that implements a flask server to do inferences. It's the file that you will modify to
# implement the scoring for your own algorithm.

from __future__ import print_function

import os
import json
import gensim
from gensim.models.word2vec import Word2Vec
import numpy as np
import pandas as pd
import pickle
from io import StringIO
import sys
import signal
import traceback
import glob

import flask



prefix = '/opt/ml/'
model_path = os.path.join(prefix, 'model')

# A singleton for holding the model. This simply loads the model and holds it.
# It has a predict function that does a prediction based on the model and the input data.

class ScoringService(object):
    model = None                # Where we keep the model when it's loaded

    @classmethod
    def get_model(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.model == None:
            # load the gensim model
            w2v_model = Word2Vec.load(os.path.join(model_path, 'word2vec_2.model'))
            print("Model vector_size:", w2v_model.vector_size)
            #w2v_model = w2v_model.init_sims(replace=True)
            cls.model = w2v_model
        return cls.model

    @classmethod
    def predict(cls, input):
        """For the input, do the predictions and return them.
        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""

        clf = cls.get_model()
        print("Model load:", clf)

        def _similar_movies(v, n = 6):
            # extract most similar movies for the input vector
            print("V load shape:", v.shape)
            v = v.reshape(-1)
            print("V shape after reshape: ", v.shape)
            ms = clf.similar_by_vector(v, topn= n+1)#[1:]
            
            return ms
        
        def _aggregate_vectors(movies):
            # get the vector average of the movies in the input
            movie_vec = []
            print("Movies: ", movies)
            movies = movies
            print("Movies Datatype: ", movies.dtypes)
            for i in movies.values:
                try:
                    movie_vec.append(clf[i])
                except KeyError:
                    continue
            print("Movie_vec: ", movie_vec)
            return np.mean(movie_vec, axis=0)

        
        print("Right before aggregate_vectors")
        new = _aggregate_vectors(input)
        #print(new)
        recs = _similar_movies(new)
        return recs

# The flask app for serving predictions
app = flask.Flask(__name__)

@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""

    status = 200
    folders = [f for f in glob.glob(model_path+'/*')]

    for f in folders:
        print("Folders:", f)
    return flask.Response(response='\n', status=status, mimetype='application/csv')

@app.route('/invocations', methods=['POST'])
def transformation():
    """Do an inference on a single batch of data. In this sample server, we take data as CSV, convert
    it to a pandas data frame for internal use and then convert the predictions back to CSV (which really
    just means one prediction per line, since there's a single column.
    """
    data = None

    # Convert from CSV to pandas
    if flask.request.content_type == 'text/csv':
        print("Flask Request: ", flask.request)
        data = flask.request.data.decode('utf-8')
        print("Flask data ingest", data)
        s = StringIO(data)
        print("String IO", s)
        #the s is required and doesn't seem to be breaking it
        data = pd.read_csv(s, sep=",").T
        data[0] = data.index
        data = data.reset_index(drop=True)
        print("Pandas df", data)
    else:
        return flask.Response(response='This predictor only supports CSV data', status=415, mimetype='text/plain')

    print('Invoked with {} records'.format(data.shape[0]))

    # Do the prediction
    predictions = ScoringService.predict(data)

    # Convert from numpy back to CSV
    out = StringIO()
    pd.DataFrame({'results':predictions}).to_csv(out, header=False, index=False)
    result = out.getvalue()

    return flask.Response(response=result, status=200, mimetype='text/csv')
