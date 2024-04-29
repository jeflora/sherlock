from fastapi import FastAPI

from app.routers import reactive, proactive
from app.reactive import measure as react
from app.proactive import measure as proact


app = FastAPI(title="MAPE UNIT")
app.include_router(proactive.router)
app.include_router(reactive.router)


reactor = react.ReactiveMeasure()
proactor = proact.ProactiveMeasure()
reactor.start()
proactor.start()



@app.get("/")
@app.get("/home")
async def root():
    return {"msg": "OK"}
