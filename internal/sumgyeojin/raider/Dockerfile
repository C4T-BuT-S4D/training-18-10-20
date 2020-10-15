FROM disconnect3d/nsjail

RUN apt -y update && apt -y install python3 python3-dev python3-pip nasm

ADD app/requirements.txt /requirements.txt

RUN python3 -m pip install -r /requirements.txt

ADD app /app

CMD ["python3", "/app/app.py"]
