
import os, json, sqlite3, requests, threading, time
import numpy as np
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sentence_transformers import SentenceTransformer

# Sovereign Internal Engine - Built for Prince Sultan (zopair)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
Base = declarative_base()

class Repository(Base):
    __tablename__ = "repositories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    stars = Column(Integer); forks = Column(Integer)
    description = Column(Text); embedding_vector = Column(Text)
    score = Column(Float); last_updated = Column(DateTime, default=datetime.utcnow)

engine = create_engine("sqlite:///sovereign_arsenal_final.db")
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')

def discover_logic(query):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(f"https://api.github.com/search/repositories?q={query}&sort=stars", headers=headers).json()
    db = SessionLocal()
    for item in res.get('items', []):
        desc = item['description'] or ""
        emb = model.encode(desc).tolist()
        repo = Repository(
            name=item['full_name'], stars=item['stargazers_count'],
            forks=item['forks_count'], description=desc,
            embedding_vector=json.dumps(emb),
            score=(item['stargazers_count']*0.4 + item['forks_count']*0.3)
        )
        db.merge(repo)
    db.commit(); db.close()

@app.get("/health")
def health(): return {"status": "Active"}

@app.post("/discover")
def discover(query: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(discover_logic, query)
    return {"message": "Started"}

@app.get("/repos")
def get_repos():
    db = SessionLocal()
    res = db.query(Repository).order_by(Repository.score.desc()).limit(10).all()
    db.close(); return res
