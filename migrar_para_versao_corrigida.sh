#!/bin/bash
# Script de Migração para Versão Corrigida
# Data: 16/02/2026

echo "=========================================="
echo "  Migração para Versão Corrigida"
echo "  Sistema Hinova → UppChannel"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está no diretório correto
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Erro: app.py não encontrado${NC}"
    echo "Execute este script no diretório do projeto"
    exit 1
fi

echo -e "${YELLOW}📋 Passo 1: Fazendo backup do app.py original...${NC}"
if [ -f "app_ORIGINAL_BACKUP.py" ]; then
    echo -e "${YELLOW}⚠️  Backup já existe, criando backup com timestamp...${NC}"
    cp app.py "app_BACKUP_$(date +%Y%m%d_%H%M%S).py"
else
    cp app.py app_ORIGINAL_BACKUP.py
fi
echo -e "${GREEN}✅ Backup criado${NC}"
echo ""

echo -e "${YELLOW}📋 Passo 2: Verificando se app_CORRIGIDO.py existe...${NC}"
if [ ! -f "app_CORRIGIDO.py" ]; then
    echo -e "${RED}❌ Erro: app_CORRIGIDO.py não encontrado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Arquivo corrigido encontrado${NC}"
echo ""

echo -e "${YELLOW}📋 Passo 3: Substituindo app.py pela versão corrigida...${NC}"
cp app_CORRIGIDO.py app.py
echo -e "${GREEN}✅ Arquivo substituído${NC}"
echo ""

echo -e "${YELLOW}📋 Passo 4: Verificando banco de dados...${NC}"
if [ -f "/tmp/hinova_messages.db" ]; then
    echo -e "${YELLOW}⚠️  Banco de dados existente encontrado${NC}"
    echo -e "${YELLOW}   A nova tabela 'evento_historico' será criada automaticamente${NC}"
else
    echo -e "${GREEN}✅ Banco será criado na primeira execução${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo "=========================================="
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Se estiver usando Git:"
echo "   git add app.py"
echo "   git commit -m 'Aplicar correções críticas de notificação'"
echo "   git push"
echo ""
echo "2. No Render:"
echo "   - Acesse o dashboard"
echo "   - Clique em 'Manual Deploy'"
echo "   - Aguarde o deploy completar"
echo ""
echo "3. Após o deploy:"
echo "   - Acesse https://seu-app.onrender.com"
echo "   - Clique em 'Executar Agora'"
echo "   - Verifique os logs"
echo ""
echo "4. Procure nos logs por:"
echo "   - '🚀 Sistema CORRIGIDO iniciando...'"
echo "   - '📅 Buscando eventos dos últimos 7 dias'"
echo "   - '📊 RESUMO DO PROCESSAMENTO'"
echo ""
echo "=========================================="
echo ""
echo "📚 Documentação disponível:"
echo "   - RESUMO_ANALISE.md (leia primeiro!)"
echo "   - DIAGNOSTICO_PROBLEMAS.md"
echo "   - GUIA_IMPLEMENTACAO.md"
echo "   - MELHORIAS_RECOMENDADAS.md"
echo ""
echo "🔄 Para reverter (se necessário):"
echo "   cp app_ORIGINAL_BACKUP.py app.py"
echo ""
