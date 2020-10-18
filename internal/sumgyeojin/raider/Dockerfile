FROM disconnect3d/nsjail

ENV PYTHONUNBUFFERED=1

RUN apt -y update && apt -y install python3 python3-dev python3-pip nasm

ADD app/requirements.txt /requirements.txt

RUN python3 -m pip install -r /requirements.txt

ADD app /app

#CMD ["python3", "/app/app.py"]

WORKDIR /app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", "--log-level", "info", "app:app"]
