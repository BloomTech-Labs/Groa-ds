import json
import pandas as pd
import psycopg2
from os import path
from getpass import getpass


"""
Populate the movies table.

It's already created, so we only need to insert the data.
"""

# connect to database
connection = psycopg2.connect(
    database  = "postgres",
    user      = "postgres",
    password  = getpass(),
    host      = "movie-rec-scrape.cvslmiksgnix.us-east-1.rds.amazonaws.com",
    port      = '5432'
)

# cursor object
try:
    cursor_boi = connection.cursor()
    print("Connected!")
except:
    print("Connection problem chief!")

# open movies file
basepath = path.dirname(__file__)
path = 'title_basics.tsv'
basics = pd.read_csv(path, delimiter='\t').replace("'", "\'") #esc. apostrophe

# remove anything that isn't a movie
basics = basics[basics.titleType.str.contains("movie|tvMovie")]
# convert values
basics.tconst = basics.tconst.str.lstrip("t") # strip leading t's
basics.startYear = pd.to_numeric(basics.startYear, errors='coerce')
basics.endYear = pd.to_numeric(basics.endYear, errors='coerce')
basics.runtimeMinutes = pd.to_numeric(basics.runtimeMinutes, errors='coerce')
# fill nulls with 99999
basics = basics.fillna(99999)
# remove short movies
basics = basics[(basics.runtimeMinutes.astype(int) > 70) \
              & (basics.runtimeMinutes.astype(int) < 99999)]
#convert numerics to int
basics.startYear = basics.startYear.astype(int)
basics.endYear = basics.endYear.astype(int)
basics.runtimeMinutes = basics.runtimeMinutes.astype(int)

print(basics.dtypes) # for debugging

old_columns = ['tconst', 'titleType', 'primaryTitle', 'originalTitle', 'isAdult',
                'startYear', 'endYear','runtimeMinutes', 'genres']
new_columns = ['movie_id', 'title_type', 'primary_title', 'original_title',
            'is_adult', 'start_year', 'end_year', 'runtime_minutes', 'genres']

basics = basics.rename(columns=dict(zip(old_columns, new_columns)))

"""I tried a couple ways to bulk insert this data.
This method seems like it will preserve the escaped apostrophes,
which is necessary."""
# convert to records for use in the query.
data = basics.to_dict('records')

query = """
INSERT INTO movies (movie_id, title_type, primary_title, original_title,
                    is_adult, start_year, end_year, runtime_minutes, genres)
SELECT
    movie_id, title_type, primary_title, original_title,
    is_adult, start_year, end_year, runtime_minutes, genres
FROM json_populate_recordset(null::movies, %s);
"""

print("BULK INSERT TIME!")
cursor_boi.execute(query, (json.dumps(data), ))

connection.commit()
cursor_boi.close()
print("BULK INSERT COMPLETE!")

#
# # save to csv for copying
# basics.to_csv('basics.csv', index=False)
#
# #import csv
# f = open('basics.csv', 'r')
# cursor_boi.copy_from(f, 'movies', sep=',')
# f.close()
