from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="API Exemplo", version="1.0")

# -----------------------------
# Modelos (Pydantic)
# -----------------------------
class ProdutoIn(BaseModel):
    nome: str
    preco: float


class ProdutoOut(BaseModel):
    id: int
    nome: str
    preco: float


class UsuarioIn(BaseModel):
    nome: str
    email: str


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str


# -----------------------------
# "Banco" em memória
# -----------------------------
produtos: list[ProdutoOut] = []
produto_id_seq = 1

usuarios: list[UsuarioOut] = []
usuario_id_seq = 1


# -----------------------------
# 1) Endpoints básicos
# -----------------------------
@app.get("/")
def root():
    return {"message": "API funcionando"}


@app.get("/status")
def status():
    return {"status": "online", "version": "1.0"}


# -----------------------------
# 2) Parâmetros de rota
# -----------------------------
@app.get("/alunos/{nome}")
def aluno(nome: str):
    # Pelo enunciado, sempre retorna esse JSON fixo (independente do nome)
    return {"aluno": "Victor", "disciplina": "Tecnologias e Programação Integrada"}


# -----------------------------
# 3) Query Parameters
# -----------------------------
@app.get("/media")
def calcular_media(nota1: float, nota2: float):
    media = (nota1 + nota2) / 2
    situacao = "Aprovado" if media >= 7 else "Reprovado"
    return {"media": media, "situacao": situacao}


# -----------------------------
# 4) Criar recurso via POST (produtos)
# -----------------------------
@app.post("/produtos", response_model=ProdutoOut)
def criar_produto(dados: ProdutoIn):
    global produto_id_seq

    novo = ProdutoOut(id=produto_id_seq, nome=dados.nome, preco=dados.preco)
    produtos.append(novo)
    produto_id_seq += 1
    return novo


# -----------------------------
# 5) CRUD completo (usuários)
# -----------------------------
@app.post("/usuarios", response_model=UsuarioOut, status_code=201)
def criar_usuario(dados: UsuarioIn):
    global usuario_id_seq

    novo = UsuarioOut(id=usuario_id_seq, nome=dados.nome, email=dados.email)
    usuarios.append(novo)
    usuario_id_seq += 1
    return novo


@app.get("/usuarios", response_model=list[UsuarioOut])
def listar_usuarios():
    return usuarios


@app.get("/usuarios/{id}", response_model=UsuarioOut)
def obter_usuario(id: int):
    for u in usuarios:
        if u.id == id:
            return u
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


@app.put("/usuarios/{id}", response_model=UsuarioOut)
def atualizar_usuario(id: int, dados: UsuarioIn):
    for i, u in enumerate(usuarios):
        if u.id == id:
            atualizado = UsuarioOut(id=id, nome=dados.nome, email=dados.email)
            usuarios[i] = atualizado
            return atualizado
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


@app.delete("/usuarios/{id}", status_code=204)
def deletar_usuario(id: int):
    for i, u in enumerate(usuarios):
        if u.id == id:
            usuarios.pop(i)
            return
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


# -----------------------------
# 6) Consumindo API pública (Agify)
# -----------------------------
@app.get("/previsao-idade/{nome}")
def previsao_idade(nome: str):
    try:
        resp = requests.get("https://api.agify.io", params={"name": nome}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {"nome": nome, "idade_prevista": data.get("age")}
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Erro ao consultar a API Agify")


# -----------------------------
# 7) Proxy de API (ViaCEP)
# -----------------------------
@app.get("/cep/{cep}")
def buscar_cep(cep: str):
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("erro") is True:
            raise HTTPException(status_code=404, detail="CEP não encontrado")

        return {
            "logradouro": data.get("logradouro"),
            "bairro": data.get("bairro"),
            "cidade": data.get("localidade"),
            "estado": data.get("uf"),
        }
    except HTTPException:
        raise
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Erro ao consultar a API ViaCEP")