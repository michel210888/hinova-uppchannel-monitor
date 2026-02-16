#!/usr/bin/env python3
"""
Script para adicionar uma rota de debug que mostra a estrutura real dos eventos
Este script será temporário - apenas para descobrir os campos corretos
"""

import requests
import json
import os
from datetime import datetime, timedelta

def debug_eventos():
    """Tenta listar eventos e mostra a estrutura completa"""
    
    HINOVA_TOKEN = os.environ.get('HINOVA_TOKEN', '')
    HINOVA_USUARIO = os.environ.get('HINOVA_USUARIO', 'roboeventos')
    HINOVA_SENHA = os.environ.get('HINOVA_SENHA', '')
    
    BASE_URL = "https://api.hinova.com.br/api/sga/v2"
    
    resultado = {
        "etapa": "",
        "auth_status": None,
        "auth_response": None,
        "eventos_status": None,
        "eventos_count": 0,
        "primeiro_evento_completo": None,
        "primeiro_evento_keys": [],
        "campos_situacao": {},
        "amostra_situacoes": [],
        "erro": None
    }
    
    try:
        # Autenticar
        resultado["etapa"] = "autenticacao"
        auth_url = f"{BASE_URL}/usuario/autenticar"
        headers = {"Authorization": f"Bearer {HINOVA_TOKEN}"}
        payload = {"usuario": HINOVA_USUARIO, "senha": HINOVA_SENHA}
        
        response = requests.post(auth_url, json=payload, headers=headers, timeout=30)
        resultado["auth_status"] = response.status_code
        auth_data = response.json()
        resultado["auth_response"] = {k: str(v)[:50] for k, v in auth_data.items()}
        
        user_token = auth_data.get('token_usuario') or auth_data.get('token')
        
        if not user_token:
            resultado["erro"] = f"Token não encontrado. Keys: {list(auth_data.keys())}"
            return resultado
        
        # Listar eventos
        resultado["etapa"] = "listar_eventos"
        hoje = datetime.now().strftime('%d/%m/%Y')
        
        eventos_url = f"{BASE_URL}/listar/evento"
        eventos_payload = {
            "data_cadastro": hoje,
            "data_cadastro_final": hoje
        }
        
        eventos_headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(eventos_url, json=eventos_payload, headers=eventos_headers, timeout=30)
        resultado["eventos_status"] = response.status_code
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                eventos = data
                resultado["formato"] = "lista_direta"
            elif isinstance(data, dict):
                eventos = data.get('eventos', [])
                resultado["formato"] = f"objeto_keys={list(data.keys())}"
            else:
                resultado["formato"] = f"desconhecido={type(data)}"
                eventos = []
            
            resultado["eventos_count"] = len(eventos)
            
            if len(eventos) > 0:
                # Primeiro evento completo
                resultado["primeiro_evento_completo"] = eventos[0]
                resultado["primeiro_evento_keys"] = list(eventos[0].keys()) if isinstance(eventos[0], dict) else []
                
                # Campos de situação
                primeiro = eventos[0]
                if isinstance(primeiro, dict):
                    for key in primeiro.keys():
                        if 'sit' in key.lower() or 'status' in key.lower():
                            resultado["campos_situacao"][key] = primeiro[key]
                
                # Amostra de situações de vários eventos
                for evt in eventos[:5]:
                    if isinstance(evt, dict):
                        amostra = {
                            "protocolo": evt.get('protocolo'),
                            "situacao": evt.get('situacao'),
                            "situacao_codigo": evt.get('situacao_codigo'),
                            "codigo_situacao": evt.get('codigo_situacao'),
                            "situacao_nome": evt.get('situacao_nome'),
                            "nome_situacao": evt.get('nome_situacao'),
                            "situacao_id": evt.get('situacao_id'),
                            "id_situacao": evt.get('id_situacao'),
                        }
                        resultado["amostra_situacoes"].append(amostra)
        else:
            resultado["erro"] = f"HTTP {response.status_code}: {response.text[:200]}"
        
        resultado["etapa"] = "concluido"
        
    except Exception as e:
        resultado["erro"] = str(e)
    
    return resultado

if __name__ == "__main__":
    result = debug_eventos()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
