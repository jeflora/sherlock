FROM python:3.11

ENV INDEX_MAP_DIR=/index_map_dir

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./index_maps /index_map_dir

EXPOSE 80

VOLUME [ "/code" ]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]