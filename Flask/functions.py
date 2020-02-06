import pandas as pd

from w2v_inference import Recommender

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
    for i in list:
        session[f'{i}'] = i.to_json()
    return tuple(list)

'''ratings = pd.read_json(session['ratings'])
reviews = pd.read_json(session['reviews'])
watched = pd.read_json(session['watched'])
watchlist = pd.read_json(session['watchlist'])'''

def multi_read_json(list):
    '''
    for retrieving multiple data frames from session
    '''
    for i in list:
        i = pd.read_json(session[f'{i}'])
    return tuple(list)

""" recs['Liked by fans of...'] = recs['Movie ID'].apply(lambda x: s.get_most_similar_title(x, good_list))
recs['URL'] = recs['URL'].apply(links)
recs['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
    + recs['Movie ID'] + '>  Good idea<br>'
recs['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
    + recs['Movie ID'] + '>  Hard No<br>'"""

def links(x):
    '''Changes URLs to actual links'''
    return '<a href="%s">Go to the IMDb page</a>' % (x)

def rec_edit(df):
    '''
    adds various columns to the recommendation data frame, namely:
    Liked by fans of shows you what movie the recommendation is most similar to from your good list
    URL changes the URL to an acutal hypertext link
    Vote Up/Down add the HTML for checkboxes
    ''' 
    df['Liked by fans of...'] = df['Movie ID'].apply(lambda x: Recommender(master_r2v).get_most_similar_title(x, good_list))
    df['URL'] = df['URL'].apply(lambda x: f'<a href="{x}">Go to the IMDb page</a>') #may need links or adjust lambda func
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
    for i in list:
        session[f'{i}'] = json.dumps(i)
    return tuple(list)

'''session['good_rate'] = good_rate
    session['bad_rate'] = bad_rate
    session['hidden'] = hidden
    session['cult'] = cult
    session['extra_weight'] = extra_weight'''

def multi_session(list):
    '''
    takes a list of variables and defines session variables for them
    '''
    for i in list:
        session[f'{i}'] = i
    return tuple(list)

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
    for i in list:
        #strip i for session[] so that the variable name remains
        i = json.loads(i)
    return tuple(list)