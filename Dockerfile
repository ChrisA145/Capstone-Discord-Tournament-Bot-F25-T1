FROM python:3.12.0

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
# Specify the command to run the bot
CMD ["python", "tournament.py"]