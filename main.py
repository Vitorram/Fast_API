from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Importações do SQLAlchemy
from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./tarefas.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo do Banco de Dados (SQLAlchemy)
class TarefaDB(Base):
    __tablename__ = "tarefas"
    id = Column(String, primary_key=True, index=True)
    titulo = Column(String)
    descricao = Column(String, nullable=True)
    completa = Column(Boolean, default=False)

# Criar as tabelas no arquivo .db
Base.metadata.create_all(bind=engine)

# --- MODELO DE VALIDAÇÃO (Pydantic) ---
class Tarefa(BaseModel):
    id: Optional[str] = None
    titulo: str
    descricao: Optional[str] = None
    completa: bool = False

    class Config:
        from_attributes = True # Permite que o Pydantic leia dados do SQLAlchemy

# --- APP E DEPENDÊNCIAS ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Função para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS ---

@app.get("/", response_class=HTMLResponse)
def exibir_pagina_inicial(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tarefas", response_model=List[Tarefa])
def listar_tarefas(db: Session = Depends(get_db)):
    return db.query(TarefaDB).all()

@app.post("/tarefas", response_model=Tarefa, status_code=201)
def criar_tarefa(tarefa: Tarefa, db: Session = Depends(get_db)):
    nova_tarefa = TarefaDB(
        id=str(uuid4()),
        titulo=tarefa.titulo,
        descricao=tarefa.descricao,
        completa=tarefa.completa
    )
    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)
    return nova_tarefa

@app.get("/tarefas/{tarefa_id}", response_model=Tarefa)
def obter_tarefa(tarefa_id: str, db: Session = Depends(get_db)):
    tarefa = db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa

@app.put("/tarefas/{tarefa_id}", response_model=Tarefa) 
def atualizar(tarefa_id: str, tarefa_atualizada: Tarefa, db: Session = Depends(get_db)):
    db_tarefa = db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
    if not db_tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    db_tarefa.titulo = tarefa_atualizada.titulo
    db_tarefa.descricao = tarefa_atualizada.descricao
    db_tarefa.completa = tarefa_atualizada.completa
    
    db.commit()
    db.refresh(db_tarefa)
    return db_tarefa

@app.delete("/tarefas/{tarefa_id}", status_code=204)
def deletar_tarefa(tarefa_id: str, db: Session = Depends(get_db)):
    db_tarefa = db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
    if not db_tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    db.delete(db_tarefa)
    db.commit()
    return None