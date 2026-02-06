# 📋 Guia das 27 Situações Configuradas

## Visão Geral

Este sistema está pré-configurado com **27 situações ativas** que enviarão mensagens automáticas via WhatsApp sempre que o status de um evento mudar.

## 🎯 Situações por Categoria

### 📢 Comunicação (1 situação)
- **Código 6** - COMUNICADO

### 🔍 Análise e Vistoria (1 situação)
- **Código 15** - ANÁLISE

### 🔓 Aprovações e Autorizações (2 situações)
- **Código 11** - AUTORIZADO EM ORÇAMENTO
- **Código 5** - REPAROS LIBERADOS

### 💰 Financeiro e Acordos (4 situações)
- **Código 23** - COTA DE PARTICIPAÇÃO
- **Código 38** - ACORDO EM ANDAMENTO
- **Código 30** - ACORDO FINALIZADO
- **Código 4** - COBRANÇA FIDELIDADE

### 🚗 Veículo Reserva (3 situações)
- **Código 80** - CARRO RESERVA
- **Código 82** - CARRO RESERVA FINALIZADO
- **Código 61** - VEÍCULO RESERVA

### 🔧 Reparos e Peças (1 situação)
- **Código 40** - COMPRA DE PEÇAS

### 🛡️ Garantia (3 situações)
- **Código 45** - GARANTIA AUTORIZADA
- **Código 77** - GARANTIA ENTREGUE
- **Código 76** - GARANTIA FINALIZADA

### 💵 Indenização (1 situação)
- **Código 33** - INDENIZAÇÃO AGENDADA

### ⚙️ Serviços Opcionais (7 situações)
- **Código 29** - OPCIONAL ABERTO
- **Código 70** - OPCIONAL COTAÇÃO
- **Código 71** - OPIC. COTA PARTICIPAÇÃO
- **Código 72** - OPCIONAL LIBERADO
- **Código 79** - OPCIONAL ENTREGUE
- **Código 32** - OPCIONAL FINALIZADO
- **Código 59** - OPCIONAL FINALIZADO 1

### ✅ Finalizações (4 situações)
- **Código 10** - VEÍCULO ENTREGUE
- **Código 3** - FINALIZADO
- **Código 8** - ROUBO/FURTO FINALIZADO
- **Código 20** - FINALIZADO REPAROS PELO TERCEIRO

## 📊 Estatísticas

| Categoria | Quantidade |
|-----------|------------|
| Total de situações | 27 |
| Situações de finalização | 10 |
| Situações em andamento | 17 |
| Com emojis personalizados | 27 |

## 💬 Templates de Mensagens

Cada situação possui um template personalizado com:

### Elementos Padrão
- ✅ **Emoji apropriado** (baseado na categoria)
- 📝 **Nome da situação**
- 🔢 **Protocolo do evento**
- 🚗 **Placa do veículo**
- 📅 **Data do evento**
- 💬 **Mensagem de encerramento** (baseada no tipo)

### Exemplo de Mensagem

```
Olá João Silva! ✅

*4.9 - FINALIZADO*

Protocolo: 20250001
Veículo: ABC-1234
Data: 06/02/2026

Obrigado por utilizar nossos serviços! ✨
```

## 🎨 Emojis por Categoria

| Categoria | Emoji | Descrição |
|-----------|-------|-----------|
| Finalizado | ✅ | Indica conclusão |
| Aprovado | 🔓 | Indica liberação |
| Análise | 🔍 | Em avaliação |
| Comunicado | 📢 | Informação importante |
| Financeiro | 💰 | Questões de pagamento |
| Veículo Reserva | 🚗 | Veículo substituto |
| Garantia | 🛡️ | Serviço de garantia |
| Opcional | ⚙️ | Serviço adicional |
| Reparo | 🔧 | Manutenção |
| Indenização | 💵 | Pagamento |

## ⚙️ Configuração

### String de Situações Ativas

Para usar no Render ou arquivo `.env`:

```bash
SITUACOES_ATIVAS=6,15,11,23,38,80,82,30,40,5,10,3,45,77,76,33,8,29,70,71,72,79,32,59,4,20,61
```

### Alterar Situações

Se você quiser **ativar apenas algumas situações**:

1. Escolha os códigos desejados da lista acima
2. Configure no Render: `SITUACOES_ATIVAS=3,10,82` (exemplo)
3. Ou edite o arquivo `config.json` localmente

