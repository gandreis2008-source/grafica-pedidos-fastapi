# grafica-pedidos-fastapi
Sistema de pedidos para gráfica desenvolvido com FastAPI

# 🖨️ Sistema de Pedidos para Gráfica (FastAPI)

Sistema web desenvolvido para **automatizar pedidos de impressão em gráficas**, desde o envio do arquivo até o controle administrativo do pedido.

Projeto criado com foco em **uso real**, não apenas estudo, e pensado para evolução futura como produto comercial.

---

## 🚀 Funcionalidades

### 👤 Cliente
- Upload de arquivos **PDF e DOCX**
- Cálculo automático de páginas
- Opções de impressão:
  - Preto e branco / Colorido
  - Tamanho do papel (A4, A3, A2, A1, A0)
  - Tipo de papel (Sulfite, Couchê, etc.)
  - Slides por página (A4)
- Visualização do orçamento antes da confirmação
- Confirmação do pedido sem reupload do arquivo

---

### 🧑‍💼 Painel Administrativo
- Listagem completa de pedidos
- Indicadores (KPIs):
  - Pedidos novos
  - Em produção
  - Prontos
  - Total
- Alteração de status do pedido
- Download do arquivo enviado pelo cliente
- Interface moderna (layout admin estilo SaaS)

---

## 🛠️ Tecnologias Utilizadas

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **Jinja2**
- **HTML + CSS**
- **SQLite** (ambiente local)
- **Git / GitHub**

---

## 🧠 Regras de Negócio Implementadas

- Valor calculado por **página cobrada**, não por folha física
- Frente e verso é apenas preferência (não altera valor)
- Slides por página aplicável apenas ao papel A4
- Preço do pedido é **congelado no momento da confirmação**
- Arquivo é salvo apenas uma vez e reutilizado no fluxo

---

## 📂 Estrutura do Projeto (resumo)

# 🖨️ Sistema de Pedidos para Gráfica (FastAPI)

Sistema web desenvolvido para **automatizar pedidos de impressão em gráficas**, desde o envio do arquivo até o controle administrativo do pedido.

Projeto criado com foco em **uso real**, não apenas estudo, e pensado para evolução futura como produto comercial.

---

## 🚀 Funcionalidades

### 👤 Cliente
- Upload de arquivos **PDF e DOCX**
- Cálculo automático de páginas
- Opções de impressão:
  - Preto e branco / Colorido
  - Tamanho do papel (A4, A3, A2, A1, A0)
  - Tipo de papel (Sulfite, Couchê, etc.)
  - Slides por página (A4)
- Visualização do orçamento antes da confirmação
- Confirmação do pedido sem reupload do arquivo

---

### 🧑‍💼 Painel Administrativo
- Listagem completa de pedidos
- Indicadores (KPIs):
  - Pedidos novos
  - Em produção
  - Prontos
  - Total
- Alteração de status do pedido
- Download do arquivo enviado pelo cliente
- Interface moderna (layout admin estilo SaaS)

---

## 🛠️ Tecnologias Utilizadas

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **Jinja2**
- **HTML + CSS**
- **SQLite** (ambiente local)
- **Git / GitHub**

---

## 🧠 Regras de Negócio Implementadas

- Valor calculado por **página cobrada**, não por folha física
- Frente e verso é apenas preferência (não altera valor)
- Slides por página aplicável apenas ao papel A4
- Preço do pedido é **congelado no momento da confirmação**
- Arquivo é salvo apenas uma vez e reutilizado no fluxo

---

## 📂 Estrutura do Projeto (resumo)

├── main.py
├── models.py
├── database.py
├── templates/
│ ├── pedido.html
│ └── admin/
│ ├── base.html
│ └── pedidos.html
├── static/
│ ├── admin.css
│ └── admin.js
├── utils/
│ └── file_reader.py
└── uploads/ (ignorado no Git)

---

## 🎯 Objetivo do Projeto

- Resolver um problema real de uma gráfica
- Aprender backend web com Python/FastAPI
- Criar base para um **produto comercial**
- Evoluir futuramente para:
  - Login de usuários
  - Pagamento online
  - Multi-gráficas (SaaS)

---

## 👨‍💻 Autor

Projeto desenvolvido por **Gustavo Andreis**  
📍 Brasil  
💼 Empreendedor / Desenvolvedor em aprendizado contínuo

---

## 📌 Status do Projeto

🚧 **Em desenvolvimento ativo (MVP funcional)**  
Novas funcionalidades e melhorias visuais em andamento.
