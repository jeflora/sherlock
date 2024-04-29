from http import HTTPStatus
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import requests


router = APIRouter()


@router.get("/reactive", tags=["reactive"])
def get_rea():
    return {}
