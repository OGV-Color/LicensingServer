# CLAUDE.md — LicensingServer

## Visão Geral

Servidor REST API em Django para gerenciamento de licenças de software. Realiza ativação, validação e revogação de licenças usando assinaturas digitais RSA. Construído para a aplicação **OGVColorCatcher**.

## Stack Tecnológica

- **Python / Django 5.2.10** — framework principal
- **Django REST Framework 3.14.0** — endpoints da API
- **PostgreSQL 18** (porta 5434) — banco de dados via psycopg2-binary
- **cryptography 46.0.5** — assinatura RSA-2048 (PKCS1v15 + SHA256)
- **python-dotenv** — carregamento de variáveis de ambiente

## Estrutura do Projeto

```
LicensingServer/
├── config/             # Configuração Django (settings, urls, wsgi, asgi)
├── licensing/          # App principal
│   ├── models.py       # Modelos License e Activation
│   ├── views.py        # Endpoints activate() e validate_license()
│   ├── urls.py         # /api/activate/ e /api/validate-license/
│   ├── admin.py        # Registro no admin do Django
│   └── utils.py        # Helper generate_license_key()
├── keys/               # Chave privada RSA (NÃO commitar — adicionar manualmente)
│   └── private_key.pem
├── requirements.txt
├── .env                # Variáveis de ambiente (desenvolvimento)
└── .env.production     # Variáveis de ambiente (produção)
```

## Configuração e Execução

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente (ver .env como referência)
# Obrigatórias: SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Gerar chave RSA (se ainda não existir)
openssl genrsa -out keys/private_key.pem 2048

# Aplicar migrations
python manage.py migrate

# Criar usuário administrador
python manage.py createsuperuser

# Iniciar servidor de desenvolvimento
python manage.py runserver
```

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django |
| `DEBUG` | `True` para dev, `False` para produção |
| `ENVIRONMENT` | `development` ou `production` |
| `DB_NAME` | Nome do banco PostgreSQL |
| `DB_USER` | Usuário do PostgreSQL |
| `DB_PASSWORD` | Senha do PostgreSQL |
| `DB_HOST` | Host do banco (ex: `localhost`) |
| `DB_PORT` | Porta do banco (padrão PostgreSQL 18: `5434`) |

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/activate/` | Ativa uma licença para um dispositivo |
| POST | `/api/validate-license/` | Valida uma licença + fingerprint |

### Ativar licença
```json
POST /api/activate/
{ "licenseKey": "XXXX-XXXX-XXXX-XXXX", "fingerprint": "<id_dispositivo>" }
```
Retorna payload JSON assinado com metadados da licença.

### Validar licença
```json
POST /api/validate-license/
{ "licenseKeyId": "XXXX-XXXX-XXXX-XXXX", "fingerprint": "<id_dispositivo>" }
```
Retorna `{ "valid": bool, "reason": string, "serverUtc": timestamp }`.

## Modelos de Dados

**License**
- `key` — chave única (formato: `XXXX-XXXX-XXXX-XXXX`)
- `customer_id` — identificador do cliente
- `max_activations` — máximo de dispositivos permitidos (padrão: 1)
- `expires_at` — data de expiração (opcional)
- `is_revoked` — flag de revogação

**Activation**
- `license` — FK para License (cascade delete)
- `fingerprint` — identificador do dispositivo
- `last_seen_at` — atualizado a cada validação
- Constraint única em `(license, fingerprint)`

## Interface Admin

Disponível em `/admin/`. Permite busca, filtragem e gerenciamento de License e Activation.

## Notas de Segurança

- A chave privada RSA (`keys/private_key.pem`) deve ser provisionada manualmente — nunca commitar.
- Os arquivos `.env` contêm segredos — não commitar credenciais no git.
- Os endpoints da API não possuem camada de autenticação — proteger via rede/firewall em produção.
- `ALLOWED_HOSTS` deve ser configurado para deploys em produção.

## Configuração do PostgreSQL (Windows)

O PostgreSQL 18 instalado com locale Português requer ajuste no `postgresql.conf` para evitar erros de encoding no psycopg2:

```
# C:\Program Files\PostgreSQL\18\data\postgresql.conf
lc_messages = 'C'
```

Após alterar, reiniciar o serviço (requer privilégios de administrador):
```powershell
Restart-Service -Name "postgresql-x64-18"
```

## Testes

```bash
python manage.py test licensing
```

Os testes ainda estão vazios — `licensing/tests.py` não possui casos implementados.
