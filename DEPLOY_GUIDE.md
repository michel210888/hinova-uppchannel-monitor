# 🚀 Guia de Deploy no Render - Passo a Passo Completo

Este guia detalhado mostrará como fazer o deploy do sistema no Render.com gratuitamente.

## 📋 Pré-requisitos

Antes de começar, você precisará:

✅ Conta no GitHub (gratuita)
✅ Conta no Render.com (gratuita)  
✅ Token da API Hinova SGA
✅ API Key do UppChannel

---

## Parte 1: Preparar o Repositório no GitHub

### Passo 1.1: Criar Repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique no botão **+** (canto superior direito) → **New repository**
3. Configure:
   - **Repository name**: `hinova-uppchannel-monitor`
   - **Description**: `Sistema de mensagens automáticas Hinova → UppChannel`
   - **Public** (recomendado para plano gratuito)
   - ✅ Marque **Add a README file**
4. Clique em **Create repository**

### Passo 1.2: Fazer Upload dos Arquivos

Você tem duas opções:

**Opção A - Via Interface Web (mais fácil):**

1. No seu repositório, clique em **Add file** → **Upload files**
2. Arraste todos os arquivos deste projeto:
   - `app.py`
   - `requirements.txt`
   - `Dockerfile`
   - `render.yaml`
   - `.env.example`
   - `.gitignore`
   - `README.md`
3. Escreva uma mensagem de commit: "Initial commit"
4. Clique em **Commit changes**

**Opção B - Via Git (se você conhece Git):**

```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/hinova-uppchannel-monitor.git
cd hinova-uppchannel-monitor

# Copie os arquivos para esta pasta
# (copie todos os arquivos do projeto)

# Adicione e commit
git add .
git commit -m "Initial commit"
git push origin main
```

---

## Parte 2: Deploy no Render

### Passo 2.1: Criar Conta no Render

