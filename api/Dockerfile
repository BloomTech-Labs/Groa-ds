FROM python:3.6
MAINTAINER Groa "groa@ctemplar.com"
RUN apt update && apt install python-dev -y
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

ENV DB_NAME=postgres
ENV DB_USER=postgres
ENV DB_PASSWORD=lambdaschoolgroa
ENV DEV=groadb-dev.cbayt2opbptw.us-east-1.rds.amazonaws.com
ENV PROD=groadb-prod.cbayt2opbptw.us-east-1.rds.amazonaws.com
ENV PORT=5432
ENV ACCESS_ID=AKIAZJ3JTPD4SNX3P4E4
ENV ACCESS_KEY=PQ4ubjMQUO8GjjBa/3+BQ3g5CpqOFBrLI8+Q1VRV
ENV BUCKET=groa-e3c8e4f6ca
ENV FOLDER=models/w2v.zip

EXPOSE 5000
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-"]
CMD ["app:app"]
