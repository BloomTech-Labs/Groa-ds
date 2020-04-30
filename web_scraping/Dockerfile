FROM python:3.7
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
COPY BaseScraper.py FinderScraper.py LetterboxScraper.py ImdbScraper.py run_scrapers_auto.py util.py .env /
CMD ["python3", "run_scrapers_auto.py"]
