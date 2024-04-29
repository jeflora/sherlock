from fastapi import FastAPI, BackgroundTasks, HTTPException
import requests
import mariadb, sys, os, glob
import app.monitor_agent as monitor_agent
import multiprocessing

from http import HTTPStatus
from typing import Dict, Optional
from pydantic import BaseModel


class Job(BaseModel):
    app_name: str = None
    status: str = "in_progress"
    created_filename: str = None


app = FastAPI(title="MONITOR AGENT")
jobs: Dict[str, Job] = {}
procs: Dict[str, multiprocessing.Process] = {}

data_files_directory = os.getenv("DATA_FILES_DIR", "/data_traces")

def get_db_connection():
    with open(os.getenv('DB_PASSWORD_FILE')) as fp:
        db_password = fp.read().strip()

    try:
        conn = mariadb.connect(
            user=os.getenv('DB_USER'),
            password=db_password,
            host="monitor_agent_db",
            port=3306,
            database=os.getenv('DB_DATABASE')

        )
        # conn.autocommit = False # True by defaulf
    except mariadb.Error as e:
        # print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    
    return conn


def start_monitoring_unit(app_name: str) -> None:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    procs[app_name] = multiprocessing.Process(target=monitor_agent.persist_data_traces, args=(app_name, return_dict))
    procs[app_name].start()
    procs[app_name].join()
    jobs[app_name].created_filename = return_dict.get(app_name)
    jobs[app_name].status = "complete"


@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}


@app.post("/monitoring/init_data_receiver/{app_name}", status_code=HTTPStatus.ACCEPTED, tags=["monitoring"])
async def init_data_receiver(app_name: str, background_tasks: BackgroundTasks):
    if app_name in jobs and jobs[app_name].status == "in_progress":
        return jobs[app_name]
    
    new_monitoring_unit = Job()
    jobs[app_name] = new_monitoring_unit
    jobs[app_name].app_name = app_name
    background_tasks.add_task(start_monitoring_unit, app_name)
    return new_monitoring_unit


@app.delete("/monitoring/data_receiver/{app_name}", status_code=HTTPStatus.OK, tags=["monitoring"])
async def stop_data_receiver(app_name: str, background_tasks: BackgroundTasks):
    procs[app_name].terminate()
    jobs[app_name].status = "complete"
    return jobs[app_name]


@app.get("/monitoring/status/{app_name}", status_code=HTTPStatus.OK, tags=["monitoring"])
async def status_handler(app_name: str):
    if app_name not in jobs:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=f"Monitoring unit {app_name} not found."
        ) 
    return jobs[app_name]


@app.get("/traces", tags=["traces"], status_code=HTTPStatus.OK)
async def get_traces_list(cluster_name: Optional[str] = None):
    filters = ""
    cluster_apps = []
    if cluster_name:
        resp = requests.get(f"http://management_engine/cluster/{cluster_name}/app_names")
        if resp.status_code >= 400:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Could not satisfy request.")
        cluster_apps = resp.json()
        filters = " where " + " or ".join(["app_name = %s" for _ in range(len(cluster_apps))])

        if not cluster_apps:
            return []

    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cur:
        cur.execute(f"select * from data_traces{filters}", cluster_apps)
        rows = cur.fetchall()
    return rows


@app.delete("/traces/{file_id}", tags=["traces"], status_code=HTTPStatus.OK)
async def delete_trace_file(file_id: int):
    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cur:
        cur.execute("select file_name from data_traces where file_id = %s", (file_id,))
        rows = cur.fetchone()
        if not rows:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"File id {file_id} not found."
            )
        filepath = os.path.join(data_files_directory, rows["file_name"])
        for file in glob.glob(f"{filepath}.*"):
            os.remove(file)
        cur.execute("delete from data_traces where file_id = %s", (file_id,))
        conn.commit()

    return {"msg": "OK", "id": file_id}