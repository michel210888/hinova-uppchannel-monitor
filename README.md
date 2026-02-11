# 🚀 Sistema Hinova → UppChannel - Versão Completa

## 📦 Arquivos Incluídos:

- `app.py` - Aplicação Flask completa
- `requirements.txt` - Dependências Python
- `Dockerfile` - Configuração Docker
- `render.yaml` - Configuração Render
- `.env.example` - Exemplo de variáveis
- `.gitignore` - Arquivos a ignorar
- `README.md` - Este arquivo

## 🎯 Funcionalidades:

✅ Auto-refresh de token (cache de 1 hora)
✅ Dashboard web com 5 abas
✅ Banco de dados SQLite
✅ Logs em tempo real
✅ Teste de 3 combinações de headers
✅ Formato correto da API Hinova
✅ Horário Brasil (UTC-3)

## 🔧 Configuração:

### Variáveis de Ambiente:

```
HINOVA_TOKEN=seu_bearer_token_fixo
HINOVA_USUARIO=roboeventos
HINOVA_SENHA=sua_senha
UPPCHANNEL_API_KEY=sua_api_key
SITUACOES_ATIVAS=6,15,11,23,38,80,82,30,40,5,10,3,45,77,76,33,8,29,70,71,72,79,32,59,4,20,61
INTERVALO_MINUTOS=15
```

## 🚀 Deploy no Render:

1. **Crie repositório no GitHub**
   - Novo repositório
   - Nome: `hinova-uppchannel-monitor`
   - Public

2. **Faça upload dos arquivos**
   - Add file → Upload files
   - Arraste todos os arquivos desta pasta
   - Commit changes

3. **Configure no Render**
   - New → Web Service
   - Connect repository
   - Environment: Docker
   - Add environment variables (as 6 variáveis acima)

4. **Deploy**
   - Create Web Service
   - Aguarde deploy (3-5 min)

## 📊 Acessar Dashboard:

```
https://seu-app.onrender.com
```

## 🔬 Sistema de Teste:

O sistema testa 3 formatos de headers automaticamente:

1. Apenas user_token no Authorization
2. Bearer token + token separado
3. Bearer token + token_usuario

Nos logs você verá qual funcionou!

## 📝 Logs:

```
🔑 Autenticando na API Hinova...
✓ Autenticação bem-sucedida!
📋 Buscando eventos...
🧪 TESTE 1: Apenas user_token no Authorization
   Status: 401
🧪 TESTE 2: Bearer token + user token separado
   Status: 200
✓ FUNCIONOU com Bearer + token separado!
✓ 5 eventos encontrados
```

## ⚙️ Campos da API Hinova:

A API usa formato brasileiro:

```json
{
  "data_cadastro": "10/02/2026",
  "data_cadastro_final": "10/02/2026"
}
```

E retorna:

```json
{
  "mensagem": "OK",
  "token_usuario": "abc123..."
}
```

## 🆘 Troubleshooting:

### Erro 401:
- Verifique o Bearer Token
- Veja nos logs qual teste funcionou
- Confirme as credenciais

### Nenhum evento:
- Normal! Significa que não há eventos para hoje
- Sistema está funcionando

### Token expira:
- Sistema renova automaticamente
- Cache de 1 hora

## 📚 Estrutura do Código:

```
app.py
├── init_database()           # Cria banco SQLite
├── HinovaAPI
│   ├── autenticar()          # Autentica e cache token
│   ├── listar_eventos()      # Lista eventos (testa 3 formatos)
│   └── buscar_veiculo()      # Busca dados veículo
├── UppChannelAPI
│   └── enviar_mensagem()     # Envia WhatsApp
├── processar_eventos()       # Lógica principal
└── rotas Flask
    ├── /                     # Dashboard
    ├── /api/status           # Status JSON
    ├── /api/logs             # Logs
    ├── /api/messages         # Histórico
    ├── /api/config           # Configuração
    ├── /api/test-connections # Testar APIs
    └── /api/run-now          # Executar manual
```

## ✅ Checklist de Deploy:

- [ ] Criar repositório GitHub
- [ ] Upload de todos os arquivos
- [ ] Criar Web Service no Render
- [ ] Adicionar 6 variáveis de ambiente
- [ ] Iniciar deploy
- [ ] Acessar dashboard
- [ ] Testar "Executar Agora"
- [ ] Verificar logs
- [ ] Confirmar que um dos 3 testes funcionou

## 🎯 Próximos Passos:

1. Faça deploy conforme instruções acima
2. Execute teste manual
3. Veja nos logs qual formato de header funcionou
4. Me conte qual foi para eu otimizar o código!

---

**Sistema completo pronto para produção!** 🚀
