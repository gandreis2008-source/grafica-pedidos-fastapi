import os
import math
import shutil

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from sqlalchemy import or_
from typing import Optional
from fastapi.staticfiles import StaticFiles
from database import SessionLocal, engine, Base
from models import Preco, Pedido
from utils.file_reader import contar_paginas_pdf, contar_paginas_docx

app = FastAPI(title="API da Gráfica")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------- DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- helpers ----------
def str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "on", "yes", "sim"}


def normalizar_tipo_cor(valor: str) -> str:
    v = (valor or "").strip().lower()
    mapa = {
        "pb": "preto e branco",
        "p/b": "preto e branco",
        "preto e branco": "preto e branco",
        "color": "colorido",
        "colorido": "colorido",
    }
    return mapa.get(v, v)


def normalizar_tamanho_papel(valor: str) -> str:
    v = (valor or "").strip().upper()
    validos = {"A4", "A3", "A2", "A1", "A0"}
    return v if v in validos else "A4"


def normalizar_tipo_papel(valor: str) -> str:
    v = (valor or "").strip()
    validos = {
        "Normal (Sulfite 75g)",
        "Couchê (foto 120g)",
        "Couchê (foto 180g)",
    }
    return v if v in validos else "Normal (Sulfite 75g)"


def contar_paginas_por_arquivo(caminho: str, filename: str) -> int:
    name = filename.lower()
    if name.endswith(".pdf"):
        return contar_paginas_pdf(caminho)
    if name.endswith(".docx"):
        return contar_paginas_docx(caminho)
    raise ValueError("Formato não suportado (use .pdf ou .docx)")


def calcular_paginas_cobradas(paginas_arquivo: int, copias: int, tamanho_papel: str, slides_por_pagina: int) -> int:
    """
    Regra:
    - Slides por página só vale no A4
    - páginas_cobradas = ceil(paginas_arquivo / slides_por_pagina) * copias
    - frente_verso NÃO entra no cálculo (só informação)
    """
    tamanho_papel = normalizar_tamanho_papel(tamanho_papel)

    if tamanho_papel != "A4":
        slides_por_pagina = 1

    slides_por_pagina = int(slides_por_pagina)
    if slides_por_pagina not in {1, 2, 4, 6}:
        slides_por_pagina = 1

    por_copia = math.ceil(paginas_arquivo / slides_por_pagina)
    return por_copia * int(copias)


# ---------- routes ----------
@app.get("/")
def home():
    return {"msg": "API da gráfica rodando 🚀"}


# -------------------------
# ADMIN PREÇOS (editáveis)
# -------------------------

@app.post("/admin/preco")
def upsert_preco(
    tipo_cor: str = Form(...),
    tamanho_papel: str = Form(...),
    tipo_papel: str = Form(...),
    preco_pagina: float = Form(...),
    ativo: str = Form("true"),
    db: Session = Depends(get_db),
):
    tipo_cor = normalizar_tipo_cor(tipo_cor)
    tamanho_papel = normalizar_tamanho_papel(tamanho_papel)
    tipo_papel = normalizar_tipo_papel(tipo_papel)
    is_ativo = str_to_bool(ativo)

    preco = db.query(Preco).filter(
        Preco.tipo_cor == tipo_cor,
        Preco.tamanho_papel == tamanho_papel,
        Preco.tipo_papel == tipo_papel
    ).first()

    if preco:
        preco.preco_pagina = float(preco_pagina)
        preco.ativo = is_ativo
    else:
        preco = Preco(
            tipo_cor=tipo_cor,
            tamanho_papel=tamanho_papel,
            tipo_papel=tipo_papel,
            preco_pagina=float(preco_pagina),
            ativo=is_ativo
        )
        db.add(preco)

    db.commit()
    return {
        "msg": "Preço salvo/atualizado com sucesso",
        "tipo_cor": tipo_cor,
        "tamanho_papel": tamanho_papel,
        "tipo_papel": tipo_papel,
        "preco_pagina": float(preco_pagina),
        "ativo": is_ativo
    }


@app.get("/admin/precos")
def listar_precos(db: Session = Depends(get_db)):
    precos = db.query(Preco).order_by(Preco.tipo_cor, Preco.tamanho_papel, Preco.tipo_papel).all()
    return [
        {
            "tipo_cor": p.tipo_cor,
            "tamanho_papel": p.tamanho_papel,
            "tipo_papel": p.tipo_papel,
            "preco_pagina": p.preco_pagina,
            "ativo": p.ativo,
        }
        for p in precos
    ]


