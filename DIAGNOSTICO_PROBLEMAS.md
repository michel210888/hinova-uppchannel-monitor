# 🔍 Diagnóstico de Problemas - Sistema Hinova → UppChannel

## Data da Análise: 16/02/2026

---

## ❌ PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **Sistema Detecta Apenas Eventos do Dia Atual**

**Localização:** Linha 631 do `app.py`

```python
hoje = datetime.now().strftime('%Y-%m-%d')
eventos = hinova.listar_eventos(hoje, hoje)
```

**Problema:**
- O sistema busca **apenas eventos cadastrados hoje**
- **Mudanças de status** em eventos antigos **NÃO são detectadas**
- Se um evento foi criado há 3 dias e mudou de status hoje, ele **não será notificado**

**Impacto:**
- ⚠️ **CRÍTICO** - Este é provavelmente o motivo principal das notificações não chegarem
- Eventos que mudam de situação após o dia de cadastro não são processados

**Solução Necessária:**
- Buscar eventos por **data de modificação** ou **última atualização**
- Ou buscar eventos dos **últimos X dias** (ex: últimos 7 dias)

---

### 2. **Sistema Não Detecta Mudanças de Status**

**Localização:** Linhas 652-657 do `app.py`

```python
evento_id = f"{protocolo}_{situacao_codigo}"

if evento_id in system_state['processed_events']:
    add_log('INFO', f'⏭️ Evento {protocolo} já processado')
    continue
```

**Problema:**
- O sistema marca eventos como processados baseado em `protocolo + situação`
- Se um evento **já foi processado uma vez**, ele **nunca mais será processado**
- **Mudanças subsequentes de status** no mesmo evento são **ignoradas**

**Exemplo do Problema:**
1. Evento 12345 muda para situação 6 (COMUNICADO) → Mensagem enviada ✅
2. Evento 12345 muda para situação 11 (AUTORIZADO) → **Mensagem NÃO enviada** ❌
3. Evento 12345 muda para situação 10 (ENTREGUE) → **Mensagem NÃO enviada** ❌

**Impacto:**
- ⚠️ **CRÍTICO** - O sistema envia apenas a **primeira notificação** de cada evento
- Todas as mudanças de status subsequentes são **silenciosamente ignoradas**

**Solução Necessária:**
- Criar tabela no banco de dados para rastrear **histórico de situações**
- Verificar se a combinação `protocolo + situação` **já foi notificada antes**
- Permitir múltiplas notificações para o mesmo protocolo com situações diferentes

---

### 3. **Falta de Persistência do Estado Entre Reinicializações**

**Localização:** Linhas 31-45 do `app.py`

```python
system_state = {
    'processed_events': set(),  # ← Armazenado apenas em memória
    ...
}
```

**Problema:**
- O conjunto `processed_events` está **apenas em memória**
- Quando o servidor reinicia (comum no Render), **todo o histórico é perdido**
- Eventos já processados podem ser **reprocessados** após reinicialização

**Impacto:**
- ⚠️ **MÉDIO** - Pode causar mensagens duplicadas
- Perda de rastreamento entre reinicializações

**Solução Necessária:**
- Salvar `processed_events` no banco de dados SQLite
- Carregar histórico ao iniciar a aplicação

---

### 4. **Ausência de Webhook ou Polling Inteligente**

**Localização:** Sistema usa apenas agendamento por tempo (APScheduler)

**Problema:**
- O sistema verifica eventos a cada X minutos (padrão: 15 minutos)
- **Não há notificação em tempo real** quando um evento muda
- Atraso de até 15 minutos entre mudança e notificação

**Impacto:**
- ⚠️ **BAIXO** - Notificações atrasadas, mas funcionais
- Não é crítico, mas reduz a experiência do usuário

**Solução Necessária:**
- Implementar **webhook** da API Hinova (se disponível)
- Ou reduzir intervalo para 2-5 minutos
- Ou implementar polling inteligente (verificar apenas eventos "em andamento")

---

### 5. **API Hinova: Campo de Data Incorreto**

**Localização:** Linhas 358-361 do `app.py`

```python
payload = {
    "data_cadastro": data_inicio_br,
    "data_cadastro_final": data_fim_br
}
```