### Personalizar Mensagens

Você pode personalizar cada mensagem:

**Opção 1 - Via Configurador HTML:**
1. Abra `configurador_27_situacoes.html`
2. Edite as mensagens
3. Gere o `config.json`

**Opção 2 - Via Variáveis de Ambiente:**
```bash
TEMPLATE_3="Olá {nome_associado}! Seu evento foi FINALIZADO! Protocolo: {protocolo}"
TEMPLATE_10="Veículo {placa} entregue para {nome_associado}!"
```

**Opção 3 - Editando config.json:**
```json
{
  "templates_mensagem": {
    "3": "Sua mensagem personalizada aqui...",
    "10": "Outra mensagem..."
  }
}
```

## 🔤 Variáveis Disponíveis

Use estas variáveis em qualquer template:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `{nome_associado}` | Nome do cliente | João Silva |
| `{protocolo}` | Número do protocolo | 20250001 |
| `{placa}` | Placa do veículo | ABC-1234 |
| `{situacao}` | Nome da situação atual | FINALIZADO |
| `{motivo}` | Motivo do evento | Colisão |
| `{data_evento}` | Data do evento | 06/02/2026 |

## 📱 Exemplos de Mensagens por Categoria

### Comunicado (Cód. 6)
```
Olá {nome_associado}! 📢

*1.0 - COMUNICADO*

Protocolo: {protocolo}
Veículo: {placa}
Data: {data_evento}

Em breve entraremos em contato! 📞
```

### Aprovação (Cód. 11)
```
Olá {nome_associado}! 🔓

*3.0 - AUTORIZADO EM ORÇAMENTO*

Protocolo: {protocolo}
Veículo: {placa}
Data: {data_evento}

Prosseguiremos com os próximos passos. 👍
```

### Finalizado (Cód. 3)
```
Olá {nome_associado}! ✅

*4.9 - FINALIZADO*

Protocolo: {protocolo}
Veículo: {placa}
Data: {data_evento}

Obrigado por utilizar nossos serviços! ✨
```

## 🎯 Boas Práticas

### ✅ Recomendado

- Manter todas as 27 situações ativas inicialmente
- Monitorar logs por 1 semana
- Ajustar mensagens com base no feedback
- Personalizar emojis se necessário

### ❌ Evitar

- Desativar situações de finalização (3, 10, etc)
- Mensagens muito longas (>300 caracteres)
- Remover variáveis importantes como {protocolo}
- Usar emojis incompatíveis com WhatsApp

## 📊 Monitoramento

### Ver Estatísticas

Acesse a dashboard do seu serviço no Render:
```
https://seu-app.onrender.com/stats
```

### Campos Importantes
- `successful_messages` - Mensagens enviadas com sucesso
- `failed_messages` - Mensagens que falharam
- `total_runs` - Total de execuções do sistema

### Logs

Para ver logs detalhados:
1. Acesse o Render Dashboard
2. Vá em **Logs**
3. Procure por:
   - `✓ Mensagem enviada para...`
   - `✓ Evento XXX processado`

## 🔧 Solução de Problemas

### Problema: Mensagens não sendo enviadas

**Verificar:**
1. A situação está na lista de ativas?
2. O telefone do associado está correto?
3. Há créditos no UppChannel?
4. Os logs mostram algum erro?

### Problema: Mensagem com formatação errada

**Solução:**
1. Verifique se todas as variáveis estão corretas
2. Use `\n` para quebra de linha
3. Use `*texto*` para negrito no WhatsApp

### Problema: Muitas mensagens duplicadas

**Solução:**
O sistema já previne duplicatas automaticamente. Se houver duplicatas:
1. Verifique o intervalo de execução
2. Confirme se não há múltiplas instâncias rodando

## 📚 Arquivos Relacionados

- `config_completo.json` - Configuração completa com todas as 27 situações
- `configurador_27_situacoes.html` - Interface visual para editar
- `Situacoes_Configuradas.pdf` - Documentação em PDF
- `situacoes_resumo.txt` - Lista resumida

## 🆘 Suporte

Para mais informações:
- **README.md principal** - Documentação completa do sistema
- **DEPLOY_GUIDE.md** - Guia passo a passo de deploy
- **Logs do Render** - Para troubleshooting em tempo real

---

✅ **Sistema pronto para uso com 27 situações ativas!**

Todas as mensagens serão enviadas automaticamente quando o status do evento mudar.