# -------------------------
# FORMULÁRIO
# -------------------------
@app.get("/pedido", response_class=HTMLResponse)
def formulario_pedido(request: Request):
    return templates.TemplateResponse("pedido.html", {"request": request})


# -------------------------
# ORÇAMENTO (HTML)
# -------------------------
@app.post("/confirmar-pedido", response_class=HTMLResponse)
def confirmar_pedido(
    request: Request,
    tipo_cor: str = Form(...),
    tamanho_papel: str = Form("A4"),
    tipo_papel: str = Form("Normal (Sulfite 75g)"),
    slides_por_pagina: int = Form(1),
    copias: int = Form(...),
    frente_verso: str = Form("false"),
    descricao: str = Form(""),
    grampear: str = Form("false"),
    encadernar: str = Form("false"),
    plastificar: str = Form("false"),
    arquivo_nome: str = Form(...),
    db: Session = Depends(get_db),
):
    tipo_cor = normalizar_tipo_cor(tipo_cor)
    tamanho_papel = normalizar_tamanho_papel(tamanho_papel)
    tipo_papel = normalizar_tipo_papel(tipo_papel)

    is_frente_verso = str_to_bool(frente_verso)
    b_grampear = str_to_bool(grampear)
    b_encadernar = str_to_bool(encadernar)
    b_plastificar = str_to_bool(plastificar)
    descricao = (descricao or "").strip()

    caminho = os.path.join(UPLOAD_DIR, arquivo_nome)
    if not os.path.exists(caminho):
        return HTMLResponse("Arquivo não encontrado. Refaça o orçamento e tente novamente.", status_code=400)

    paginas_arquivo = contar_paginas_por_arquivo(caminho, arquivo_nome)

    paginas_cobradas = calcular_paginas_cobradas(
        paginas_arquivo=paginas_arquivo,
        copias=copias,
        tamanho_papel=tamanho_papel,
        slides_por_pagina=slides_por_pagina,
    )

    preco = db.query(Preco).filter(
        Preco.tipo_cor == tipo_cor,
        Preco.tamanho_papel == tamanho_papel,
        Preco.tipo_papel == tipo_papel,
        Preco.ativo == True
    ).first()

    if not preco:
        return HTMLResponse(
            f"Preço não cadastrado para: {tipo_cor} + {tamanho_papel} + {tipo_papel}.",
            status_code=400
        )

    preco_pagina_usado = float(preco.preco_pagina)
    valor_total = paginas_cobradas * preco_pagina_usado

    pedido = Pedido(
        tipo_cor=tipo_cor,
        tamanho_papel=tamanho_papel,
        tipo_papel=tipo_papel,
        slides_por_pagina=slides_por_pagina if tamanho_papel == "A4" else 1,
        frente_verso=is_frente_verso,
        paginas_arquivo=paginas_arquivo,
        copias=copias,
        paginas_cobradas=paginas_cobradas,
        preco_pagina_usado=preco_pagina_usado,
        valor_total=valor_total,
        descricao=descricao if descricao else None,
        grampear=b_grampear,
        encadernar=b_encadernar,
        plastificar=b_plastificar,
        arquivo=arquivo_nome,
        status="novo"
    )

    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    return templates.TemplateResponse(
        "confirmado.html",
        {"request": request, "pedido_id": pedido.id, "valor_total": pedido.valor_total}
    )

