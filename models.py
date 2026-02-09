from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func, UniqueConstraint
from database import Base


class Preco(Base):
    __tablename__ = "precos"

    id = Column(Integer, primary_key=True, index=True)

    # "preto e branco" | "colorido"
    tipo_cor = Column(String(50), index=True, nullable=False)

    # "A4" | "A3" | "A2" | "A1" | "A0"
    tamanho_papel = Column(String(10), index=True, nullable=False)

    # "Normal (Sulfite 75g)" | "Couchê (foto 120g)" | "Couchê (foto 180g)"
    tipo_papel = Column(String(50), index=True, nullable=False)

    preco_pagina = Column(Float, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tipo_cor", "tamanho_papel", "tipo_papel", name="uq_preco_combo"),
    )


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)

    # escolha do cliente
    tipo_cor = Column(String(50), index=True, nullable=False)
    tamanho_papel = Column(String(10), index=True, nullable=False)
    tipo_papel = Column(String(50), nullable=False)

    slides_por_pagina = Column(Integer, nullable=False, default=1)  # 1,2,4,6 (só A4)
    frente_verso = Column(Boolean, nullable=False, default=False)   # só informação (não altera valor)

    paginas_arquivo = Column(Integer, nullable=False)
    copias = Column(Integer, nullable=False)

    # o que será cobrado (após aplicar slides_por_pagina quando A4)
    paginas_cobradas = Column(Integer, nullable=False)

    # valores congelados no pedido (não mudam quando preço muda)
    preco_pagina_usado = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)

    # extras
    descricao = Column(String(700), nullable=True)
    grampear = Column(Boolean, nullable=False, default=False)
    encadernar = Column(Boolean, nullable=False, default=False)
    plastificar = Column(Boolean, nullable=False, default=False)

    arquivo = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="novo")
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
