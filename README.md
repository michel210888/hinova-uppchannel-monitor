# 🚗 Monitor Hinova → UppChannel

Sistema automatizado de monitoramento de eventos da API Hinova SGA com envio de mensagens WhatsApp via UppChannel.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

## 📋 Sobre o Projeto

Este sistema monitora automaticamente eventos cadastrados no sistema Hinova SGA e envia notificações via WhatsApp para os clientes utilizando a API do UppChannel. Ideal para:

- ✅ Notificar clientes sobre status de eventos
- 📱 Enviar atualizações automáticas por WhatsApp
- ⚙️ Personalizar mensagens por situação
- 📊 Monitorar estatísticas em tempo real

## 🚀 Deploy Rápido no Render (Gratuito)

### Passo 1: Fork este Repositório

1. Clique em **Fork** no canto superior direito desta página
2. Aguarde o fork ser criado na sua conta

### Passo 2: Criar Conta no Render

1. Acesse [render.com](https://render.com)
2. Crie uma conta gratuita (pode usar GitHub)

### Passo 3: Deploy Automático

1. No Render, clique em **New +** → **Web Service**
2. Conecte seu repositório GitHub
3. Configure:
   - **Name**: `hinova-monitor` (ou nome de sua preferência)
   - **Environment**: `Docker`
   - **Plan**: `Free`

### Passo 4: Configurar Variáveis de Ambiente

Na aba **Environment**, adicione:

```
HINOVA_TOKEN=seu_token_aqui
HINOVA_USUARIO=seu_usuario
HINOVA_SENHA=sua_senha
UPPCHANNEL_API_KEY=sua_chave_api
SITUACOES_ATIVAS=1,9
INTERVALO_MINUTOS=15
```

### Passo 5: Deploy!

Clique em **Create Web Service** e aguarde o deploy (2-3 minutos).

## 🔐 Obtendo as Credenciais

### Token Hinova SGA

1. Acesse o sistema SGA
2. Vá em **Área Cliente** → **APIs** → **Gerenciar APIs**
3. Clique em **Novo**
4. Selecione o Interveniente
5. Defina um apelido
6. Marque **Permitir Acesso** como **SIM**
7. Libere os endpoints necessários
8. Copie o token gerado

### API Key UppChannel

1. Acesse [uppchannel.readme.io](https://uppchannel.readme.io/)
2. Faça login na sua conta
3. Navegue até a seção de API
4. Copie sua API Key

## ⚙️ Configurações

### Situações Disponíveis

Configure quais situações devem enviar mensagens através da variável `SITUACOES_ATIVAS`:

| Código | Situação | Descrição |
|--------|----------|-----------|
| 1 | ABERTO | Evento recém criado |
| 2 | EM ANÁLISE | Equipe avaliando |
| 3 | EM ANDAMENTO | Reparos em execução |
| 9 | FINALIZADO | Evento concluído |

**Exemplo**: `SITUACOES_ATIVAS=1,9` (notifica apenas eventos abertos e finalizados)

### Templates de Mensagens

Você pode personalizar as mensagens definindo variáveis de ambiente:

```
TEMPLATE_1="Olá {nome_associado}! Seu evento está ABERTO"
TEMPLATE_2="Evento {protocolo} em ANÁLISE"
TEMPLATE_3="Evento {protocolo} EM ANDAMENTO"
TEMPLATE_9="✅ Evento {protocolo} FINALIZADO!"
```

#### Variáveis Disponíveis

Use estas variáveis nos templates:

- `{nome_associado}` - Nome do cliente
- `{protocolo}` - Número do protocolo
- `{placa}` - Placa do veículo
- `{situacao}` - Situação atual
- `{motivo}` - Motivo do evento
- `{data_evento}` - Data do evento

## 📊 Monitoramento

Após o deploy, acesse a URL fornecida pelo Render para visualizar:

- ✅ Status do sistema
- 📈 Estatísticas de envios
- ⏱️ Última execução
- ❌ Erros (se houver)

### Endpoints Disponíveis

- `/` - Dashboard principal
- `/health` - Health check
- `/stats` - Estatísticas em JSON
- `/run-now` - Executar processamento manualmente

## 🔧 Configurações Avançadas

### Alterar Intervalo de Verificação

Por padrão, o sistema verifica eventos a cada 15 minutos. Para alterar:

```
INTERVALO_MINUTOS=30
```

### Horário Comercial (Opcional)

Para executar apenas em horário comercial, adicione:

```
HORARIO_INICIO=08:00
HORARIO_FIM=18:00
DIAS_SEMANA=1,2,3,4,5
```

## 🐛 Resolução de Problemas

### Erro de Autenticação

❌ **Problema**: "Erro na autenticação Hinova"

✅ **Solução**:
- Verifique se o token está correto
- Confirme usuário e senha
- Certifique-se que os endpoints estão liberados no SGA

### Mensagens Não Enviadas

❌ **Problema**: "Erro ao enviar mensagem"

✅ **Solução**:
- Verifique a API Key do UppChannel
- Confirme formato do telefone
- Verifique créditos na conta UppChannel

### Eventos Não Encontrados

❌ **Problema**: "Nenhum evento encontrado"

✅ **Solução**:
- Confirme que existem eventos na data atual
- Verifique permissões do usuário no SGA

## 📝 Logs

Os logs são exibidos no dashboard do Render em tempo real:

1. Acesse seu serviço no Render
2. Clique na aba **Logs**
3. Visualize todas as operações

## 💰 Custos

Este projeto utiliza:

- **Render Free Tier**: Gratuito com limitações
  - 750 horas/mês de execução
  - Hiberna após 15 minutos sem uso
  - Reinicia automaticamente quando acessado

Para uso ininterrupto, considere o plano **Starter** ($7/mês).

## 🛠️ Desenvolvimento Local

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/hinova-uppchannel.git
cd hinova-uppchannel

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais

# Execute
python app.py
```

Acesse: `http://localhost:10000`

## 📚 Documentação das APIs

- [Hinova SGA API](https://api.hinova.com.br/api/sga/v2/doc/)
- [UppChannel API](https://uppchannel.readme.io/)

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## 📧 Suporte

Encontrou algum problema? Abra uma [issue](https://github.com/seu-usuario/hinova-uppchannel/issues) no GitHub.

---

⭐ Se este projeto foi útil para você, considere dar uma estrela!

**Desenvolvido com ❤️ para automatizar comunicação com clientes**
