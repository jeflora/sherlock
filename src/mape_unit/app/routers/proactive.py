from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import requests


router = APIRouter()


@router.get("/proactive", tags=["proactive"])
def get_pro():
    return {}