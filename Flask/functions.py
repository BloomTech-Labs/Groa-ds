import pandas as pd
from flask import session
from w2v_inference import Recommender
import json

# possible types: strings from session, lists, dataframes, csvs,
# things it needs to do for df:read_csv,to_json,read_json
# things it needs to do for lists: dumps, loads
# good_rate and bad_rate should be floats, I think extra_weight is a bool
def save_session(var_list):
    '''
    Takes lists of objects and appropriately sessions them
    '''
    return_list = []
    for x in var_list:
        if isinstance(x,pd.DataFrame):
            return_list.append(x.to_json())
        elif isinstance(x,list):
            return_list.append(json.dumps(x))
        elif isinstance(x,(bool or int or float)):
            return_list.append(x)
    return return_list    

def load_session(str_list):
    '''
    takes a list of sessions and 
    turns them into their appropriate types
    '''
    df_list = ['hidden_df', 'cult_df', 'recs', 'reviews',
               'watched', 'watchlist']
    list_list = ['id_list', 'good_list', 'bad_list', 'hist_list', 
                 'val_list', 'ratings_dict', 'checked_list', 'rejected_list']
    other_list = ['good_rate', 'bad_rate', 'extra_weight']

    return_list = []
    for x in str_list:
        if x in df_list:
            return_list.append(pd.read_json(session[x]))
        elif x in list_list:
            return_list.append(json.loads(session[x]))
        else:
            return_list.append(session[x])
    return return_list
        
def highlight_watchlist(id_column, title_column, watchlist):
    '''
    This function checks the "Movie ID" column against the watchlist and
    will give booleans on whether the ID in the column is present on the list.
    If it is present, then it adds color styling.
    '''
    bool_list=[]
    for x in id_column:
        bool_list.append(str(x) in watchlist)
    matched = list(zip(title_column, bool_list))
    b = [f'<p style="color:#b59fe0">{title}</p>' if x==True else title for title, x in matched]
    return b

def links(x):
    '''Changes URLs to actual links'''
    return '<a href="%s">Go to the IMDb page</a>' % (x)

def rec_edit(df, val_list):
    '''
    adds various columns to the recommendation data frame, namely:
    Liked by fans of shows you what movie the recommendation is most similar to from your good list
    URL changes the URL to an actual hypertext link
    Vote Up/Down add the HTML for checkboxes
    '''
    df['IMDb Link'] = df['IMDb Link'].apply(lambda x: f'<a href="{x}">IMDb</a>') #may need links or adjust lambda func
    df['Letterboxd Link'] = df['Movie ID'].apply(lambda x: f'<a href="{x}">Letterboxd</a>') #may need links or adjust lambda func
    df['Title'] = highlight_watchlist(df['Movie ID'], df['Title'], val_list)
    df['Vote Up'] = '<input type="checkbox" name="upvote" value=' \
        + df['Movie ID'] + '>  Good idea<br>'
    df['Vote Down'] = '<input type="checkbox" name="downvote" value=' \
        + df['Movie ID'] + '>  Hard No<br>'
    return df

def multi_read(list,tag):
    '''
    Takes a list of CSV file names and returns them as a list of dataframes.
    The tag is a random number generated to create a unique temp folder, so
    that users' sessions do not interfere with one another.
    '''
    x=[]
    for i in list:
        x.append(pd.read_csv(f'temp{tag}/{i}.csv'))
    return x

def multi_jsonify(list):
    '''
    for sessioning multiple dataframes to JSON
    '''
    x=[]
    for i in list:
        x.append(i.to_json())
    return x

def multi_read_json(list):
    '''
    for retrieving multiple dataframes from session
    '''
    x=[]
    for i in list:
        x.append(pd.read_json(session[f'{i}']))
    return x

def multi_dump(list):
    '''
    takes a list of lists, dumps them to json, and defines session variables for them
    '''
    x=[]
    for i in list:
        x.append(json.dumps(i))
    return x

def multi_session(list):
    '''
    takes a list of variables and defines session variables for them
    '''
    x=[]
    for i in list:
        x.append(i)
    return x

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

def timer_func(printme=""):
    """Prints seconds passed since last checkpoint, for debugging purposes."""
    global my_time
    print(printme, "--- %s seconds ---" % (time.time() - my_time))
    my_time = time.time()