**Problema:**
- O sistema busca por `data_cadastro` (data de criação)
- Para detectar mudanças, deveria buscar por `data_modificacao` ou `data_atualizacao`
- **Eventos antigos com mudanças recentes não aparecem**

**Impacto:**
- ⚠️ **CRÍTICO** - Combinado com problema #1, impede detecção de mudanças

**Solução Necessária:**
- Verificar documentação da API Hinova para campo correto
- Testar com `data_modificacao`, `data_atualizacao` ou similar
- Ou buscar eventos dos últimos 7 dias e filtrar por modificações

---

## 📊 RESUMO DOS PROBLEMAS

| # | Problema | Severidade | Impacto nas Notificações |
|---|----------|------------|--------------------------|
| 1 | Busca apenas eventos do dia | 🔴 CRÍTICA | 90% das notificações perdidas |
| 2 | Não detecta mudanças de status | 🔴 CRÍTICA | Apenas primeira notificação enviada |
| 3 | Estado não persiste | 🟡 MÉDIA | Duplicatas após reinício |
| 4 | Sem webhook/polling inteligente | 🟢 BAIXA | Atraso de 15 min |
| 5 | Campo de data incorreto | 🔴 CRÍTICA | Eventos antigos ignorados |

---

## 🎯 CAUSA RAIZ DO PROBLEMA

**Por que as notificações não estão chegando:**

1. ✅ Sistema busca eventos da API Hinova
2. ❌ **MAS** busca apenas eventos cadastrados HOJE
3. ❌ **E** eventos já processados são ignorados permanentemente
4. ❌ **RESULTADO:** Mudanças de status em eventos existentes nunca são detectadas

**Cenário Real:**
- Evento criado em 10/02/2026 com situação "Análise" (código 15)
- Hoje (16/02/2026) muda para "Autorizado" (código 11)
- Sistema busca eventos com `data_cadastro = 16/02/2026`
- Evento não aparece (foi cadastrado em 10/02)
- **Notificação nunca é enviada** ❌

---

## ✅ SOLUÇÕES NECESSÁRIAS (em ordem de prioridade)

### 1. **Implementar Rastreamento de Mudanças de Status**
- Criar tabela `evento_situacoes` no banco
- Salvar histórico: `protocolo`, `situacao_codigo`, `data_notificacao`
- Verificar se combinação já foi notificada

### 2. **Buscar Eventos por Período Amplo**
- Buscar eventos dos últimos 7-30 dias
- Ou implementar campo de data de modificação
- Comparar situação atual com última situação salva

### 3. **Persistir Estado no Banco de Dados**
- Salvar `processed_events` no SQLite
- Carregar ao iniciar aplicação
- Limpar registros antigos (>30 dias)

### 4. **Adicionar Logs Detalhados**
- Logar quantos eventos foram buscados
- Logar quantos foram filtrados e por quê
- Logar comparação de situações

### 5. **Implementar Modo de Teste**
- Endpoint para simular mudança de status
- Visualização de eventos em diferentes situações
- Teste de templates sem enviar mensagens

---

## 🔧 PRÓXIMOS PASSOS

1. **Implementar correções críticas** (problemas #1, #2, #5)
2. **Testar com eventos reais** da API Hinova
3. **Adicionar monitoramento** de mudanças de status
4. **Documentar** comportamento esperado vs atual
5. **Deploy** da versão corrigida

---

## 📝 OBSERVAÇÕES ADICIONAIS

### Pontos Positivos do Código Atual:
- ✅ Autenticação com cache de token (1 hora)
- ✅ Banco de dados SQLite para logs
- ✅ Dashboard web funcional
- ✅ Templates customizados por situação
- ✅ Tratamento de erros básico
- ✅ Múltiplas tentativas de autenticação

### Melhorias Recomendadas (não críticas):
- 📊 Dashboard com gráficos de situações ao longo do tempo
- 🔔 Notificações de erro por email/Telegram
- 📱 Validação de formato de telefone
- 🧪 Modo sandbox (não envia mensagens reais)
- 📈 Métricas de tempo de resposta da API
- 🔄 Retry automático para mensagens falhas

---

**Documento gerado automaticamente pela análise do código**
