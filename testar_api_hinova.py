#!/usr/bin/env python3
"""
Script de teste para verificar formato da resposta da API Hinova
"""

import requests
import json
from datetime import datetime, timedelta

# Credenciais do config.json
HINOVA_TOKEN = "ef9be58415741701f2dc63a3192d8f0ef9b4d7aa10c34f66d12ee16fcae8a258a8c8616d608aa2ed44559e7fb50c40bab4c9ca4ed76807307a5c8cff4ca0b77c842015788f1316a175c12510a726df396a278d369391b6c2f34750e9ae1ca1bfb07cb99c7b7fb804bae55850a966c8bfb5e842a01aa0a26a57acf6c9220669b0d949ccbc9d068462df5f2246c5d88133"
HINOVA_USUARIO = "roboeventos"
HINOVA_SENHA = "Ubho3592#"

BASE_URL = "https://api.hinova.com.br/api/sga/v2"

print("=" * 60)
print("TESTE DA API HINOVA - Verificar Formato de Resposta")
print("=" * 60)
print()

# Passo 1: Autenticar
print("🔑 Passo 1: Autenticando...")
auth_url = f"{BASE_URL}/usuario/autenticar"
auth_headers = {"Authorization": f"Bearer {HINOVA_TOKEN}"}
auth_payload = {
    "usuario": HINOVA_USUARIO,
    "senha": HINOVA_SENHA
}

try:
    response = requests.post(auth_url, json=auth_payload, headers=auth_headers, timeout=30)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        auth_data = response.json()
        print(f"   ✓ Autenticação bem-sucedida!")
        print(f"   Keys na resposta: {list(auth_data.keys())}")
        
        user_token = auth_data.get('token_usuario') or auth_data.get('token')
        
        if not user_token:
            print(f"   ❌ Token não encontrado na resposta!")
            print(f"   Resposta completa: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")
            exit(1)
        
        print(f"   User token: {user_token[:30]}...")
        print()
        
        # Passo 2: Listar eventos
        print("📋 Passo 2: Listando eventos...")
        
        # Buscar eventos de hoje
        hoje = datetime.now().strftime('%d/%m/%Y')
        
        eventos_url = f"{BASE_URL}/listar/evento"
        eventos_payload = {
            "data_cadastro": hoje,
            "data_cadastro_final": hoje
        }
        
        # Testar com user_token no Authorization
        eventos_headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        print(f"   URL: {eventos_url}")
        print(f"   Payload: {eventos_payload}")
        print(f"   Buscando eventos de: {hoje}")
        print()
        
        response = requests.post(eventos_url, json=eventos_payload, headers=eventos_headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✓ Requisição bem-sucedida!")
            print()
            
            # Analisar resposta
            resposta = response.json()
            
            print("📊 ANÁLISE DA RESPOSTA:")
            print(f"   Tipo da resposta: {type(resposta)}")
            print()
            
            if isinstance(resposta, dict):
                print(f"   ✓ Resposta é um dicionário")
                print(f"   Keys disponíveis: {list(resposta.keys())}")
                print()
                
                # Verificar se tem 'eventos'
                if 'eventos' in resposta:
                    eventos = resposta['eventos']
                    print(f"   ✓ Campo 'eventos' encontrado!")
                    print(f"   Tipo de 'eventos': {type(eventos)}")
                    print(f"   Quantidade de eventos: {len(eventos) if isinstance(eventos, list) else 'N/A'}")
                    
                    if isinstance(eventos, list) and len(eventos) > 0:
                        print()
                        print("   📝 Primeiro evento:")
                        print(f"   Tipo: {type(eventos[0])}")
                        if isinstance(eventos[0], dict):
                            print(f"   Keys: {list(eventos[0].keys())}")
                            print()
                            print("   Dados completos do primeiro evento:")
                            print(json.dumps(eventos[0], indent=2, ensure_ascii=False))
                else:
                    print(f"   ❌ Campo 'eventos' NÃO encontrado!")
                    print()
                    print("   Resposta completa:")
                    print(json.dumps(resposta, indent=2, ensure_ascii=False))
                    
            elif isinstance(resposta, list):
                print(f"   ✓ Resposta é uma LISTA diretamente!")
                print(f"   Quantidade de itens: {len(resposta)}")
                
                if len(resposta) > 0:
                    print()
                    print("   📝 Primeiro item:")
                    print(f"   Tipo: {type(resposta[0])}")
                    if isinstance(resposta[0], dict):
                        print(f"   Keys: {list(resposta[0].keys())}")
                        print()
                        print("   Dados completos do primeiro item:")
                        print(json.dumps(resposta[0], indent=2, ensure_ascii=False))
            else:
                print(f"   ⚠️ Formato inesperado: {type(resposta)}")
                print(f"   Resposta: {resposta}")
                
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            print(f"   Resposta: {response.text[:500]}")
            
    else:
        print(f"   ❌ Erro na autenticação: {response.status_code}")
        print(f"   Resposta: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Erro: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("FIM DO TESTE")
print("=" * 60)
