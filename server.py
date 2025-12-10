import os
import json
import math
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

app = FastAPI()

# Configuração para permitir acesso da rede
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PASTA_DADOS = "Dados"

def carregar_tudo() -> List[Dict[str, Any]]:
    """Lê todos os JSONs da pasta e junta em uma lista única na memória."""
    lista_completa = []
    if not os.path.exists(PASTA_DADOS):
        return []
    
    for nome_arq in sorted(os.listdir(PASTA_DADOS)):
        if nome_arq.endswith(".json"):
            caminho = os.path.join(PASTA_DADOS, nome_arq)
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = json.load(f)
                    if isinstance(conteudo, list):
                        lista_completa.extend(conteudo)
                    elif isinstance(conteudo, dict) and "messages" in conteudo:
                        lista_completa.extend(conteudo["messages"])
            except Exception as e:
                print(f"Erro ao ler {nome_arq}: {e}")
    return lista_completa

# Rota 1: Entrega a página visual (HTML)
@app.get("/")
def home():
    return FileResponse("index.html")

# NOVA ROTA: Entrega o arquivo CSS
@app.get("/style.css")
def style():
    return FileResponse("style.css")

# Rota para o Favicon (PNG)
@app.get("/favicon.png")
def favicon():
    # Garante que o ficheiro existe antes de tentar entregar
    if os.path.exists("favicon.png"):
        return FileResponse("favicon.png")
    return {"error": "Imagem não encontrada"}

# Rota 2: Faz a pesquisa...
@app.get("/api/busca")
def buscar(q: str, pagina: int = 1, limite: int = 5):
    """
    Busca o termo 'q' nos campos relevantes, com dados carregados a cada requisição,
    e retorna resultados paginados.
    """
    if not q:
        return {"resultados": [], "pagina": 1, "total_paginas": 0, "total_resultados": 0}

    # Carrega os dados frescos a cada busca
    database = carregar_tudo()
    
    termo = q.lower()
    resultados_filtrados = []
    
    for item in database:
        if not isinstance(item, dict) or item.get("message_state") == "DELETED":
            continue

        creator = item.get("creator")
        nome_creator = ""
        if isinstance(creator, dict):
            nome_creator = str(creator.get("name", "")).lower()
            
        texto_mensagem = str(item.get("text", "")).lower()
        
        if termo in nome_creator or termo in texto_mensagem:
            resultados_filtrados.append(item)

    # Ordena por data de criação (mais recentes primeiro)
    resultados_filtrados.sort(key=lambda x: x.get("created_date", ""), reverse=True)

    # Lógica de paginação
    total_resultados = len(resultados_filtrados)
    total_paginas = math.ceil(total_resultados / limite)
    inicio = (pagina - 1) * limite
    fim = inicio + limite
    
    resultados_paginados = resultados_filtrados[inicio:fim]

    return {
        "resultados": resultados_paginados,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "total_resultados": total_resultados
    }