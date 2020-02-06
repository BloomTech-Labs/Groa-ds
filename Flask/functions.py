import pandas as pd
from flask import session
from w2v_inference import Recommender
import json

#make predetermined lists so that 

'''reviews = pd.read_csv(f'temp{tag}/reviews.csv')
watched = pd.read_csv(f'temp{tag}/watched.csv')
watchlist = pd.read_csv(f'temp{tag}/watchlist.csv')'''

def multi_read(list,tag):
    '''
    for reading multiple csvs and defining them as variables
    '''
    x=[]
    for i in list:
        x.append(pd.read_csv(f'temp{tag}/{i}.csv'))
    return x


'''session['ratings'] = ratings.to_json()
session['reviews'] = reviews.to_json()
session['watched'] = watched.to_json()
session['watchlist'] = watchlist.to_json()'''

def multi_jsonify(list):
    '''
    for sessioning multiple data frames
    '''
    x=[]
    for i in list:
        x.append(i.to_json())
    return x

'''ratings = pd.read_json(session['ratings'])
reviews = pd.read_json(session['reviews'])
watched = pd.read_json(session['watched'])
watchlist = pd.read_json(session['watchlist'])'''

def multi_read_json(list):
    '''
    for retrieving multiple data frames from session
    '''
    x=[]
    for i in list:
        x.append(pd.read_json(session[f'{i}']))
    return x

""" recs['Liked by fans of...'] = recs['Movie ID'].apply(lambda x: s.get_most_similar_title(x, good_list))
recs['URL'] = recs['URL'].apply(links)
recs['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
    + recs['Movie ID'] + '>  Good idea<br>'
recs['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
    + recs['Movie ID'] + '>  Hard No<br>'"""

def links(x):
    '''Changes URLs to actual links'''
    return '<a href="%s">Go to the IMDb page</a>' % (x)

def rec_edit(df,good_list):
    '''
    adds various columns to the recommendation data frame, namely:
    Liked by fans of shows you what movie the recommendation is most similar to from your good list
    URL changes the URL to an acutal hypertext link
    Vote Up/Down add the HTML for checkboxes
    ''' 
    master_r2v = 'models/r2v_Botanist_v1.1000.5.model'
    df['Liked by fans of...'] = df['Movie ID'].apply(lambda x: Recommender(master_r2v).get_most_similar_title(x, good_list))
    df['URL'] = df['URL'].apply(lambda x: f'<a href="{x}">IMDb page</a>') #may need links or adjust lambda func
    df['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
        + df['Movie ID'] + '>  Good idea<br>'
    df['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
        + df['Movie ID'] + '>  Hard No<br>'
    return df

'''session['id_list'] = json.dumps(id_list)
    session['good_list'] = json.dumps(good_list)
    session['bad_list'] = json.dumps(bad_list)
    session['hist_list'] = json.dumps(hist_list)
    session['val_list'] = json.dumps(val_list)
    session['ratings_dict'] = json.dumps(ratings_dict)'''

def multi_dump(list):
    '''
    takes a list of lists, dumps them to json, and defines session variables for them
    '''
    x=[]
    for i in list:
        x.append(json.dumps(i))
    return x

'''session['good_rate'] = good_rate
    session['bad_rate'] = bad_rate
    session['hidden'] = hidden
    session['cult'] = cult
    session['extra_weight'] = extra_weight'''

def multi_session(list):
    '''
    takes a list of variables and defines session variables for them
    '''
    x=[]
    for i in list:
        x.append(i)
    return x

'''id_list = json.loads(session['id_list']) # all of the ids of the previous recommendations
    good_list = json.loads(session['good_list'])
    bad_list = json.loads(session['bad_list'])
    hist_list = json.loads(session['hist_list'])
    val_list = json.loads(session['val_list'])
    ratings_dict = json.loads(session['ratings_dict'])'''

def multi_load(list):
    '''
    takes a list of session objects and assigns them to variables
    '''
    x=[]
    for i in list:
        #strip i for session[] so that the variable name remains
        x.append(json.loads(session[f'{i}']))
    return x

def bool_func(column,id_list):
    '''
    This function checks the "Movie ID" column against the id_list and
    will give booleans on whether the ID in the column is present on the list.
    If it is present, then it changes the entry from True to NEW!.
    '''
    bool_list=[]
    for x in column:
        bool_list.append(x in id_list)
    b = ['<p style="color: #00bc8c">NEW!</p>' if x==True else '' for x in bool_list]
    return b