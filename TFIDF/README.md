# TF-IDF model guide


This model uses TF-IDF embeddings with Truncated SVD to provide movie recommendations based on a user-defined movie review. It does not give very good results. However, it contains an effective method for constructing a Document-Term Matrix (DTM) from millions of documents in an efficient manner that is robust to network failures.

One problem with gradually building a large dataframe in Pandas is that every time you add a row, the dataframe must be copied in its entirety. I decided to first fetch all the rows from the database and store them locally, so that progress is not lost in the event of a network failure. Once all rows have been fetched and serialized, the Master DTM can be constructed in one command. To make the process robust to network failures, I made a setup wizard with multiple commands that can be executed in sequence. This repo also contains a bash script that attempts to run the process and can continue after the terminal session is ended.



To run this code, you need a database of movie reviews. The columns used are:
- movie_id (varchar)
- review_text (varchar)
