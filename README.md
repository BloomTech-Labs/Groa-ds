# Gróa

You can check out the [live demo of Gróa here](http://www.groa.us/).

## Contributors

|                                       [Michael Gospodinoff](https://github.com/cmgospod)                                        |                                       [Gabe flomo](https://github.com/gabe-flomo)                                        |                                       [Jeff Rowe](https://github.com/Jeffrowetull)                                        |                                       [Coop Williams](https://github.com/coopwilliams)                                        |                                       [Eric Smith](https://github.com/moviedatascience)                                        |
| :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: |
|                      [<img src="https://avatars1.githubusercontent.com/u/53590416?s=400&u=1ddb3c7742a0c79a8d108b2aeff7680e32faa29e&v=4" width = "200" />](https://github.com/cmgospod)                       |                      [<img src="https://avatars0.githubusercontent.com/u/44428182?s=460&v=4" width = "200" />](https://github.com/gabe-flomo)                       |                      [<img src="https://avatars0.githubusercontent.com/u/18298291?s=460&v=4" width = "200" />](https://github.com/Jeffrowetull)                       |                      [<img src="https://avatars2.githubusercontent.com/u/6357375?s=460&v=4" width = "200" />](https://github.com/)                       |                      [<img src="https://ca.slack-edge.com/T4JUEB3ME-ULYDF6SMC-gee06200f773-512" width = "200" />](https://www.imdb.com/title/tt0047522/videoplayer/vi375194649)                       |
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

Movie Recommendation Engine will use NLP to create unique recommendations based upon the way in which users talk about movies rather than the reductive 1-5 or 1-10 rating system.


### Tech Stack

#### AWS:

- EC2
- S3 Bucket
- RDS
- Elastic Beanstalk

#### Machine Learning:

- [Gensim](https://radimrehurek.com/gensim/)
- [Sklearn](https://scikit-learn.org/stable/index.html)

#### Data Collection/Manipulation:

- [Pandas](https://pypi.org/project/pandas/)
- [Numpy](https://numpy.org/)
- [SciPy](https://www.scipy.org)
- [Psycopg2](https://pypi.org/project/psycopg2)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- [Requests](https://2.python-requests.org/en/master/)

### Predictions

Based on the user's movie ratings and reviews, provide recommendations for movies to watch that they have never before considered watching. We can do this by vectorizing the user's Letterboxd or IMDb reviews and finding cosine-similar matches from 22GB worth of movie reviews. Results can be filtered to remove movies the user has already watched, so long as they provide their data exported from one of those sites.

###  Explanatory Variables

-   Explanatory Variable 1
-   Explanatory Variable 2
-   Explanatory Variable 3
-   Explanatory Variable 4
-   Explanatory Variable 5

### Data Sources
🚫  Add to or delete souce links as needed for your project


-   [IMDb data files](https://datasets.imdbws.com/)
-   [Source 2](🚫add link to python notebook here)
-   [Source 3](🚫add link to python notebook here)
-   [Source 4](🚫add link to python notebook here)
-   [Source 5](🚫add link to python notebook here)

### Python Notebooks

🚫  Add to or delete python notebook links as needed for your project

[Python Notebook 1](🚫add link to python notebook here)

[Python Notebook 2](🚫add link to python notebook here)

[Python Notebook 3](🚫add link to python notebook here)

### 3️⃣ How to connect to the web API

🚫 List directions on how to connect to the API here

### 3️⃣ How to connect to the data API

🚫 List directions on how to connect to the API here

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
