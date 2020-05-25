import gzip
from urllib.request import urlopen
import io
import pandas as pd
import numpy as np
import re

from ImdbScraper import ImdbScraper
from LetterboxScraper import LetterboxScraper

def get_ids_from_tarball():

    print("Fetching tsv...")
    path = 'https://datasets.imdbws.com/title.basics.tsv.gz'
    buf = urlopen(path)
    contents = buf.read()
    print("Got tsv")
    b = io.BytesIO(contents)
    
    with gzip.open(b) as f:
        df = pd.read_csv(f, sep="\t")

    # filter adult
    df["runtimeMinutes"] = df["runtimeMinutes"].apply(lambda x: int(x) if re.match("\d+", x) else 0)
    df = df[(df["runtimeMinutes"] >= 50) & (df["isAdult"] == 0)]

    return list(id.strip("tt") for id in df["tconst"])

step = 100
def run_scrapers(start, end):
    """
    Run the scrapers in blocks of {step}.
    """

    ids = get_ids_from_tarball()
    num_max_ids = len(ids[start:end])

    for ix in range(start, start+num_max_ids, step):

        imdb = ImdbScraper(ix, ix+step, step, ids=ids)
        imdb.update()


def run_scrapers_update(start, end):

    ids = get_ids_from_tarball()
    num_max_ids = len(ids[start:end])

    for ix in range(start, start+num_max_ids, step):
        imdb = ImdbScraper(ix, ix+step, step)
        imdb.update()
        letterbox = LetterboxScraper(ix, ix+step, step, ids=ids)
        letterbox.scrape()
