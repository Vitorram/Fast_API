from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI(title="Carros API",
    description="API para controle de inventário de veículos com persistência em SQLite",
    version="1.0.0")

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---

def get_db_connection():
    """Abre a conexão com o banco de dados SQLite."""
    conn = sqlite3.connect('garagem.db')
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome (ex: carro['marca'])
    return conn

def init_db():
    """Cria a tabela se ela não existir. (Corrigido 'TEST' para 'TEXT')"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS carros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            imagem_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Inicializa o banco ao rodar o arquivo
init_db()

# --- CONFIGURAÇÕES DO FASTAPI ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- ROTAS (ENDPOINTS) ---

# 1. LISTAR E BUSCAR (GET)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, buscar_marca: str = Query(None)):
    conn = get_db_connection()
    if buscar_marca:
        comando = "SELECT * FROM carros WHERE marca LIKE ?"
        cursor = conn.execute(comando, (f'%{buscar_marca}%',))
        resultados = cursor.fetchall()
    else:
        cursor = conn.execute('SELECT * FROM carros')
        resultados = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cars": resultados,
        "termo_buscado": buscar_marca
    })

# 2. CADASTRAR (POST) - (Ajustado parênteses do execute)
@app.post("/carros", status_code=201)
async def cadastrar_carro(
    marca: str = Form(...),
    modelo: str = Form(...),
    ano: int = Form(...),
    imagem_url: str = Form(...)
):
    conn = get_db_connection()
    comando = 'INSERT INTO carros (marca, modelo, ano, imagem_url) VALUES (?, ?, ?, ?)'
    # Correção: comando e valores são argumentos SEPARADOS no execute
    conn.execute(comando, (marca, modelo, ano, imagem_url))
    conn.commit()
    conn.close()
    return RedirectResponse(url='/', status_code=303)

# 3. PÁGINA DE EDIÇÃO (GET)
@app.get("/editar/{car_id}", response_class=HTMLResponse)
async def pagina_editar(request: Request, car_id: int):
    conn = get_db_connection()
    carro = conn.execute('SELECT * FROM carros WHERE id = ?', (car_id,)).fetchone()
    conn.close()
    
    if carro is None:
        return RedirectResponse(url="/")
        
    return templates.TemplateResponse("editar.html", {"request": request, "car": carro})

# 4. SALVAR EDIÇÃO (PUT)
@app.put("/carros/{car_id}")
async def atualizar_carro(car_id: int, dados: dict):
    conn = get_db_connection()
    comando = '''
        UPDATE carros 
        SET marca = ?, modelo = ?, ano = ?, imagem_url = ? 
        WHERE id = ?
    '''
    conn.execute(comando, (
        dados['marca'], 
        dados['modelo'], 
        dados['ano'], 
        dados['imagem_url'], 
        car_id
    ))
    conn.commit()
    conn.close()
    return {"status": "sucesso"}

# 5. DELETAR (DELETE) - (Ajustado vírgula na tupla)
@app.delete("/carros/{car_id}", status_code=204)
async def deletar_carro(car_id: int):
    conn = get_db_connection()
    # Correção: O SQLite exige uma vírgula para identificar uma tupla de um item só
    conn.execute('DELETE FROM carros WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    return None