# 🔧 Guia de Implementação das Correções

## Data: 16/02/2026

---

## 📋 VISÃO GERAL

Este guia explica como implementar as correções críticas no sistema Hinova → UppChannel.

**Arquivos criados:**
- ✅ `app_CORRIGIDO.py` - Versão corrigida completa
- ✅ `app_ORIGINAL_BACKUP.py` - Backup do código original
- ✅ `DIAGNOSTICO_PROBLEMAS.md` - Análise detalhada dos problemas
- ✅ `MELHORIAS_RECOMENDADAS.md` - Roadmap de melhorias futuras

---

## 🎯 CORREÇÕES IMPLEMENTADAS

### 1. ✅ Rastreamento de Mudanças de Status

**O que foi feito:**
- Nova tabela `evento_historico` no banco de dados
- Função `verificar_situacao_ja_notificada()` - Verifica se já foi notificada
- Função `registrar_situacao_detectada()` - Registra nova situação
- Função `marcar_situacao_como_notificada()` - Marca como enviada
- Função `get_ultima_situacao()` - Retorna última situação conhecida

**Benefício:**
- ✅ Permite múltiplas notificações para o mesmo protocolo
- ✅ Evita duplicatas (mesmo após reinicialização)
- ✅ Rastreia histórico completo de mudanças

**Exemplo:**
```
Evento 12345:
  10/02 → Situação 15 (Análise) → Notificado ✅
  12/02 → Situação 11 (Autorizado) → Notificado ✅
  15/02 → Situação 10 (Entregue) → Notificado ✅
```

---

### 2. ✅ Busca de Eventos dos Últimos 7 Dias

**O que foi feito:**
- Alterada linha 631: busca eventos dos últimos 7 dias (não apenas hoje)
- Nova variável de ambiente: `DIAS_BUSCA` (padrão: 7)
- Logs detalhados do período de busca

**Antes:**
```python
hoje = datetime.now().strftime('%Y-%m-%d')
eventos = hinova.listar_eventos(hoje, hoje)
```

**Depois:**
```python
dias_busca = config.get('dias_busca', 7)
data_inicio = (datetime.now() - timedelta(days=dias_busca)).strftime('%Y-%m-%d')
data_fim = datetime.now().strftime('%Y-%m-%d')
eventos = hinova.listar_eventos(data_inicio, data_fim)
```

**Benefício:**
- ✅ Detecta mudanças em eventos antigos
- ✅ Não perde notificações de eventos criados dias atrás

---

### 3. ✅ Persistência no Banco de Dados

**O que foi feito:**
- Tabela `evento_historico` persiste entre reinicializações
- Estado não é mais perdido quando servidor reinicia
- Histórico completo mantido no SQLite

**Benefício:**
- ✅ Sem duplicatas após reinicialização
- ✅ Rastreamento confiável
- ✅ Auditoria completa

---

### 4. ✅ Logs Detalhados de Comparação

**O que foi feito:**
- Logs mostram se evento é novo ou mudança
- Comparação de situação anterior vs atual
- Estatísticas detalhadas no final

**Exemplo de logs:**
```
🆕 Protocolo 12345: NOVO evento detectado (situação: Análise)
🔄 Protocolo 12346: MUDANÇA detectada
   Situação anterior: Análise (código 15)
   Situação atual: Autorizado (código 11)
```

**Estatísticas:**
```
📊 RESUMO DO PROCESSAMENTO:
   Total de eventos analisados: 45
   Eventos novos: 3
   Mudanças de situação: 8
   Sem mudança (já notificados): 34
   Mensagens enviadas: 11
```

---

## 🚀 COMO IMPLEMENTAR

### Opção 1: Substituir Arquivo Completo (Recomendado)

```bash
# 1. Fazer backup do original
cp app.py app_ORIGINAL_BACKUP.py

# 2. Substituir pelo corrigido
cp app_CORRIGIDO.py app.py

# 3. Reiniciar aplicação
# No Render: Manual Deploy → Clear build cache & deploy
```

**Vantagens:**
- ✅ Mais rápido
- ✅ Menos chance de erro
- ✅ Todas as correções de uma vez

**Desvantagens:**
- ⚠️ Precisa redeployar

---

### Opção 2: Aplicar Correções Manualmente

Se preferir aplicar as correções no código existente:

#### Passo 1: Adicionar Nova Tabela no Banco

Adicione após a linha 78 (função `init_database`):

```python
# NOVA: Tabela de histórico de situações
c.execute('''
    CREATE TABLE IF NOT EXISTS evento_historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        protocolo TEXT NOT NULL,
        situacao_codigo INTEGER NOT NULL,
        situacao_nome TEXT,
        data_deteccao TEXT NOT NULL,
        data_notificacao TEXT,
        status_notificacao TEXT,
        UNIQUE(protocolo, situacao_codigo)
    )
''')
```

#### Passo 2: Adicionar Funções de Rastreamento

Adicione após a linha 240 (função `get_config`):

