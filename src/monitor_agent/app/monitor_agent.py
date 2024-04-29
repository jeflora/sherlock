import zipfile, redis, mariadb, sys
import random, string, os, datetime


data_files_directory = os.getenv("DATA_FILES_DIR", "/data_traces")
date_format = "%Y-%m-%d %H:%M:%S"


def get_db_connection():
    with open(os.getenv("DB_PASSWORD_FILE")) as fp:
        db_password = fp.read().strip()

    try:
        conn = mariadb.connect(
            user=os.getenv("DB_USER"),
            password=db_password,
            host="monitor_agent_db",
            port=3306,
            database=os.getenv("DB_DATABASE"),
        )
    except mariadb.Error as e:
        sys.exit(1)

    return conn


def generate_filename(length=15):
    letters = string.ascii_letters
    return "".join(random.choice(letters) for i in range(length))


def insert_file_metadata(conn, cur, redis_channel):
    good_filename = False
    while not good_filename:
        filename = generate_filename()
        try:
            cur.execute(
                f"insert into data_traces (app_name, file_name) values ('{redis_channel}', '{filename}')"
            )
            good_filename = True
            conn.commit()
        except:
            pass

    return filename


def update_file_metadata(
    conn, cur, file_name, begin_date, end_date, text_bytes, zip_bytes
):
    try:
        cur.execute(
            f"""update data_traces
            set begin_date = '{begin_date.strftime(date_format)}',
                end_date = '{end_date.strftime(date_format)}',
                text_bytes = {text_bytes},
                zip_bytes = {zip_bytes}
            where file_name = '{file_name}'"""
        )
        conn.commit()
    except:
        pass

    return


def persist_data_traces(redis_channel: str, return_dict):
    redis_conn = redis.StrictRedis(
        "redis_pubsub_traces", 6379, charset="utf-8", decode_responses=True
    )

    conn = get_db_connection()
    cur = conn.cursor()

    sub = redis_conn.pubsub()
    sub.subscribe(redis_channel)

    filename = insert_file_metadata(conn, cur, redis_channel)
    return_dict[redis_channel] = filename

    text_filename, zip_filename = f"{filename}.txt", f"{filename}.zip"
    text_filepath = os.path.join(data_files_directory, text_filename)
    fp = open(text_filepath, "w")

    begin_date = None
    for message in sub.listen():
        if message is not None and isinstance(message, dict):
            data = message.get("data", "")
            if not data or data == 1:
                continue
            if data == "CLOSE":
                break
            if not begin_date:
                begin_date = datetime.datetime.utcnow()
            fp.write(data)
    end_date = datetime.datetime.utcnow()
    fp.close()

    cur_dir = os.getcwd()
    os.chdir(data_files_directory)
    text_bytes = os.path.getsize(text_filename)
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as myzip:
        myzip.write(text_filename)
    os.remove(text_filename)
    zip_bytes = os.path.getsize(zip_filename)
    os.chdir(cur_dir)

    update_file_metadata(
        conn, cur, filename, begin_date, end_date, text_bytes, zip_bytes
    )
    cur.close()

    return filename
