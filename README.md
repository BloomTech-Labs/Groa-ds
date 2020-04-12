# Gróa

You can check out the [live demo of Gróa here](http://www.groa.us/).

## Contributors

|                                       [Michael Gospodinoff](https://github.com/cmgospod)                                        |                                       [Gabe flomo](https://github.com/gabe-flomo)                                        |                                       [Jeff Rowe](https://github.com/Jeffrowetull)                                        |                                       [Coop Williams](https://github.com/coopwilliams)                                        |                                       [Eric Smith](https://github.com/moviedatascience)                                        |
| :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: |
|                      [<img src="https://avatars1.githubusercontent.com/u/53590416?s=400&u=1ddb3c7742a0c79a8d108b2aeff7680e32faa29e&v=4" width = "200" />](https://github.com/cmgospod)                       |                      [<img src="https://avatars0.githubusercontent.com/u/44428182?s=460&v=4" width = "200" />](https://github.com/gabe-flomo)                       |                      [<img src="https://avatars0.githubusercontent.com/u/18298291?s=460&v=4" width = "200" />](https://github.com/Jeffrowetull)                       |                      [<img src="https://avatars2.githubusercontent.com/u/6357375?s=460&v=4" width = "200" />](https://github.com/)                       |                      [<img src="https://avatars2.githubusercontent.com/u/7471385?s=460&v=4" width = "200" />](https://www.imdb.com/title/tt0047522/videoplayer/vi375194649)                       |
|                 [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/cmgospod)                 |            [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/gabe-flomo)             |           [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/Jeffrowetull)            |          [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/coopwilliams)           |            [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/moviedatascience)             |
| [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/michael-gospodinoff-00908216a/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/jeff-rowe-36216a6b/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/cooper-williams-308b2a60/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/ericdavidsmith91/) |


## Project Overview


 [Trello Board](https://trello.com/b/ZyU1nW83/labs19-movierecommender)
We use Trello as a quick wireframe tracker through the first stages of development. As the product moves past releases 1.1 and 1.2 we will transition away from Trello and into the git ecosystem entirely. 

 [Product Canvas](https://www.notion.so/b593b3d6c6ca41b5a32871e10e4ac3b7?v=bfe15a25eab44b15bfdc04fd1763cc2e)
This notion document serves as a solid resource if you want to learn more about our motivations for creating this product and the general development direction it is taking.

### Project Description

The companies which have the resources to create an elegant Movie Recommendation Engine have a profit motive aligned with recommending high cost proprietary content rather than films their customers would genuinely enjoy.

Existing web sites geared towards providing a recommendation rely entirely on basic rating models which are weighted heavily towards popular films and generally do a poor job identifying unique outliers.

Groa combines the public data available on IMDb with tried-and-true recommendation techniques to provide a user-driven movie discovery experience. We use two similar language embedding models to achieve this.

- We trained Word2Vec on positive user ratings histories to create a user-based collaborative filtering recommender. The algorithm embeds over 97,000 movie IDs into a 100-dimensional vector space according to their co-occurence in a user's positive ratings history. The ID for each movie is a key for its vector, which can be called from the model and compared with any other vector in that space for cosine-similarity. To provide recommendations given a new user's watch history, we simply find the vector average of the user's choice of "good movies" and find the top-n cosine-similar vectors from the model. We can improve the recommendations by subtracting a "bad movies" vector from the "good movies" vector before inferencing. Models trained in this way can be tested by treating a user's watchlist (unwatched movies saved for later) as a validation set.

- The above model fulfills most requirements for a general-purpose movie recommender system. However, it is unable to make riskier recommendations for movies that a majority of reviewers do not enjoy (cult movies). To satisfy users who seek underrated movies, we also trained Doc2Vec on user review histories to create a review-based collaborative filtering model. This model does not recommend movies, but finds reviewers who write similarly to a new user. We then query the review database for positive reviews from these users, both in cases where the ratings count is 1k-10k (hidden gems), and where the reviewer rates a movie 3 stars more than the average.

The lightning-fast inferencing of the Word2Vec/Doc2vec algorithms allows us to incorporate user feedback into progressively updating recommendations. If the user elects to approve or disapprove of a movie, its corresponding vector is added to, or subtracted from, the user's overall taste vector. Weighting these feedback vectors by a factor like 1.2 increases the influence of that feedback on the user's taste vector, and this factor can be tweaked to change the effective "learning rate" of the re-recommendations process.




### Tech Stack

#### AWS:

- EC2
- S3 Bucket
- RDS
- Elastic Beanstalk

#### Machine Learning:

- [Gensim](https://radimrehurek.com/gensim/)

#### Data Collection/Manipulation:

- [Pandas](https://pypi.org/project/pandas/)
- [Numpy](https://numpy.org/)
- [SciPy](https://www.scipy.org)
- [Psycopg2](https://pypi.org/project/psycopg2)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- [Requests](https://2.python-requests.org/en/master/)

### Predictions

Based on the user's movie ratings and reviews, provide recommendations for movies to watch that they have never before considered watching. We can do this by vectorizing the user's Letterboxd or IMDb reviews and finding cosine-similar matches from 22GB worth of movie reviews. Results can be filtered to remove movies the user has already watched, so long as they provide their data exported from one of those sites.

### Data Sources

Our primary sources of data are the user reviews of IMDb.com and Letterboxd.com. This was collected from these websites with our own custom-built web scraper. In addition, we make use of [IMDb's data files](https://datasets.imdbws.com/) for summary information on films.


## Contributing
When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.

Please note we have a [code of conduct](./code_of_conduct.md.md). Please follow it in all your interactions with the project.

### Issue/Bug Request

 **If you are having an issue with the existing project code, please submit a bug report under the following guidelines:**
 - Check first to see if your issue has already been reported.
 - Check to see if the issue has recently been fixed by attempting to reproduce the issue using the latest master branch in the repository.
 - Create a live example of the problem.
 - Submit a detailed bug report including your environment & browser, steps to reproduce the issue, actual and expected outcomes,  where you believe the issue is originating from, and any potential solutions you have considered.

### Feature Requests

We would love to hear from you about new features which would improve this app and further the aims of our project. Please provide as much detail and information as possible to show us why you think your new feature should be implemented.

### Pull Requests

If you have developed a patch, bug fix, or new feature that would improve this app, please submit a pull request. It is best to communicate your ideas with the developers first before investing a great deal of time into a pull request to ensure that it will mesh smoothly with the project.

Remember that this project is licensed under the MIT license, and by submitting a pull request, you agree that your work will be, too.

#### Pull Request Guidelines

- Ensure any install or build dependencies are removed before the end of the layer when doing a build.
- Update the README.md with details of changes to the interface, including new plist variables, exposed ports, useful file locations and container parameters.
- Ensure that your code conforms to our existing code conventions and test coverage.
- Include the relevant issue number, if applicable.
- You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

### Attribution

These contribution guidelines have been adapted from [this good-Contributing.md-template](https://gist.github.com/PurpleBooth/b24679402957c63ec426).

## Documentation

See [Backend Documentation](_link to your backend readme here_) for details on the backend of our project.

See [Front End Documentation](_link to your front end readme here_) for details on the front end of our project.
