# 🚀 Sistema Hinova → UppChannel - Versão Completa

## ✨ Novidades desta Versão

### 🔄 Auto-Refresh de Token
- ✅ Token da Hinova renovado automaticamente
- ✅ Cache de token com validade de 1 hora
- ✅ Reautenticação transparente quando expirar
- ✅ **Solução para o problema do token que expira!**

### 📊 Dashboard Completo em Tempo Real
- ✅ Interface web moderna e profissional
- ✅ Logs em tempo real (atualiza a cada 5 segundos)
- ✅ 4 abas: Dashboard, Logs, Mensagens, Configurações
- ✅ Visualização de status e progresso

### 💾 Banco de Dados SQLite
- ✅ Histórico completo de mensagens enviadas
- ✅ Logs do sistema persistidos
- ✅ Configurações salvas no banco
- ✅ **Nunca perde dados, mesmo após reiniciar!**

### ⚙️ Painel de Configuração
- ✅ Editar credenciais pela interface web
- ✅ Alterar situações ativas
- ✅ Modificar intervalo de verificação
- ✅ Tudo sem editar código!

### 📝 Sistema de Logs Avançado
- ✅ Logs coloridos por nível (INFO, SUCCESS, WARNING, ERROR)
- ✅ Timestamps precisos
- ✅ Histórico completo no banco
- ✅ **Fácil de debugar problemas!**

## 📦 Arquivos Incluídos

```
sistema-completo/
├── app.py                 # Aplicação Flask completa
├── dashboard.html         # Interface web (será servida pelo app.py)
├── requirements.txt       # Dependências Python
├── Dockerfile            # Container Docker
├── render.yaml          # Configuração Render
├── .gitignore           # Arquivos a ignorar
├── .env.example         # Exemplo de variáveis
└── README_COMPLETO.md   # Este arquivo
```

## 🚀 Novos Recursos

### 1. Auto-Refresh de Token ✅

O sistema agora gerencia automaticamente o token da Hinova:

```python
# Token é armazenado em cache
token_cache = {
    'bearer_token': None,
    'user_token': None,
    'expires_at': None  # Expira em 1 hora
}

# Se expirar, reautentica automaticamente
if datetime.now() >= token_cache['expires_at']:
    autenticar(force=True)
```

**Benefício:** Você não precisa mais se preocupar com o token expirando!

### 2. Dashboard Web Completo

Acesse `https://seu-app.onrender.com` para ver:

#### 📊 **Aba Dashboard**
- Estatísticas em tempo real
- Status do sistema (rodando/ocioso)
- Logs em tempo real
- Botão "Executar Agora"

#### 📋 **Aba Logs do Sistema**
- Todos os logs do sistema
- Filtrados por nível
- Com timestamps
- Histórico completo

#### 💬 **Aba Histórico de Mensagens**
- Todas as mensagens enviadas
- Status (Enviado/Falhou)
- Dados do cliente
- Visualizar mensagem completa

#### ⚙️ **Aba Configurações**
- Editar credenciais
- Alterar situações ativas
- Modificar intervalo
- Salvar no banco de dados

### 3. Banco de Dados SQLite

O sistema agora salva tudo em `/tmp/hinova_messages.db`:

**Tabelas:**
- `messages` - Histórico de mensagens
- `system_logs` - Logs do sistema
- `config` - Configurações

**Campos da tabela messages:**
```sql
- id (auto-increment)
- timestamp
- protocolo
- evento_id
- situacao_codigo
- situacao_nome
- telefone
- mensagem
- status (ENVIADO/FALHOU)
- erro
- nome_associado
- placa
```

### 4. Logs em Tempo Real

Os logs aparecem instantaneamente na interface:

```
10:30:15 [INFO] 🚀 INICIANDO PROCESSAMENTO DE EVENTOS
10:30:16 [SUCCESS] ✓ Autenticação bem-sucedida
10:30:17 [INFO] 📋 Buscando eventos de 2026-02-06...
10:30:18 [INFO] ✓ 5 eventos encontrados
10:30:19 [SUCCESS] ✓ Mensagem enviada para 31999998888
10:30:25 [SUCCESS] ✓ Processamento concluído: 3 mensagens
```

## 📊 Endpoints da API

### GET `/`
Dashboard principal (interface HTML)

### GET `/health`
Health check para o Render
```json
{
  "status": "healthy",
  "timestamp": "2026-02-06T10:30:00"
}
```

### GET `/api/status`
Status completo do sistema
```json
{
  "last_run": "2026-02-06T10:30:00",
  "last_status": "✓ 3 mensagens enviadas",
  "is_running": false,
  "current_step": "",
  "stats": {
    "total_runs": 10,
    "successful_messages": 27,
    "failed_messages": 2
  },
  "logs": [...],
  "processed_events_count": 15
}
```

### GET `/api/logs`
Todos os logs do sistema (últimos 100)

### GET `/api/messages`
Histórico de mensagens enviadas

### GET `/api/run-now`
Executa processamento manual

### GET|POST `/api/config`
- GET: Retorna configuração atual
- POST: Salva nova configuração

