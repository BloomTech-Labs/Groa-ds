from dotenv import load_dotenv
from util import run_scrapers

load_dotenv()

run_scrapers(0, 2**31)
