# Mercado — Sistema de Estoque

Aplicação web desenvolvida com Django para cadastro e consulta de produtos por código de barras. O sistema utiliza a câmera do dispositivo para ler códigos de barras e consulta a base Open Food Facts para preencher automaticamente as informações disponíveis do produto.

O projeto está sendo desenvolvido com foco em uma interface simples, responsiva e adequada para uso em dispositivos móveis.

https://tinyurl.com/P2mercado

https://docs.google.com/spreadsheets/d/1Myfgn3MaPbwG75cfQxyI9-Yo7xms5hTo8gEWU-vwAqE/edit?pli=1&gid=0#gid=0


## Funcionalidades

* **Cadastro de produtos:** registro de código de barras, nome, quantidade e preço.
* **Leitura de códigos de barras:** utilização da câmera do celular para identificar produtos.
* **Preenchimento automático:** consulta à API Open Food Facts para obter nome e marca do produto, quando disponíveis.
* **Consulta de estoque:** visualização dos produtos cadastrados em uma tabela, com a próxima validade de cada um.
* **Painel inicial e vencimentos:** tela de entrada com atalhos e lista dos lotes que vencem em 3, 7, 15 ou 30 dias.
* **Deploy em contêiner:** imagem Docker publicada no GHCR, para Google Cloud Run ou stack do Portainer.

## Tecnologias utilizadas

