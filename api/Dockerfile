FROM python:3.7-slim-buster
LABEL maintainer="groa"

# makes and sets working directory
RUN mkdir -p /usr/src/groa
WORKDIR /usr/src/groa

# installs application dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# copies over all application files
COPY . .

# exposes port 5000
EXPOSE 5000

# runs groa_ds_api
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "--log-level", "error", "main:app"]