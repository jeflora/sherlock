FROM python:3.11

WORKDIR /code

ENV DAEMON_HOST=k8s_daemon
ENV DAEMON_PORT=80

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 80

VOLUME [ "/code" ]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]