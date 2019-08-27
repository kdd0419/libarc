FROM python:latest

COPY . .

RUN pip install -r requirements.txt
RUN pip install discord
RUN pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
RUN pip install asyncio

CMD ["python", "discord_bot.py"]

# docker build -t 이름 .
# docker run 이름 