FROM python:3

WORKDIR /services/not_twitter

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "gunicorn", "--bind", "0.0.0.0:3113", "wsgi:app" ]