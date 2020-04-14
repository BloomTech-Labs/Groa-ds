import dotenv

from ImdbScraper import ImdbScraper
from LetterboxScraper import LetterboxScraper
from FinderScraper import FinderScraper

def checker(str):
    """
    Quick utility function to help with our input Q&A
    """
    valid_inputs = ['y', 'yes', 'n', 'no']
    var = input(str).lower()
    while not var in valid_inputs:
        print("Valid inputs for this question are y, n, yes, and no.")
        var = input(str).lower()
    return var

if __name__ == "__main__":
    dotenv.load_dotenv()

    start = int(input("Start at which row? "))
    end = int(input("End at which row? (Inclusive)"))
    if start > end:
        raise ValueError("The starting position needs to be less than or \
equal to the end position.")
    max_iter = int(input("Maximum iterations? "))
    if max_iter < 1:
        raise ValueError("Maximum iterations must be positive.")

    imdb = ImdbScraper(start, end, max_iter)
    letterbox = LetterboxScraper(start, end, max_iter)
    finder = FinderScraper(start, end, max_iter)

    website = checker("Are you scraping IMDB?")
    if website == "y" or website == "yes":
        update = checker("Do you want to reject reviews already \
in the database?")
        if update == "y" or update == "yes":
            imdb.update()
        elif update == "n" or update == "no":
            imdb.scrape()
    elif website == "n" or website == "no":
        website2 = checker("Are you scraping Letterboxd?")
        if website2 == "y" or website2 == "yes":
            letterbox.scrape()
        elif website2 == "n" or website2 == "no":
            finder.scrape()
