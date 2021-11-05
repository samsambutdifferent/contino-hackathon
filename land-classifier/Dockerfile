FROM python:3.7-slim

WORKDIR /app

# Copy list of dependencies
COPY ./requirements.txt .

# Install dependencies first
RUN pip3 install -r requirements.txt --no-cache-dir

# Copy app code
# This is in a later step so a layer with the Python dependencies can be cached
# This will speed up local development dramatically
COPY /app .

# Open port 8080 for serving the webpage
EXPOSE 8080

# Do not use root user
RUN adduser python --disabled-password

# Set permissions
RUN chown -R python:python /app

USER python

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "1", "--timeout", "0", "app:app"]