## 🔧 Instalação Local

### Requisitos
- Python 3.7+
- pip

### Passos

1. **Extrair arquivos**
```bash
unzip sistema-completo.zip
cd sistema-completo
```

2. **Instalar dependências**
```bash
pip install -r requirements.txt
```

3. **Configurar variáveis de ambiente**
```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

4. **Executar**
```bash
python app.py
```

5. **Acessar**
```
http://localhost:10000
```

## 🚀 Deploy no Render

### Opção 1: Via GitHub (Recomendado)

1. Faça upload dos arquivos para o GitHub
2. No Render: New → Web Service
3. Conecte o repositório
4. Configure:
   - Environment: Docker
   - Plan: Free

5. Adicione as variáveis de ambiente:
```
HINOVA_TOKEN=seu_token
HINOVA_USUARIO=seu_usuario
HINOVA_SENHA=sua_senha
UPPCHANNEL_API_KEY=sua_api_key
SITUACOES_ATIVAS=6,15,11,23,38,80,82,30,40,5,10,3,45,77,76,33,8,29,70,71,72,79,32,59,4,20,61
INTERVALO_MINUTOS=15
```

6. Deploy!

### Opção 2: Deploy Direto

Render também aceita deploy direto do ZIP.

## 💡 Como Usar

### 1. Acesse a Dashboard

Abra a URL fornecida pelo Render (ex: `https://hinova-monitor.onrender.com`)

### 2. Monitore em Tempo Real

- Dashboard atualiza automaticamente a cada 5 segundos
- Veja logs acontecendo em tempo real
- Acompanhe estatísticas

### 3. Execute Manualmente

Clique em "▶️ Executar Agora" para processar eventos imediatamente

### 4. Visualize Mensagens

- Vá na aba "Histórico de Mensagens"
- Veja todas as mensagens enviadas
- Clique em "Ver" para ver a mensagem completa

### 5. Configure pelo Painel

- Vá na aba "Configurações"
- Edite credenciais
- Altere situações ativas
- Salve

## 🔍 Solução de Problemas

### Problema: Token expira durante execução

**Solução:** ✅ Já resolvido! O sistema renova automaticamente.

### Problema: Não vejo os logs

**Solução:** 
1. Aguarde 5 segundos (atualização automática)
2. Ou clique em "🔄 Atualizar"

### Problema: Mensagens não aparecem no histórico

**Solução:**
1. Vá na aba "Histórico de Mensagens"
2. Clique em "🔄 Atualizar"
3. Verifique se o processamento foi executado

### Problema: Configuração não salva

**Solução:**
1. Certifique-se de clicar em "💾 Salvar Configuração"
2. Aguarde a confirmação
3. **Importante:** Reinicie o serviço no Render para aplicar

### Problema: Banco de dados vazio após reiniciar

**Solução:**
⚠️ No plano free do Render, o `/tmp` é limpo em reinicializações.
Para persistência permanente, considere o plano pago ou use um banco externo.

## 📊 Estatísticas e Monitoramento

### Métricas Disponíveis

- **Total de Execuções**: Quantas vezes o sistema rodou
- **Mensagens Enviadas**: Total de sucesso
- **Falhas**: Mensagens que falharam
- **Eventos Processados**: Total único de eventos

### Logs por Nível

- **INFO**: Informações gerais
- **SUCCESS**: Operações bem-sucedidas
- **WARNING**: Avisos (não bloqueiam o sistema)
- **ERROR**: Erros que precisam atenção

## 🎯 Melhores Práticas

### ✅ Recomendado

1. Monitore a dashboard pelo menos 1x por dia
2. Verifique logs se houver falhas
3. Ajuste o intervalo conforme necessidade
4. Mantenha backup das credenciais

### ❌ Evitar

1. Intervalo menor que 5 minutos (pode sobrecarregar APIs)
2. Desativar situações importantes (3, 10, etc)
3. Alterar configuração durante processamento
4. Executar manualmente com muita frequência

## 🆕 Diferenças da Versão Anterior

| Recurso | Versão Antiga | Versão Nova |
|---------|---------------|-------------|
| Refresh de Token | ❌ Manual | ✅ Automático |
| Interface Web | ❌ Básica | ✅ Completa |
| Banco de Dados | ❌ Nenhum | ✅ SQLite |
| Histórico | ❌ Memória | ✅ Persistido |
| Configuração | ❌ Variáveis | ✅ Interface |
| Logs | ❌ Console | ✅ Tempo Real |

## 📚 Documentação Adicional

- **API Hinova**: https://api.hinova.com.br/api/sga/v2/doc/
- **API UppChannel**: https://uppchannel.readme.io/

## 🆘 Suporte

Se tiver problemas:

1. Verifique os logs na aba "Logs do Sistema"
2. Consulte a aba "Histórico de Mensagens"
3. Teste as credenciais manualmente
4. Verifique se há créditos no UppChannel

---

✅ **Sistema completo pronto para produção!**

Com auto-refresh de token, banco de dados e interface moderna! 🚀