```python
def verificar_situacao_ja_notificada(protocolo, situacao_codigo):
    """Verifica se esta combinação protocolo+situação já foi notificada"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                SELECT id, data_notificacao, status_notificacao 
                FROM evento_historico 
                WHERE protocolo = ? AND situacao_codigo = ?
            ''', (protocolo, situacao_codigo))
            
            row = c.fetchone()
            conn.close()
            
            if row:
                return True, {
                    'id': row[0],
                    'data_notificacao': row[1],
                    'status': row[2]
                }
            return False, None
            
        except Exception as e:
            logger.error(f"Erro ao verificar histórico: {e}")
            return False, None

def registrar_situacao_detectada(protocolo, situacao_codigo, situacao_nome):
    """Registra que esta situação foi detectada"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                INSERT OR IGNORE INTO evento_historico 
                (protocolo, situacao_codigo, situacao_nome, data_deteccao)
                VALUES (?, ?, ?, ?)
            ''', (protocolo, situacao_codigo, situacao_nome, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar situação: {e}")
            return False

def marcar_situacao_como_notificada(protocolo, situacao_codigo, status='ENVIADO'):
    """Marca que a notificação foi enviada"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                UPDATE evento_historico 
                SET data_notificacao = ?, status_notificacao = ?
                WHERE protocolo = ? AND situacao_codigo = ?
            ''', (datetime.now().isoformat(), status, protocolo, situacao_codigo))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao marcar notificação: {e}")
            return False

def get_ultima_situacao(protocolo):
    """Retorna a última situação conhecida de um protocolo"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                SELECT situacao_codigo, situacao_nome, data_deteccao 
                FROM evento_historico 
                WHERE protocolo = ?
                ORDER BY data_deteccao DESC
                LIMIT 1
            ''', (protocolo,))
            
            row = c.fetchone()
            conn.close()
            
            if row:
                return {
                    'codigo': row[0],
                    'nome': row[1],
                    'data': row[2]
                }
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar última situação: {e}")
            return None
```

#### Passo 3: Alterar Busca de Eventos

Substitua as linhas 630-632:

**Antes:**
```python
hoje = datetime.now().strftime('%Y-%m-%d')
eventos = hinova.listar_eventos(hoje, hoje)
```

**Depois:**
```python
dias_busca = config.get('dias_busca', 7)
data_inicio = (datetime.now() - timedelta(days=dias_busca)).strftime('%Y-%m-%d')
data_fim = datetime.now().strftime('%Y-%m-%d')

add_log('INFO', f'📅 Buscando eventos dos últimos {dias_busca} dias ({data_inicio} a {data_fim})')

eventos = hinova.listar_eventos(data_inicio, data_fim)
```

#### Passo 4: Alterar Lógica de Processamento

Substitua as linhas 652-663:

**Antes:**
```python
evento_id = f"{protocolo}_{situacao_codigo}"

if evento_id in system_state['processed_events']:
    add_log('INFO', f'⏭️ Evento {protocolo} já processado')
    continue

if situacao_codigo not in config['situacoes_ativas']:
    add_log('INFO', f'⏭️ Situação {situacao_codigo} não está ativa')
    continue
```

**Depois:**
```python
# Verificar situação ativa
if situacao_codigo not in config['situacoes_ativas']:
    add_log('INFO', f'⏭️ Protocolo {protocolo}: Situação {situacao_codigo} não está ativa')
    continue

# Verificar se já foi notificada
ja_notificada, historico = verificar_situacao_ja_notificada(protocolo, situacao_codigo)

if ja_notificada:
    add_log('INFO', f'⏭️ Protocolo {protocolo}: Situação {situacao_codigo} ({situacao_nome}) já foi notificada em {historico["data_notificacao"]}')
    continue

# Detectar se é novo ou mudança
ultima_situacao = get_ultima_situacao(protocolo)

if ultima_situacao is None:
    add_log('INFO', f'🆕 Protocolo {protocolo}: NOVO evento detectado (situação: {situacao_nome})')
else:
    add_log('INFO', f'🔄 Protocolo {protocolo}: MUDANÇA detectada')
    add_log('INFO', f'   Situação anterior: {ultima_situacao["nome"]} (código {ultima_situacao["codigo"]})')
    add_log('INFO', f'   Situação atual: {situacao_nome} (código {situacao_codigo})')

# Registrar que detectamos esta situação
registrar_situacao_detectada(protocolo, situacao_codigo, situacao_nome)
```

#### Passo 5: Marcar Notificações Enviadas

Adicione após linha 706 (dentro do `if uppchannel.enviar_mensagem`):

```python
# Marcar como notificada
marcar_situacao_como_notificada(protocolo, situacao_codigo, 'ENVIADO')
```

E após linha 715 (dentro do `else`):

```python
marcar_situacao_como_notificada(protocolo, situacao_codigo, 'FALHOU')
```

---

## ⚙️ CONFIGURAÇÃO

### Nova Variável de Ambiente (Opcional)

Adicione ao arquivo `.env` ou configuração do Render:

