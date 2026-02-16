#!/usr/bin/env python3
"""
Script de debug para inspecionar a estrutura real dos eventos da API Hinova
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Credenciais
HINOVA_TOKEN = os.environ.get('HINOVA_TOKEN', 'ef9be58415741701f2dc63a3192d8f0ef9b4d7aa10c34f66d12ee16fcae8a258a8c8616d608aa2ed44559e7fb50c40bab4c9ca4ed76807307a5c8cff4ca0b77c842015788f1316a175c12510a726df396a278d369391b6c2f34750e9ae1ca1bfb07cb99c7b7fb804bae55850a966c8bfb5e842a01aa0a26a57acf6c9220669b0d949ccbc9d068462df5f2246c5d88133')
HINOVA_USUARIO = os.environ.get('HINOVA_USUARIO', 'roboeventos')
HINOVA_SENHA = os.environ.get('HINOVA_SENHA', 'Ubho3592#')

BASE_URL = "https://api.hinova.com.br/api/sga/v2"

print("=" * 70)
print("DEBUG API HINOVA - Inspecionar Estrutura dos Eventos")
print("=" * 70)
print()

# Passo 1: Autenticar
print("1. Autenticando...")
auth_url = f"{BASE_URL}/usuario/autenticar"
auth_headers = {"Authorization": f"Bearer {HINOVA_TOKEN}"}
auth_payload = {"usuario": HINOVA_USUARIO, "senha": HINOVA_SENHA}

try:
    response = requests.post(auth_url, json=auth_payload, headers=auth_headers, timeout=30)
    print(f"   Status: {response.status_code}")
    auth_data = response.json()
    
    if 'error' in auth_data:
        print(f"   ERRO: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")
        
        # Tentar com user_token direto
        print()
        print("   Tentando autenticar com token direto...")
        auth_headers2 = {"Authorization": HINOVA_TOKEN}
        response2 = requests.post(auth_url, json=auth_payload, headers=auth_headers2, timeout=30)
        print(f"   Status: {response2.status_code}")
        auth_data = response2.json()
        print(f"   Resposta: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")
        
        if 'error' in auth_data:
            print("\n   Tentando sem Bearer...")
            headers3 = {"token": HINOVA_TOKEN, "Content-Type": "application/json"}
            response3 = requests.post(auth_url, json=auth_payload, headers=headers3, timeout=30)
            print(f"   Status: {response3.status_code}")
            auth_data = response3.json()
            print(f"   Resposta: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")
    
    # Pegar user_token
    user_token = auth_data.get('token_usuario') or auth_data.get('token') or auth_data.get('user_token')
    
    if not user_token:
        print(f"\n   Todas as keys: {list(auth_data.keys())}")
        print(f"   Resposta completa: {json.dumps(auth_data, indent=2, ensure_ascii=False)}")
        
        # Tentar usar o HINOVA_TOKEN direto como user_token
        print("\n   Tentando usar HINOVA_TOKEN direto para listar eventos...")
        user_token = HINOVA_TOKEN
    
    print(f"   Token obtido: {str(user_token)[:40]}...")
    print()
    
    # Passo 2: Listar eventos
    print("2. Listando eventos...")
    hoje = datetime.now().strftime('%d/%m/%Y')
    
    eventos_url = f"{BASE_URL}/listar/evento"
    eventos_payload = {
        "data_cadastro": hoje,
        "data_cadastro_final": hoje
    }
    
    # Tentar várias combinações de headers
    headers_options = [
        {"Authorization": user_token, "Content-Type": "application/json"},
        {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"},
        {"Authorization": f"Bearer {HINOVA_TOKEN}", "token": user_token, "Content-Type": "application/json"},
    ]
    
    for i, headers in enumerate(headers_options):
        print(f"\n   Tentativa {i+1}...")
        response = requests.post(eventos_url, json=eventos_payload, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                eventos = data
                print(f"   Formato: LISTA direta com {len(eventos)} itens")
            elif isinstance(data, dict):
                eventos = data.get('eventos', data.get('data', []))
                print(f"   Formato: OBJETO com keys: {list(data.keys())}")
                print(f"   Eventos: {len(eventos)} itens")
            else:
                print(f"   Formato desconhecido: {type(data)}")
                continue
            
            if len(eventos) > 0:
                print()
                print("=" * 70)
                print("3. ESTRUTURA DO PRIMEIRO EVENTO:")
                print("=" * 70)
                primeiro = eventos[0]
                print(json.dumps(primeiro, indent=2, ensure_ascii=False))
                
                print()
                print("=" * 70)
                print("4. TODAS AS KEYS DO EVENTO:")
                print("=" * 70)
                if isinstance(primeiro, dict):
                    for key in sorted(primeiro.keys()):
                        valor = primeiro[key]
                        tipo = type(valor).__name__
                        if isinstance(valor, dict):
                            print(f"   {key}: (dict) keys={list(valor.keys())}")
                        elif isinstance(valor, list):
                            print(f"   {key}: (list) len={len(valor)}")
                        else:
                            print(f"   {key}: ({tipo}) = {valor}")
                
                # Procurar campos de situação
                print()
                print("=" * 70)
                print("5. CAMPOS RELACIONADOS A SITUAÇÃO:")
                print("=" * 70)
                for key in primeiro.keys():
                    key_lower = key.lower()
                    if 'sit' in key_lower or 'status' in key_lower or 'codigo' in key_lower:
                        print(f"   {key} = {primeiro[key]}")
                
                # Se tem campo 'situacao'
                if 'situacao' in primeiro:
                    sit = primeiro['situacao']
                    print(f"\n   Campo 'situacao' encontrado!")
                    print(f"   Tipo: {type(sit)}")
                    print(f"   Valor: {sit}")
                    if isinstance(sit, dict):
                        print(f"   Sub-keys: {list(sit.keys())}")
                        for k, v in sit.items():
                            print(f"     {k} = {v}")
                
                # Mostrar mais eventos para comparar
                if len(eventos) > 1:
                    print()
                    print("=" * 70)
                    print("6. SITUAÇÕES DE TODOS OS EVENTOS:")
                    print("=" * 70)
                    for evt in eventos[:10]:
                        prot = evt.get('protocolo', '?')
                        # Tentar vários campos
                        sit_obj = evt.get('situacao')
                        sit_cod = evt.get('situacao_codigo') or evt.get('codigo_situacao')
                        sit_nome = evt.get('situacao_nome') or evt.get('nome_situacao')
                        sit_id = evt.get('situacao_id') or evt.get('id_situacao')
                        
                        print(f"   Protocolo {prot}:")
                        print(f"     situacao = {sit_obj}")
                        print(f"     situacao_codigo = {sit_cod}")
                        print(f"     situacao_nome = {sit_nome}")
                        print(f"     situacao_id = {sit_id}")
                        print()
                
                break
            else:
                print("   Nenhum evento encontrado")
        else:
            print(f"   Erro: {response.text[:200]}")

except Exception as e:
    print(f"ERRO: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("FIM DO DEBUG")
print("=" * 70)
