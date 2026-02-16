# 🚀 Deploy Imediato - Guia Rápido

## ✅ Código Atualizado e Enviado ao GitHub!

As correções críticas já foram aplicadas e estão no seu repositório GitHub.

---

## 📋 PASSO A PASSO NO RENDER

### 1. Acesse o Render Dashboard
   - Vá para: https://dashboard.render.com
   - Faça login na sua conta

### 2. Selecione seu Web Service
   - Clique no serviço `hinova-uppchannel-monitor`
   - Ou o nome que você deu ao serviço

### 3. Faça o Deploy Manual
   - No menu superior, clique em **"Manual Deploy"**
   - Selecione **"Clear build cache & deploy"** (recomendado)
   - Ou apenas **"Deploy latest commit"**
   - Clique em **"Deploy"**

### 4. Aguarde o Deploy
   - O processo leva cerca de 2-5 minutos
   - Você verá os logs em tempo real
   - Aguarde até ver: **"Your service is live 🎉"**

### 5. Acesse o Dashboard
   - Clique no link do seu serviço (ex: `https://seu-app.onrender.com`)
   - O dashboard deve abrir

### 6. Execute Processamento Manual
   - No dashboard, clique no botão verde **"▶️ Executar"**
   - Vá para a aba **"Logs do Sistema"**
   - Aguarde o processamento completar

---

## 🔍 O QUE PROCURAR NOS LOGS

### ✅ Sinais de Sucesso:

```
🚀 Sistema CORRIGIDO iniciando...
✅ Correções aplicadas:
   1. Rastreamento de mudanças de status
   2. Busca de eventos dos últimos 7 dias
   3. Persistência no banco de dados
   4. Logs detalhados de comparação

📅 Buscando eventos dos últimos 7 dias (09/02/2026 a 16/02/2026)
✓ Autenticação bem-sucedida!
✓ Token de usuário válido até XX:XX:XX

📋 Buscando eventos de 2026-02-09 até 2026-02-16...
🧪 TESTE 1: Apenas user_token no Authorization
   Status: 200
✓ FUNCIONOU com apenas user_token!
   Formato: Lista direta (ou "Objeto com chave eventos")
✓ X eventos encontrados no período

🆕 Protocolo 20263278: NOVO evento detectado (situação: ANÁLISE)
📝 Processando notificação para protocolo 20263278

📊 RESUMO DO PROCESSAMENTO:
   Total de eventos analisados: X
   Eventos novos: X
   Mudanças de situação: X
   Sem mudança (já notificados): X
   Mensagens enviadas: X
```

### ❌ Se Ver Erros:

**Erro de Autenticação:**
```
❌ Erro HTTP 401: Usuário ou senha inválidos
```
**Solução:** Verificar credenciais no Render (variáveis de ambiente)

**Erro de Parsing:**
```
❌ Erro ao listar eventos: 'list' object has no attribute 'get'
```
**Solução:** Já corrigido! Se ainda aparecer, me avise.

**Nenhum Evento:**
```
✓ Nenhum evento encontrado nos últimos 7 dias
```
**Solução:** Normal se não houver eventos. Crie um evento de teste na Hinova.

---

## 🧪 TESTAR COM EVENTO REAL

### Passo 1: Criar Evento de Teste na Hinova
1. Acesse a Hinova
2. Crie um novo evento (qualquer tipo)
3. Anote o **protocolo** (ex: 20263278)
4. Coloque em uma das **situações ativas** (ex: 2.1 - ANÁLISE)

### Passo 2: Executar Processamento
1. No dashboard do monitor, clique em **"▶️ Executar"**
2. Aguarde 10-30 segundos
3. Vá para **"Logs do Sistema"**

### Passo 3: Verificar Logs
Procure por:
- `🆕 Protocolo 20263278: NOVO evento detectado`
- `✓ Mensagem enviada para XXXXXXXXXXX`

### Passo 4: Mudar Situação
1. Na Hinova, mude o evento para outra situação (ex: 3.0 - AUTORIZADO)
2. Execute processamento novamente
3. Deve ver: `🔄 Protocolo 20263278: MUDANÇA detectada`

### Passo 5: Verificar WhatsApp
- O associado deve receber **2 mensagens** (uma para cada situação)
- Se recebeu as 2, está funcionando perfeitamente! ✅

