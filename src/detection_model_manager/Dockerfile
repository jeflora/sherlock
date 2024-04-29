FROM python:3.11

ENV MODEL_PATH_DIR=/models_dir

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

EXPOSE 80

VOLUME [ "/code" ]
VOLUME [ "${MODEL_PATH_DIR}" ]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]