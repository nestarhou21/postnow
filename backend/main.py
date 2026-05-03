"""
main.py — POSTNOW FastAPI application entry point
"""
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db
from routes.auth import router as auth_router
from routes.profile import router as profile_router
from routes.generate import router as generate_router

app = FastAPI(title="POSTNOW API", version="1.0.0")

# Allow Vue.js dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(generate_router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "POSTNOW API running"}