1. Acesse [render.com](https://render.com)
2. Clique em **Get Started** ou **Sign Up**
3. Escolha **Sign up with GitHub** (mais fácil)
4. Autorize o Render a acessar seus repositórios

### Passo 2.2: Criar Web Service

1. No dashboard do Render, clique em **New +** (canto superior direito)
2. Selecione **Web Service**
3. Na lista de repositórios:
   - Se não aparecer seu repositório, clique em **Configure account**
   - Dê permissão ao Render para acessar todos os repositórios
   - Volte e atualize a página

### Passo 2.3: Configurar o Serviço

1. Selecione o repositório `hinova-uppchannel-monitor`
2. Configure os campos:

   **Name**: `hinova-monitor` (ou qualquer nome que preferir)
   
   **Region**: Escolha a mais próxima:
   - Oregon (EUA Oeste)
   - Frankfurt (Europa)
   - Singapore (Ásia)
   
   **Branch**: `main`
   
   **Runtime**: Será detectado automaticamente como **Docker**
   
   **Instance Type**: **Free** (gratuito)

3. **NÃO clique em Create ainda!** Antes, precisamos configurar as variáveis de ambiente.

### Passo 2.4: Configurar Variáveis de Ambiente

1. Role para baixo até a seção **Environment Variables**
2. Clique em **Add Environment Variable** e adicione cada uma:

```
HINOVA_TOKEN
Valor: [Cole aqui seu token Hinova]

HINOVA_USUARIO
Valor: [Seu usuário do SGA]

HINOVA_SENHA
Valor: [Sua senha do SGA]

UPPCHANNEL_API_KEY
Valor: [Cole aqui sua API Key UppChannel]

SITUACOES_ATIVAS
Valor: 1,9

INTERVALO_MINUTOS
Valor: 15
```

**💡 Dica**: Para cada variável:
- Clique em **Add Environment Variable**
- Digite o **Key** (nome da variável)
- Digite o **Value** (valor)
- Repita para todas as variáveis

### Passo 2.5: Iniciar o Deploy

1. Depois de adicionar todas as variáveis, clique em **Create Web Service**
2. O Render começará a fazer o deploy (isso leva 2-5 minutos)
3. Você verá os logs em tempo real na tela

### Passo 2.6: Verificar o Deploy

Aguarde até ver as mensagens:

```
==> Build successful 🎉
==> Deploying...
==> Your service is live 🎉
```

---

## Parte 3: Testar o Sistema

### Passo 3.1: Acessar a Dashboard

1. No topo da página do Render, você verá uma URL como:
   ```
   https://hinova-monitor.onrender.com
   ```
2. Clique nessa URL para abrir seu sistema
3. Você verá a dashboard com:
   - Status do sistema
   - Última execução
   - Estatísticas

### Passo 3.2: Executar Teste Manual

1. Na dashboard, clique em **▶️ Executar Agora**
2. O sistema processará eventos imediatamente
3. Verifique os logs no Render:
   - Volte ao dashboard do Render
   - Clique na aba **Logs**
   - Acompanhe o processamento em tempo real

### Passo 3.3: Verificar Logs

No Render, vá em **Logs** e procure por:

```
✓ Autenticação Hinova realizada com sucesso
Encontrados X eventos
✓ Mensagem enviada para 31999999999
✓ Evento 12345 processado
=== Processamento concluído: X mensagens ===
```

---

## Parte 4: Configurações Avançadas (Opcional)

### Personalizar Templates de Mensagens

Se quiser mensagens personalizadas, adicione estas variáveis no Render:

```
TEMPLATE_1
Olá {nome_associado}! 🚗\n\nSeu evento *{protocolo}* está ABERTO\nVeículo: {placa}

TEMPLATE_2
Evento {protocolo} em ANÁLISE\nVeículo: {placa}

TEMPLATE_3
Evento {protocolo} EM ANDAMENTO\nVeículo: {placa}

TEMPLATE_9
✅ Evento {protocolo} FINALIZADO!\nVeículo: {placa}\nData: {data_evento}
```

Depois de adicionar, clique em **Save Changes** e o serviço reiniciará automaticamente.

### Alterar Intervalo de Verificação

Para verificar eventos com mais ou menos frequência:

1. Edite a variável `INTERVALO_MINUTOS`
2. Valores sugeridos:
   - `5` - A cada 5 minutos (mais frequente)
   - `15` - A cada 15 minutos (padrão)
   - `30` - A cada 30 minutos
   - `60` - A cada 1 hora

---

## 🎯 Checklist Final

Antes de considerar concluído, verifique:

- [ ] Repositório criado no GitHub com todos os arquivos
- [ ] Web Service criado no Render
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Deploy concluído com sucesso (status: Live)
- [ ] Dashboard acessível via URL
- [ ] Teste manual executado com sucesso
- [ ] Logs mostrando processamento correto

---

## ⚠️ Limitações do Plano Gratuito

**Importante saber:**

- ⏸️ O serviço **hiberna** após 15 minutos sem uso
- 🔄 Quando alguém acessa a URL, ele **reinicia automaticamente** (leva ~30 segundos)
- ⏱️ Limite de **750 horas/mês** (suficiente para uso normal)
- 🔧 Para **manter sempre ativo**, considere o plano Starter ($7/mês)

**Dica**: Para evitar hibernação, você pode:
- Usar um serviço de "ping" como [UptimeRobot](https://uptimerobot.com/) (gratuito)
- Configure para fazer uma requisição HTTP ao seu serviço a cada 10 minutos

---

## 🐛 Problemas Comuns

### "Build Failed"

**Causa**: Erro nos arquivos
**Solução**: Verifique se todos os arquivos foram enviados corretamente

### "Service Unavailable"

**Causa**: Serviço hibernou
**Solução**: Aguarde 30 segundos, ele reiniciará automaticamente

### "Authentication Error"

**Causa**: Credenciais incorretas
**Solução**: 
1. Vá em **Environment** no Render
2. Verifique se as variáveis estão corretas
3. Clique em **Manual Deploy** → **Deploy latest commit**

### Não encontra eventos

**Causa**: Pode não haver eventos no dia atual
**Solução**: Isso é normal! O sistema só processa eventos do dia

---

## 📞 Suporte

Se tiver problemas:

1. **Verifique os logs** no Render (aba Logs)
2. **Consulte a documentação** das APIs:
   - [Hinova SGA](https://api.hinova.com.br/api/sga/v2/doc/)
   - [UppChannel](https://uppchannel.readme.io/)
3. **Abra uma issue** no GitHub do projeto

---

## 🎉 Pronto!

Seu sistema está rodando na nuvem! Ele verificará automaticamente eventos a cada 15 minutos e enviará mensagens via WhatsApp.

**Próximos passos sugeridos:**

1. Monitore a dashboard diariamente
2. Ajuste os templates conforme necessário
3. Configure alertas (se necessário)
4. Considere upgrade para plano pago se precisar de mais recursos

---

✅ **Deploy completo!** Seu sistema já está monitorando eventos automaticamente!
