# 🔐 Entendendo o Sistema de Tokens da API Hinova

## 📖 Como Funciona (Explicação Completa)

### 🎯 Dois Tipos de Token

A API Hinova usa **2 tokens diferentes**:

1. **Bearer Token** (Fixo)
   - Você cria no painel da Hinova
   - É permanente (até você excluir)
   - Usado para AUTENTICAR
   - Exemplo: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

2. **User Token** (Temporário)
   - Você recebe da API após autenticar
   - É temporário (expira em ~1 hora)
   - Usado para FAZER REQUISIÇÕES
   - Exemplo: `AbCdEf1234567890XyZ...`

---

## 🔄 Fluxo Correto

### Passo 1: Autenticação

```http
POST https://api.hinova.com.br/api/sga/v2/usuario/autenticar

Headers:
  Authorization: Bearer SEU_BEARER_TOKEN_FIXO

Body:
{
  "usuario": "seu_usuario",
  "senha": "sua_senha"
}

Resposta:
{
  "token": "AbCdEf1234567890XyZ...",  ← USER TOKEN (temporário)
  "nome": "Seu Nome",
  "email": "seu@email.com"
}
```

### Passo 2: Usar o User Token

Agora você usa AMBOS os tokens em TODAS as outras requisições:

```http
POST https://api.hinova.com.br/api/sga/v2/listar/evento

Headers:
  Authorization: Bearer SEU_BEARER_TOKEN_FIXO
  token: AbCdEf1234567890XyZ...  ← USER TOKEN temporário

Body:
{
  "data_inicio": "2026-02-09",
  "data_fim": "2026-02-09"
}
```

```http
GET https://api.hinova.com.br/api/sga/v2/veiculo/buscar/123/codigo

Headers:
  Authorization: Bearer SEU_BEARER_TOKEN_FIXO
  token: AbCdEf1234567890XyZ...  ← MESMO USER TOKEN

(sem body)
```

---

## ⚠️ REGRA IMPORTANTE

**VOCÊ DESCOBRIU ESSA REGRA:**

> "Se você fizer uma NOVA AUTENTICAÇÃO, receberá um NOVO user token, 
> e o user token ANTERIOR será INVALIDADO!"

### Exemplo do Problema:

```
1. Autentica → Recebe Token A
2. Lista eventos com Token A → ✅ OK
3. Autentica de novo → Recebe Token B
4. Tenta buscar veículo com Token A → ❌ ERRO (token inválido)
```

### Solução:

```
1. Autentica UMA VEZ → Recebe Token A
2. Lista eventos com Token A → ✅ OK
3. Busca veículo 1 com Token A → ✅ OK
4. Busca veículo 2 com Token A → ✅ OK
5. Busca veículo 3 com Token A → ✅ OK

(Todas as operações usam o MESMO token!)
```

---

## 💻 Como o Sistema Implementa

### 1. Cache Global de Token

```python
token_cache = {
    'bearer_token': None,      # Token fixo
    'user_token': None,        # Token temporário da última autenticação
    'expires_at': None         # Quando expira (1 hora)
}
```

### 2. Autenticação Inteligente

```python
def autenticar(self, force=False):
    # Verifica se token em cache ainda é válido
    if token_cache['user_token'] and not force:
        if datetime.now() < token_cache['expires_at']:
            return True  # Usa o token em cache!
    
    # Só autentica se necessário
    response = requests.post(url, ...)
    token_cache['user_token'] = response.json()['token']
    token_cache['expires_at'] = datetime.now() + timedelta(hours=1)
```

### 3. Uso nas Requisições

```python
def listar_eventos(self, data_inicio, data_fim):
    headers = {
        "Authorization": f"Bearer {token_cache['bearer_token']}",
        "token": token_cache['user_token']  # Usa o token em cache!
    }
    response = requests.post(url, headers=headers, ...)
```

### 4. Reautenticação Automática

```python
# Se receber erro 401 (token expirou)
if response.status_code == 401:
    self.autenticar(force=True)  # Pega novo token
    # Tenta de novo com novo token
```

---

## 🎯 Por Que o Sistema Funciona Agora

### ✅ Antes (ERRADO):

```
Processamento:
├─ Autentica → Token A
├─ Lista eventos → Token A ✅
└─ Busca 10 veículos → Token A ✅

Teste de Conexões:
└─ Autentica → Token B (NOVO!)
    └─ Token A invalidado! ❌

Próximo Processamento:
└─ Tenta usar Token A → ERRO! ❌
```

### ✅ Agora (CORRETO):

```
Processamento:
├─ Autentica → Token A
├─ Lista eventos → Token A ✅
└─ Busca 10 veículos → Token A ✅

Teste de Conexões:
└─ Verifica Token A em cache → Ainda válido! ✅
    └─ NÃO autentica de novo!

Próximo Processamento:
├─ Verifica Token A → Ainda válido! ✅
└─ Usa Token A → Funciona! ✅
```

---

## 📊 Logs que Você Verá Agora

### Primeira Execução:

```
🔑 Autenticando na API Hinova...
   Bearer Token: eyJhbGciOi...
   Usuário: seu_usuario
   URL: https://api.hinova.com.br/...
   Status HTTP: 200
✓ Autenticação bem-sucedida!
   User Token: AbCdEf123...
   Válido até: 14:30:00
```

### Execuções Seguintes:

```
✓ Token em cache ainda válido (expira às 14:30:00)
📋 Buscando eventos...
✓ 5 eventos encontrados
```

### Quando Token Expira:

```
⚠️ Token expirado às 14:30:00
🔑 Reautenticando...
✓ Novo token obtido! Válido até 15:30:00
```

---

## 🔧 Teste de Conexões Atualizado

A página "Testar Conexões" agora:

1. **Verifica** se já existe token em cache
2. **Mostra** o status do token
3. **NÃO AUTENTICA** de novo (para não invalidar!)

```
✅ API Hinova SGA
Status: Token em cache válido
Token: AbCdEf123...
Expira em: 09/02/2026 14:30:00
```

---

## 💡 Resumo

| Situação | O Que Fazer |
|----------|-------------|
| Início do processamento | Autenticar e pegar user token |
| Durante processamento | Usar MESMO user token em TUDO |
| Token expira | Reautenticar e pegar NOVO token |
| Teste de conexões | APENAS verificar token em cache |
| Entre execuções | Reutilizar token se ainda válido |

---

## ✅ Checklist de Implementação Correta

- [x] Autentica UMA VEZ no início do processamento
- [x] Armazena user token em cache global
- [x] Usa mesmo token em TODAS as requisições
- [x] Envia Bearer + User token juntos
- [x] Reautentica apenas se token expirar (erro 401)
- [x] Página de teste NÃO invalida token em uso
- [x] Logs mostram quando usa cache vs quando autentica

---

**Agora o sistema está 100% alinhado com o funcionamento correto da API Hinova!** ✅