```bash
DIAS_BUSCA=7
```

**Valores recomendados:**
- `7` - Padrão (última semana)
- `3` - Para menos carga na API
- `14` - Para maior cobertura
- `30` - Para rastreamento completo

---

## 🧪 TESTANDO AS CORREÇÕES

### Teste 1: Verificar Banco de Dados

```python
# Conectar ao banco
import sqlite3
conn = sqlite3.connect('/tmp/hinova_messages.db')
c = conn.cursor()

# Verificar se tabela foi criada
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evento_historico'")
print(c.fetchone())  # Deve retornar ('evento_historico',)

# Ver registros
c.execute("SELECT * FROM evento_historico LIMIT 10")
for row in c.fetchall():
    print(row)
```

### Teste 2: Executar Processamento Manual

1. Acesse o dashboard: `https://seu-app.onrender.com`
2. Clique em "▶️ Executar Agora"
3. Vá para aba "Logs do Sistema"
4. Procure por:
   - `📅 Buscando eventos dos últimos 7 dias`
   - `🆕 Protocolo XXX: NOVO evento`
   - `🔄 Protocolo XXX: MUDANÇA detectada`
   - `📊 RESUMO DO PROCESSAMENTO`

### Teste 3: Simular Mudança de Status

1. Crie um evento de teste na Hinova
2. Mude a situação dele
3. Aguarde próxima execução (ou execute manualmente)
4. Verifique se ambas as notificações foram enviadas

---

## 📊 MONITORAMENTO

### Logs Importantes

**Busca ampliada funcionando:**
```
📅 Buscando eventos dos últimos 7 dias (09/02/2026 a 16/02/2026)
✓ 45 eventos encontrados no período
```

**Detecção de mudanças:**
```
🔄 Protocolo 12345: MUDANÇA detectada
   Situação anterior: Análise (código 15)
   Situação atual: Autorizado (código 11)
```

**Resumo detalhado:**
```
📊 RESUMO DO PROCESSAMENTO:
   Total de eventos analisados: 45
   Eventos novos: 3
   Mudanças de situação: 8
   Sem mudança (já notificados): 34
   Mensagens enviadas: 11
```

### Verificar Histórico no Banco

```sql
-- Ver todas as situações de um protocolo
SELECT * FROM evento_historico 
WHERE protocolo = '12345' 
ORDER BY data_deteccao DESC;

-- Ver situações não notificadas
SELECT * FROM evento_historico 
WHERE data_notificacao IS NULL;

-- Ver estatísticas
SELECT 
    situacao_codigo,
    situacao_nome,
    COUNT(*) as total,
    SUM(CASE WHEN data_notificacao IS NOT NULL THEN 1 ELSE 0 END) as notificadas
FROM evento_historico
GROUP BY situacao_codigo, situacao_nome;
```

---

## 🔄 ROLLBACK (Se necessário)

Se algo der errado, você pode voltar para a versão original:

```bash
# Restaurar backup
cp app_ORIGINAL_BACKUP.py app.py

# Redeployar
# No Render: Manual Deploy
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Antes do Deploy:
- [ ] Backup do `app.py` original criado
- [ ] Código corrigido revisado
- [ ] Variáveis de ambiente verificadas
- [ ] Documentação lida

### Durante o Deploy:
- [ ] Deploy realizado com sucesso
- [ ] Aplicação iniciou sem erros
- [ ] Dashboard acessível

### Após o Deploy:
- [ ] Executar processamento manual
- [ ] Verificar logs detalhados
- [ ] Confirmar criação da tabela `evento_historico`
- [ ] Testar com evento real
- [ ] Monitorar por 24h

---

## 🆘 TROUBLESHOOTING

### Erro: "no such table: evento_historico"

**Solução:**
```bash
# Deletar banco antigo (dados serão perdidos!)
rm /tmp/hinova_messages.db

# Reiniciar aplicação
# A tabela será criada automaticamente
```

### Erro: "UNIQUE constraint failed"

**Causa:** Tentando inserir situação duplicada

**Solução:** Isso é normal! O sistema usa `INSERT OR IGNORE` para evitar duplicatas.

### Muitas mensagens duplicadas

**Verificar:**
1. Tabela `evento_historico` existe?
2. Função `verificar_situacao_ja_notificada` está sendo chamada?
3. Logs mostram "já foi notificada"?

---

## 📞 SUPORTE

Se encontrar problemas:

1. **Verificar logs** no Render
2. **Consultar** `DIAGNOSTICO_PROBLEMAS.md`
3. **Revisar** `MELHORIAS_RECOMENDADAS.md`
4. **Testar** em ambiente local primeiro

---

## 🎯 PRÓXIMOS PASSOS

Após implementar as correções críticas:

1. **Monitorar** por 1 semana
2. **Coletar feedback** dos usuários
3. **Implementar melhorias** da Fase 2 (ver `MELHORIAS_RECOMENDADAS.md`)
4. **Otimizar** performance se necessário

---

**Documento criado em: 16/02/2026**
**Versão: 1.0**