@app.post("/mostrar-orcamento", response_class=HTMLResponse)
def mostrar_orcamento(
    request: Request,
    tipo_cor: str = Form(...),
    tamanho_papel: str = Form("A4"),
    tipo_papel: str = Form("Normal (Sulfite 75g)"),
    slides_por_pagina: int = Form(1),
    copias: int = Form(...),
    frente_verso: str = Form("false"),
    descricao: str = Form(""),
    grampear: str = Form("false"),
    encadernar: str = Form("false"),
    plastificar: str = Form("false"),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        tipo_cor = normalizar_tipo_cor(tipo_cor)
        tamanho_papel = normalizar_tamanho_papel(tamanho_papel)
        tipo_papel = normalizar_tipo_papel(tipo_papel)

        is_frente_verso = str_to_bool(frente_verso)  # só informação
        b_grampear = str_to_bool(grampear)
        b_encadernar = str_to_bool(encadernar)
        b_plastificar = str_to_bool(plastificar)
        descricao = (descricao or "").strip()

        caminho = os.path.join(UPLOAD_DIR, arquivo.filename)
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        paginas_arquivo = contar_paginas_por_arquivo(caminho, arquivo.filename)

        paginas_cobradas = calcular_paginas_cobradas(
            paginas_arquivo=paginas_arquivo,
            copias=copias,
            tamanho_papel=tamanho_papel,
            slides_por_pagina=slides_por_pagina,
        )

        preco = db.query(Preco).filter(
            Preco.tipo_cor == tipo_cor,
            Preco.tamanho_papel == tamanho_papel,
            Preco.tipo_papel == tipo_papel,
            Preco.ativo == True
        ).first()

        if not preco:
            return HTMLResponse(
                f"Preço não cadastrado para: {tipo_cor} + {tamanho_papel} + {tipo_papel}. Cadastre em /docs -> POST /admin/preco.",
                status_code=400
            )

        preco_pagina = float(preco.preco_pagina)
        valor_total = paginas_cobradas * preco_pagina

        return templates.TemplateResponse(
            "orcamento.html",
            {
                "request": request,
                "tipo_cor": tipo_cor,
                "tamanho_papel": tamanho_papel,
                "tipo_papel": tipo_papel,
                "slides_por_pagina": slides_por_pagina if tamanho_papel == "A4" else 1,
                "paginas_arquivo": paginas_arquivo,
                "copias": copias,
                "paginas_cobradas": paginas_cobradas,
                "frente_verso": is_frente_verso,
                "descricao": descricao,
                "grampear": b_grampear,
                "encadernar": b_encadernar,
                "plastificar": b_plastificar,
                "preco_pagina": preco_pagina,
                "valor_total": valor_total,
                "arquivo_nome": arquivo.filename,
                
            }
        )

    except Exception as e:
        return HTMLResponse(f"Erro ao calcular orçamento: {e}", status_code=400)


# -------------------------
# ORÇAMENTO (JSON) - opcional, útil pra testes
# -------------------------
@app.post("/orcamento")
def orcamento_json(
    tipo_cor: str = Form(...),
    tamanho_papel: str = Form("A4"),
    tipo_papel: str = Form("Normal (Sulfite 75g)"),
    slides_por_pagina: int = Form(1),
    copias: int = Form(...),
    frente_verso: str = Form("false"),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    tipo_cor = normalizar_tipo_cor(tipo_cor)
    tamanho_papel = normalizar_tamanho_papel(tamanho_papel)
    tipo_papel = normalizar_tipo_papel(tipo_papel)

    caminho = os.path.join(UPLOAD_DIR, arquivo.filename)
    with open(caminho, "wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)

    try:
        paginas_arquivo = contar_paginas_por_arquivo(caminho, arquivo.filename)
    except ValueError as e:
        return JSONResponse({"erro": str(e)}, status_code=400)

    paginas_cobradas = calcular_paginas_cobradas(paginas_arquivo, copias, tamanho_papel, slides_por_pagina)

    preco = db.query(Preco).filter(
        Preco.tipo_cor == tipo_cor,
        Preco.tamanho_papel == tamanho_papel,
        Preco.tipo_papel == tipo_papel,
        Preco.ativo == True
    ).first()

    if not preco:
        return JSONResponse(
            {"erro": f"Preço não cadastrado para {tipo_cor} + {tamanho_papel} + {tipo_papel}"},
            status_code=400
        )

    preco_pagina = float(preco.preco_pagina)
    valor_total = paginas_cobradas * preco_pagina

    return {
        "tipo_cor": tipo_cor,
        "tamanho_papel": tamanho_papel,
        "tipo_papel": tipo_papel,
        "paginas_arquivo": paginas_arquivo,
        "slides_por_pagina": slides_por_pagina if tamanho_papel == "A4" else 1,
        "copias": copias,
        "paginas_cobradas": paginas_cobradas,
        "frente_verso": str_to_bool(frente_verso),
        "preco_pagina": preco_pagina,
        "valor_total": valor_total,
    }


# -------------------------
# CRIAR PEDIDO (salva e congela preço usado)
# -------------------------
@app.post("/pedido-criar")
def criar_pedido(
    tipo_cor: str = Form(...),
    tamanho_papel: str = Form("A4"),
    tipo_papel: str = Form("Normal (Sulfite 75g)"),
    slides_por_pagina: int = Form(1),
    copias: int = Form(...),
    frente_verso: str = Form("false"),
    descricao: str = Form(""),
    grampear: str = Form("false"),
    encadernar: str = Form("false"),
    plastificar: str = Form("false"),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    tipo_cor = normalizar_tipo_cor(tipo_cor)
    tamanho_papel = normalizar_tamanho_papel(tamanho_papel)
    tipo_papel = normalizar_tipo_papel(tipo_papel)

    is_frente_verso = str_to_bool(frente_verso)  # só informação
    b_grampear = str_to_bool(grampear)
    b_encadernar = str_to_bool(encadernar)
    b_plastificar = str_to_bool(plastificar)
    descricao = (descricao or "").strip()

    caminho = os.path.join(UPLOAD_DIR, arquivo.filename)
    with open(caminho, "wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)

    try:
        paginas_arquivo = contar_paginas_por_arquivo(caminho, arquivo.filename)
    except ValueError as e:
        return JSONResponse({"erro": str(e)}, status_code=400)

    paginas_cobradas = calcular_paginas_cobradas(paginas_arquivo, copias, tamanho_papel, slides_por_pagina)

    preco = db.query(Preco).filter(
        Preco.tipo_cor == tipo_cor,
        Preco.tamanho_papel == tamanho_papel,
        Preco.tipo_papel == tipo_papel,
        Preco.ativo == True
    ).first()

    if not preco:
        return JSONResponse(
            {"erro": f"Preço não cadastrado para {tipo_cor} + {tamanho_papel} + {tipo_papel}"},
            status_code=400
        )

    preco_pagina_usado = float(preco.preco_pagina)
    valor_total = paginas_cobradas * preco_pagina_usado

    pedido = Pedido(
        tipo_cor=tipo_cor,
        tamanho_papel=tamanho_papel,
        tipo_papel=tipo_papel,
        slides_por_pagina=slides_por_pagina if tamanho_papel == "A4" else 1,
        frente_verso=is_frente_verso,
        paginas_arquivo=paginas_arquivo,
        copias=copias,
        paginas_cobradas=paginas_cobradas,
        preco_pagina_usado=preco_pagina_usado,
        valor_total=valor_total,
        descricao=descricao if descricao else None,
        grampear=b_grampear,
        encadernar=b_encadernar,
        plastificar=b_plastificar,
        arquivo=arquivo.filename,
        status="novo"
    )

    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    return {
        "msg": "Pedido criado com sucesso",
        "pedido_id": pedido.id,
        "valor_total": pedido.valor_total,
        "preco_pagina_usado": pedido.preco_pagina_usado,
        "paginas_cobradas": pedido.paginas_cobradas
    }
from typing import Optional
from sqlalchemy import or_

@app.get("/admin/pedidos", response_class=HTMLResponse)
def admin_pedidos(
    request: Request,
    status: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Pedido)

    # filtro por status
    if status:
        query = query.filter(Pedido.status == status)

    # busca por texto (arquivo ou descrição)
    if q:
        texto = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Pedido.descricao.ilike(texto),
                Pedido.arquivo.ilike(texto),
            )
        )

    pedidos = query.order_by(Pedido.id.desc()).all()

    # KPIs (contadores do topo)
    kpis = {
        "novo": db.query(Pedido).filter(Pedido.status == "novo").count(),
        "em_producao": db.query(Pedido).filter(Pedido.status == "em_producao").count(),
        "pronto": db.query(Pedido).filter(Pedido.status == "pronto").count(),
        "total": db.query(Pedido).count(),
    }

    return templates.TemplateResponse(
        "admin/pedidos.html",
        {
            "request": request,
            "pedidos": pedidos,
            "kpis": kpis,
            "status": status,
            "q": q,
            "nav": "pedidos",
        }
    )
@app.post("/admin/pedido/status")
def atualizar_status_pedido(
    pedido_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()

    if not pedido:
        return {"erro": "Pedido não encontrado"}

    pedido.status = status
    db.commit()

    return {"msg": "Status atualizado com sucesso"}