* Python
* Django
* SQLite
* HTML e CSS
* JavaScript
* [html5-qrcode](https://github.com/mebjas/html5-qrcode)
* [Open Food Facts API](https://world.openfoodfacts.org/)
* Docker
* Google Cloud Run
* Google Artifact Registry

## Estrutura do projeto

```text
config/
├── ambiente.py        # leitura tipada das variáveis de ambiente
├── settings.py
├── urls.py
└── tests/

mercado/
├── fixtures/dados_iniciais.json
├── management/commands/   # semear_dados_iniciais, criar_admin_inicial
├── migrations/
├── templates/
│   ├── base.html
│   ├── painel.html
│   ├── vencimentos.html
│   ├── stock.html
│   ├── product_form.html
│   ├── product_edit.html
│   └── scan.html
├── tests/
├── api.py
├── models.py
├── urls.py
├── vencimentos.py     # regras de validade (sem view, sem template)
├── views.py
└── views_painel.py

bin/iniciar-container.sh
.github/workflows/ci.yml
docker-compose.yml
Dockerfile
requirements.txt
manage.py
```

## Modelo de dados

O sistema utiliza o modelo `Product` para armazenar os produtos cadastrados.

| Campo      | Descrição                        |
| ---------- | -------------------------------- |
| `name`     | Nome do produto                  |
| `barcode`  | Código de barras único           |
| `quantity` | Quantidade disponível em estoque |
| `price`    | Preço do produto                 |

## Executando localmente

### 1. Pré-requisitos

* Python 3.12 ou compatível
* Git
* Pip

### 2. Clone o repositório

```bash
git https://github.com/RenatoHT/PI-2.git
cd PI-2
```

### 3. Crie e ative um ambiente virtual

No Linux ou macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

No Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores (o `.env` é ignorado pelo git).
Toda configuração que muda por ambiente — chave secreta, debug, hosts, caminho do banco —
vem de variáveis de ambiente, lidas em `config/ambiente.py`.

```bash
cp .env.example .env
```

### 6. Execute as migrações

```bash
python manage.py migrate
```

### 7. Inicie o servidor

```bash
python manage.py runserver
```

A aplicação estará disponível em:

http://127.0.0.1:8000/

Para rodar os testes:

```bash
python manage.py test
```

## Login e usuários

Todas as telas e a API exigem login. O primeiro administrador é criado na primeira subida a partir
de `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` e `DJANGO_SUPERUSER_EMAIL`. Só
administradores abrem **Usuários** (cabeçalho) para cadastrar pessoas, definir a senha de alguém
ou desativar um acesso; qualquer usuário troca a própria senha em **Minha senha**. A sessão dura
30 dias no aparelho; **Sair** encerra antes.

## Principais rotas

| Rota                      | Descrição                                 |
| ------------------------- | ----------------------------------------- |
| `/entrar/`, `/sair/`      | Login (única tela sem sessão) e saída     |
| `/senha/`                 | Trocar a própria senha                    |
| `/usuarios/`              | Gestão de usuários (só administrador)     |
| `/`                       | Painel inicial (resumo e atalhos)         |
| `/vencimentos/`           | Lotes a vencer; filtro `?dias=3|7|15|30`  |
| `/stock/`                 | Consulta de estoque com próxima validade  |
| `/stock/new/`             | Cadastro de produto e primeiro lote       |
| `/scan/`                  | Página de leitura de códigos de barras    |
| `/lookup/CODIGO/`         | Consulta de produto pelo código de barras |
| `/api/...`                | API JSON (produtos, estoque, vendas, caixa) |
| `/mercado/...`            | Prefixo antigo; redireciona (301) para a raiz |

## Consulta de produtos

O sistema utiliza a API Open Food Facts para consultar informações de produtos a partir do código de barras.

As informações retornadas dependem da disponibilidade e da qualidade dos dados cadastrados na base externa. Quando um produto não é encontrado, seus dados podem precisar ser preenchidos manualmente.

## Implantação

### Imagem Docker

A imagem é construída pelo GitHub Actions (`.github/workflows/ci.yml`) a cada push,
**depois que os testes passam**, e publicada no GHCR como
`ghcr.io/<dono>/merchant-univesp:<branch>` (também `sha-<commit>` e, na `main`, `latest`).

Dentro do contêiner roda o gunicorn, com os arquivos estáticos servidos pelo WhiteNoise.
Ao subir, `bin/iniciar-container.sh` aplica as migrações, carrega os dados iniciais
(`mercado/fixtures/dados_iniciais.json`) se o banco estiver vazio e cria o admin a partir
de `DJANGO_SUPERUSER_*` se ele ainda não existir. O banco SQLite fica em `/data` (volume).

### Stack no Portainer

1. No GitHub, torne o pacote `merchant-univesp` **público** (*Packages → Package settings →
   Change visibility*) ou cadastre as credenciais do GHCR no Portainer.
2. *Stacks → Add stack → Repository*: URL deste repositório, referência `refs/heads/<branch>`,
   compose path `docker-compose.yml`.
3. Em *Environment variables*, cadastre as variáveis descritas no `.env.example`. Obrigatórias:
   `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`. Recomendadas:
   `DJANGO_SUPERUSER_USERNAME/PASSWORD/EMAIL` (primeira subida) e `IMAGEM_TAG` (branch ou `sha-<commit>`).
4. *Deploy the stack*. Aponte o túnel ou proxy HTTPS para a porta `MERCADO_PORTA` (padrão `8080`)
   do servidor. Atrás de túnel mantenha `DJANGO_ATRAS_DE_PROXY=1` e informe o domínio com
   `https://` em `DJANGO_CSRF_TRUSTED_ORIGINS`; sem isso os formulários são recusados (CSRF).
   Sem HTTPS a câmera do celular não abre.
5. Para atualizar: aguarde o Actions ficar verde e use **Pull and redeploy** com **Re-pull image**.
   Para voltar uma versão: `IMAGEM_TAG=sha-<commit bom>` e redeploy.

O volume `dados_mercado` guarda o banco e sobrevive ao redeploy. Faça backup copiando
`/data/db.sqlite3` de dentro do contêiner.

### Rodar o contêiner na sua máquina

```bash
docker build -t merchant-univesp .
docker run --rm -p 8080:8000 --env-file .env -e DJANGO_DB_PATH=/data/db.sqlite3   -v dados_mercado:/data merchant-univesp
```

### Google Cloud Run

Continua funcionando com a mesma imagem: o servidor escuta na porta `PORT` que o Cloud Run
define. Cadastre as mesmas variáveis de ambiente no serviço.

## Observações

Este projeto está em desenvolvimento e pode receber novas funcionalidades e alterações na estrutura.