---

## ⚙️ VERIFICAR VARIÁVEIS DE AMBIENTE

Se a autenticação falhar, verifique as variáveis no Render:

### No Render Dashboard:
1. Clique no seu serviço
2. Vá em **"Environment"** no menu lateral
3. Verifique se estas variáveis estão configuradas:

```bash
HINOVA_TOKEN=ef9be58415741701f2dc63a3192d8f0ef9b4d7aa10c34f66d12ee16fcae8a258a8c8616d608aa2ed44559e7fb50c40bab4c9ca4ed76807307a5c8cff4ca0b77c842015788f1316a175c12510a726df396a278d369391b6c2f34750e9ae1ca1bfb07cb99c7b7fb804bae55850a966c8bfb5e842a01aa0a26a57acf6c9220669b0d949ccbc9d068462df5f2246c5d88133

HINOVA_USUARIO=roboeventos

HINOVA_SENHA=Ubho3592#

UPPCHANNEL_API_KEY=Bearer pn_NXI0uWeSMy0ruztCP0TJjiYV4YGALFX21CsEaxlstFc

SITUACOES_ATIVAS=6,15,11,23,38,80,82,30,40,5,10,3,45,77,76,33,8,29,70,71,72,79,32,59,4,20,61

INTERVALO_MINUTOS=15

DIAS_BUSCA=7
```

**Importante:** Se as credenciais estiverem erradas, atualize-as e faça deploy novamente.

---

## 📊 MONITORAMENTO

### Dashboard Principal
- **Execuções:** Quantas vezes o sistema rodou
- **Enviadas:** Mensagens enviadas com sucesso
- **Falhas:** Mensagens que falharam
- **Processados:** Eventos únicos processados

### Aba "Histórico"
- Lista todas as mensagens enviadas
- Mostra protocolo, situação, cliente e status
- Use para auditar notificações

### Aba "Logs do Sistema"
- Logs detalhados de todas as operações
- Use para debugging
- Atualiza automaticamente a cada 5 segundos

---

## 🆘 PROBLEMAS COMUNS

### 1. "Nenhum evento para processar"
**Causa:** Não há eventos nos últimos 7 dias ou nenhum nas situações ativas
**Solução:** Criar evento de teste na Hinova

### 2. "Erro na autenticação"
**Causa:** Credenciais incorretas ou token expirado
**Solução:** Verificar variáveis de ambiente no Render

### 3. "Telefone não encontrado"
**Causa:** Associado do evento não tem telefone cadastrado
**Solução:** Adicionar telefone na Hinova

### 4. "Situação X não está ativa"
**Causa:** A situação do evento não está na lista de situações ativas
**Solução:** Adicionar o código da situação em `SITUACOES_ATIVAS`

---

## 📞 PRÓXIMOS PASSOS

### Após Confirmar que Funciona:

1. **Monitorar por 24h**
   - Verificar se notificações estão chegando
   - Checar taxa de sucesso vs falha

2. **Ajustar Intervalo (Opcional)**
   - Se quiser notificações mais rápidas: `INTERVALO_MINUTOS=10`
   - Se quiser menos carga: `INTERVALO_MINUTOS=20`

3. **Implementar Melhorias Futuras**
   - Ver arquivo `MELHORIAS_RECOMENDADAS.md`
   - Prioridade: Sistema de alertas, Dashboard aprimorado

---

## ✅ CHECKLIST

- [ ] Deploy feito no Render
- [ ] Aplicação iniciou sem erros
- [ ] Dashboard acessível
- [ ] Executar processamento manual
- [ ] Logs mostram "Sistema CORRIGIDO iniciando"
- [ ] Logs mostram "Buscando eventos dos últimos 7 dias"
- [ ] Criar evento de teste na Hinova
- [ ] Executar novamente
- [ ] Verificar se evento foi detectado
- [ ] Mudar situação do evento
- [ ] Verificar se mudança foi detectada
- [ ] Confirmar que 2 mensagens foram enviadas

---

**Tudo pronto! Agora é só fazer o deploy no Render e testar! 🚀**

Se tiver qualquer problema, me avise e eu te ajudo a resolver.
