#!/usr/bin/env python3
"""
Script de Validação de Credenciais
Testa as credenciais antes de fazer o deploy
"""

import requests
import json
import sys

def banner():
    print("=" * 60)
    print("  🔍 VALIDADOR DE CREDENCIAIS")
    print("  Sistema Hinova → UppChannel")
    print("=" * 60)
    print()

def testar_hinova(token, usuario, senha):
    """Testa autenticação na API Hinova"""
    print("📡 Testando Hinova SGA...")
    
    try:
        url = "https://api.hinova.com.br/api/sga/v2/usuario/autenticar"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"usuario": usuario, "senha": senha}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('token'):
                print("   ✅ Autenticação Hinova OK")
                print(f"   → Token de usuário obtido: {data['token'][:20]}...")
                return True, data['token']
            else:
                print("   ❌ Resposta sem token")
                return False, None
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            print(f"   → {response.text[:200]}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("   ❌ Timeout - API não respondeu em 30s")
        return False, None
    except requests.exceptions.ConnectionError:
        print("   ❌ Erro de conexão - Verifique sua internet")
        return False, None
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False, None

def testar_hinova_listar(token, user_token):
    """Testa listagem de eventos"""
    print("\n📋 Testando listagem de eventos...")
    
    try:
        from datetime import datetime
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        url = "https://api.hinova.com.br/api/sga/v2/listar/evento"
        headers = {
            "Authorization": f"Bearer {token}",
            "token": user_token
        }
        payload = {
            "data_inicio": hoje,
            "data_fim": hoje
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('eventos', [])
            print(f"   ✅ API de eventos OK")
            print(f"   → {len(eventos)} eventos encontrados para hoje")
            return True
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def testar_uppchannel(api_key):
    """Testa API UppChannel (teste básico de conectividade)"""
    print("\n📱 Testando UppChannel...")
    
    try:
        # Teste básico - enviar para número inválido só pra verificar se a API responde
        url = "https://api.uppchannel.com.br/chat/v1/message/send"
        headers = {
            "Content-Type": "application/json",
            "apikey": api_key
        }
        payload = {
            "number": "0000000000",  # Número inválido de propósito
            "message": "teste"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Qualquer resposta (mesmo erro) indica que a API key está sendo processada
        if response.status_code in [200, 400, 401]:
            if response.status_code == 401:
                print("   ❌ API Key inválida")
                return False
            else:
                print("   ✅ UppChannel API OK")
                print(f"   → API Key aceita (status {response.status_code})")
                return True
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def validar_situacoes(situacoes_str):
    """Valida string de situações"""
    print("\n🔢 Validando situações...")
    
    try:
        situacoes = [int(x.strip()) for x in situacoes_str.split(',')]
        print(f"   ✅ {len(situacoes)} situações configuradas")
        print(f"   → Códigos: {', '.join(map(str, situacoes[:10]))}{'...' if len(situacoes) > 10 else ''}")
        return True
    except Exception as e:
        print(f"   ❌ Formato inválido: {e}")
        return False

def main():
    banner()
    
    print("Digite suas credenciais para validação:")
    print("(ou deixe em branco para usar valores de exemplo)\n")
    
    # Coletar credenciais
    token = input("Token Hinova SGA: ").strip()
    usuario = input("Usuário SGA: ").strip()
    senha = input("Senha SGA: ").strip()
    api_key_upp = input("API Key UppChannel: ").strip()
    situacoes = input("Situações ativas (ex: 6,15,11,...) [padrão: 27 situações]: ").strip()
    
    if not situacoes:
        situacoes = "6,15,11,23,38,80,82,30,40,5,10,3,45,77,76,33,8,29,70,71,72,79,32,59,4,20,61"
    
    print("\n" + "=" * 60)
    print("  INICIANDO VALIDAÇÃO")
    print("=" * 60 + "\n")
    
    resultados = {
        'hinova_auth': False,
        'hinova_eventos': False,
        'uppchannel': False,
        'situacoes': False
    }
    
    # Testar Hinova
    if token and usuario and senha:
        success, user_token = testar_hinova(token, usuario, senha)
        resultados['hinova_auth'] = success
        
        if success and user_token:
            resultados['hinova_eventos'] = testar_hinova_listar(token, user_token)
    else:
        print("⚠️  Credenciais Hinova não fornecidas - pulando teste\n")
    
    # Testar UppChannel
    if api_key_upp:
        resultados['uppchannel'] = testar_uppchannel(api_key_upp)
    else:
        print("\n⚠️  API Key UppChannel não fornecida - pulando teste\n")
    
    # Validar situações
    resultados['situacoes'] = validar_situacoes(situacoes)
    
    # Resumo
    print("\n" + "=" * 60)
    print("  📊 RESUMO DA VALIDAÇÃO")
    print("=" * 60 + "\n")
    
    total = len(resultados)
    passou = sum(resultados.values())
    
    for teste, resultado in resultados.items():
        status = "✅ OK" if resultado else "❌ FALHOU"
        print(f"{status} - {teste.replace('_', ' ').title()}")
    
    print(f"\nResultado: {passou}/{total} testes passaram")
    
    if passou == total:
        print("\n🎉 TUDO OK! Suas credenciais estão corretas.")
        print("   Pode prosseguir com o deploy no Render.\n")
        return 0
    else:
        print("\n⚠️  ATENÇÃO! Alguns testes falharam.")
        print("   Corrija os problemas antes de fazer o deploy.\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Validação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
