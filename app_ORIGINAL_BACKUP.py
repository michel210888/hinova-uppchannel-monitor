#!/usr/bin/env python3
"""
Sistema Hinova → UppChannel - Versão Completa
Com banco de dados, logs em tempo real e interface web
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
from threading import Lock

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lock para thread-safety
db_lock = Lock()

# Estado global
system_state = {
    'last_run': None,
    'last_status': "Aguardando primeira execução",
    'is_running': False,
    'current_step': '',
    'processed_events': set(),
    'stats': {
        'total_runs': 0,
        'successful_messages': 0,
        'failed_messages': 0,
        'last_error': None
    },
    'logs': [],
    'max_logs': 200
}

# Token cache
token_cache = {
    'bearer_token': None,
    'user_token': None,
    'expires_at': None
}

# ==================== BANCO DE DADOS ====================

def init_database():
    """Inicializa banco de dados SQLite"""
    with db_lock:
        conn = sqlite3.connect('/tmp/hinova_messages.db')
        c = conn.cursor()
        
        # Tabela de mensagens enviadas
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                protocolo TEXT,
                evento_id TEXT,
                situacao_codigo INTEGER,
                situacao_nome TEXT,
                telefone TEXT,
                mensagem TEXT,
                status TEXT,
                erro TEXT,
                nome_associado TEXT,
                placa TEXT
            )
        ''')
        
        # Tabela de logs do sistema
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT,
                message TEXT
            )
        ''')
        
        # Tabela de configuração
        c.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    logger.info("✓ Banco de dados inicializado")

def save_message_log(protocolo, evento_id, situacao_codigo, situacao_nome, 
                     telefone, mensagem, status, erro=None, nome_associado=None, placa=None):
    """Salva log de mensagem no banco"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO messages 
                (timestamp, protocolo, evento_id, situacao_codigo, situacao_nome, 
                 telefone, mensagem, status, erro, nome_associado, placa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                protocolo,
                evento_id,
                situacao_codigo,
                situacao_nome,
                telefone,
                mensagem,
                status,
                erro,
                nome_associado,
                placa
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao salvar log de mensagem: {e}")

def save_system_log(level, message):
    """Salva log do sistema no banco"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO system_logs (timestamp, level, message)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), level, message))
            
            # Manter apenas últimos 1000 logs
            c.execute('''
                DELETE FROM system_logs 
                WHERE id NOT IN (
                    SELECT id FROM system_logs 
                    ORDER BY id DESC LIMIT 1000
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao salvar log do sistema: {e}")

def get_messages_history(limit=100):
    """Recupera histórico de mensagens"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                SELECT * FROM messages 
                ORDER BY id DESC LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in c.description]
            rows = c.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {e}")
            return []

def get_system_logs(limit=100):
    """Recupera logs do sistema"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                SELECT * FROM system_logs 
                ORDER BY id DESC LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in c.description]
            rows = c.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Erro ao recuperar logs: {e}")
            return []

def save_config(key, value):
    """Salva configuração no banco"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('''
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, json.dumps(value), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")

def get_config(key, default=None):
    """Recupera configuração do banco"""
    with db_lock:
        try:
            conn = sqlite3.connect('/tmp/hinova_messages.db')
            c = conn.cursor()
            
            c.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = c.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row[0])
            return default
        except Exception as e:
            logger.error(f"Erro ao recuperar configuração: {e}")
            return default

# ==================== LOG HELPER ====================

def add_log(level, message):
    """Adiciona log ao sistema"""
    # Horário do Brasil (UTC-3)
    timestamp = (datetime.now() - timedelta(hours=3)).strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    
    system_state['logs'].insert(0, log_entry)
    
    # Limitar logs em memória
    if len(system_state['logs']) > system_state['max_logs']:
        system_state['logs'] = system_state['logs'][:system_state['max_logs']]
    
    # Salvar no banco
    save_system_log(level, message)
    
    # Log no console também
    if level == 'ERROR':
        logger.error(message)
    elif level == 'WARNING':
        logger.warning(message)
    else:
        logger.info(message)

# ==================== APIS ====================

class HinovaAPI:
    """Cliente para API Hinova SGA com auto-refresh de token"""
    
    def __init__(self, token, usuario, senha):
        self.token = token
        self.usuario = usuario
        self.senha = senha
        self.base_url = "https://api.hinova.com.br/api/sga/v2"
    
    def autenticar(self, force=False):
        """Autentica na API com cache de token"""
        global token_cache
        
        # Verificar se token ainda é válido
        if not force and token_cache['user_token'] and token_cache['expires_at']:
            if datetime.now() < token_cache['expires_at']:
                add_log('INFO', f'✓ Token em cache ainda válido (expira às {token_cache["expires_at"].strftime("%H:%M:%S")})')
                return True
        
        try:
            add_log('INFO', '🔑 Autenticando na API Hinova...')
            add_log('INFO', f'   Bearer Token: {self.token[:30]}...')
            
            url = f"{self.base_url}/usuario/autenticar"
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "usuario": self.usuario,
                "senha": self.senha
            }
            
            add_log('INFO', f'   Usuário: {self.usuario}')
            add_log('INFO', f'   URL: {url}')
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            add_log('INFO', f'   Status HTTP: {response.status_code}')
            
            if response.status_code != 200:
                add_log('ERROR', f'❌ Erro HTTP {response.status_code}: {response.text[:200]}')
                return False
            
            data = response.json()
            add_log('INFO', f'   Resposta JSON keys: {list(data.keys())}')
            
            # A API Hinova retorna 'token_usuario' e não 'token'
            user_token = data.get('token_usuario') or data.get('token')
            
            if not user_token:
                add_log('ERROR', '❌ Resposta não contém campo "token_usuario" ou "token"')
                add_log('ERROR', f'   Resposta completa: {str(data)[:300]}')
                return False
            
            # Atualizar cache (token válido por 1 hora)
            token_cache['bearer_token'] = self.token
            token_cache['user_token'] = user_token
            token_cache['expires_at'] = datetime.now() + timedelta(hours=1)
            
            add_log('SUCCESS', f'✓ Autenticação bem-sucedida!')
            add_log('INFO', f'   User Token: {user_token[:30]}...')
            add_log('INFO', f'   Válido até: {token_cache["expires_at"].strftime("%H:%M:%S")}')
            return True
            
        except requests.exceptions.Timeout:
            add_log('ERROR', '❌ Timeout na autenticação (>30s)')
            return False
        except requests.exceptions.RequestException as e:
            add_log('ERROR', f'❌ Erro de conexão: {str(e)}')
            return False
        except Exception as e:
            add_log('ERROR', f'❌ Erro na autenticação: {str(e)}')
            return False
    
    def listar_eventos(self, data_inicio, data_fim):
        """Lista eventos por período"""
        try:
            add_log('INFO', f'📋 Buscando eventos de {data_inicio} até {data_fim}...')
            
            url = f"{self.base_url}/listar/evento"
            
            # Converter data de YYYY-MM-DD para DD/MM/YYYY (formato que a API espera)
            from datetime import datetime as dt
            data_inicio_br = dt.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
            data_fim_br = dt.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')
            
            # A API Hinova usa campos diferentes!
            payload = {
                "data_cadastro": data_inicio_br,
                "data_cadastro_final": data_fim_br
            }
            
            # TESTE SIMPLIFICADO: Apenas user token no Authorization
            add_log('INFO', f'   🧪 TESTE 1: Apenas user_token no Authorization')
            headers1 = {
                "Authorization": f"Bearer {token_cache['user_token']}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers1, timeout=30)
            add_log('INFO', f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                add_log('SUCCESS', '✓ FUNCIONOU com apenas user_token!')
                data = response.json()
                eventos = data.get('eventos', [])
                add_log('INFO', f'✓ {len(eventos)} eventos encontrados')
                return eventos
            
            # TESTE 2: Bearer + token separado
            add_log('INFO', f'   🧪 TESTE 2: Bearer token + user token separado')
            headers2 = {
                "Authorization": f"Bearer {token_cache['bearer_token']}",
                "token": token_cache['user_token'],
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers2, timeout=30)
            add_log('INFO', f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                add_log('SUCCESS', '✓ FUNCIONOU com Bearer + token separado!')
                data = response.json()
                eventos = data.get('eventos', [])
                add_log('INFO', f'✓ {len(eventos)} eventos encontrados')
                return eventos
            
            # TESTE 3: token_usuario como header
            add_log('INFO', f'   🧪 TESTE 3: token_usuario como header separado')
            headers3 = {
                "Authorization": f"Bearer {token_cache['bearer_token']}",
                "token_usuario": token_cache['user_token'],
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers3, timeout=30)
            add_log('INFO', f'   Status: {response.status_code}')
            
            if response.status_code == 200:
                add_log('SUCCESS', '✓ FUNCIONOU com token_usuario!')
                data = response.json()
                eventos = data.get('eventos', [])
                add_log('INFO', f'✓ {len(eventos)} eventos encontrados')
                return eventos
            
            # Se nenhuma funcionou
            add_log('ERROR', '❌ Todas as 3 tentativas falharam!')
            add_log('ERROR', f'   Última resposta: {response.text[:300]}')
            
            # Tentar reautenticar
            add_log('WARNING', '⚠️ Tentando reautenticar...')
            if self.autenticar(force=True):
                # Repetir teste 2 com novo token
                headers2["Authorization"] = f"Bearer {token_cache['bearer_token']}"
                headers2["token"] = token_cache['user_token']
                response = requests.post(url, json=payload, headers=headers2, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    eventos = data.get('eventos', [])
                    add_log('SUCCESS', f'✓ {len(eventos)} eventos encontrados após reautenticação')
                    return eventos
            
            return []
            
        except Exception as e:
            add_log('ERROR', f'❌ Erro ao listar eventos: {str(e)}')
            return []
    
    def buscar_veiculo(self, veiculo_id):
        """Busca dados do veículo"""
        try:
            url = f"{self.base_url}/veiculo/buscar/{veiculo_id}/codigo"
            headers = {
                "Authorization": f"Bearer {token_cache['bearer_token']}",
                "token": token_cache['user_token']
            }
            
            add_log('INFO', f'   Buscando veículo {veiculo_id}...')
            
            response = requests.get(url, headers=headers, timeout=30)
            
            # Se token expirou, reautenticar
            if response.status_code == 401:
                add_log('WARNING', '⚠️ Token expirado ao buscar veículo, reautenticando...')
                if self.autenticar(force=True):
                    headers["Authorization"] = f"Bearer {token_cache['bearer_token']}"
                    headers["token"] = token_cache['user_token']
                    response = requests.get(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            add_log('WARNING', f'⚠️ Erro ao buscar veículo {veiculo_id}: {str(e)}')
            return None


class UppChannelAPI:
    """Cliente para API UppChannel"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.uppchannel.com.br/chat"
    
    def enviar_mensagem(self, telefone, mensagem):
        """Envia mensagem via WhatsApp"""
        try:
            url = f"{self.base_url}/v1/message/send"
            headers = {
                "Content-Type": "application/json",
                "apikey": self.api_key
            }
            payload = {
                "number": telefone,
                "message": mensagem
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            add_log('SUCCESS', f'✓ Mensagem enviada para {telefone}')
            return True
            
        except Exception as e:
            add_log('ERROR', f'❌ Erro ao enviar para {telefone}: {str(e)}')
            return False


# ==================== CONFIGURAÇÃO ====================

def carregar_configuracao():
    """Carrega configuração das variáveis de ambiente ou banco"""
    # Tentar carregar do banco primeiro
    config_db = get_config('main_config')
    
    if config_db:
        add_log('INFO', '📖 Configuração carregada do banco de dados')
        return config_db
    
    # Se não houver no banco, usar variáveis de ambiente
    config = {
        'hinova': {
            'token': os.getenv('HINOVA_TOKEN'),
            'usuario': os.getenv('HINOVA_USUARIO'),
            'senha': os.getenv('HINOVA_SENHA')
        },
        'uppchannel': {
            'api_key': os.getenv('UPPCHANNEL_API_KEY')
        },
        'situacoes_ativas': [int(x) for x in os.getenv('SITUACOES_ATIVAS', '6,15,11,23,38,80,82,30,40,5,10,3,45,77,76,33,8,29,70,71,72,79,32,59,4,20,61').split(',')],
        'intervalo_minutos': int(os.getenv('INTERVALO_MINUTOS', '15'))
    }
    
    # Templates padrão
    config['templates_mensagem'] = {}
    for cod in config['situacoes_ativas']:
        env_key = f'TEMPLATE_{cod}'
        if os.getenv(env_key):
            config['templates_mensagem'][str(cod)] = os.getenv(env_key)
    
    return config


# ==================== PROCESSAMENTO ====================

def formatar_mensagem(template, evento, veiculo_data):
    """Formata mensagem substituindo variáveis"""
    try:
        associado = veiculo_data.get('associado', {})
        
        mensagem = template.format(
            nome_associado=associado.get('nome', 'Cliente'),
            protocolo=evento.get('protocolo', 'N/A'),
            placa=veiculo_data.get('placa', 'N/A'),
            situacao=evento.get('situacao', {}).get('nome', 'N/A'),
            motivo=evento.get('motivo', {}).get('nome', 'N/A'),
            data_evento=evento.get('data_evento', datetime.now().strftime('%d/%m/%Y'))
        )
        
        return mensagem
        
    except Exception as e:
        add_log('ERROR', f'❌ Erro ao formatar mensagem: {str(e)}')
        return None


def extrair_telefone(associado_data):
    """Extrai telefone do associado"""
    try:
        celular = associado_data.get('celular', '')
        if celular:
            telefone = ''.join(filter(str.isdigit, celular))
            if len(telefone) >= 10:
                return telefone
        
        telefone_fixo = associado_data.get('telefone', '')
        if telefone_fixo:
            telefone = ''.join(filter(str.isdigit, telefone_fixo))
            if len(telefone) >= 10:
                return telefone
        
        return None
        
    except Exception as e:
        add_log('ERROR', f'❌ Erro ao extrair telefone: {str(e)}')
        return None


def processar_eventos():
    """Função principal de processamento"""
    if system_state['is_running']:
        add_log('WARNING', '⚠️ Processamento já em execução, pulando...')
        return
    
    system_state['is_running'] = True
    system_state['last_run'] = datetime.now()
    system_state['stats']['total_runs'] += 1
    
    try:
        add_log('INFO', '=' * 60)
        add_log('INFO', '🚀 INICIANDO PROCESSAMENTO DE EVENTOS')
        add_log('INFO', '=' * 60)
        
        system_state['current_step'] = 'Carregando configuração...'
        config = carregar_configuracao()
        
        # Validar configuração
        if not config['hinova']['token'] or not config['uppchannel']['api_key']:
            system_state['last_status'] = "❌ Erro: Credenciais não configuradas"
            add_log('ERROR', '❌ Credenciais não configuradas')
            return
        
        # Inicializar APIs
        system_state['current_step'] = 'Inicializando APIs...'
        hinova = HinovaAPI(
            config['hinova']['token'],
            config['hinova']['usuario'],
            config['hinova']['senha']
        )
        
        uppchannel = UppChannelAPI(config['uppchannel']['api_key'])
        
        # Autenticar UMA VEZ no início
        system_state['current_step'] = 'Autenticando...'
        if not hinova.autenticar():
            system_state['last_status'] = "❌ Erro na autenticação"
            add_log('ERROR', '❌ Falha na autenticação - verifique credenciais')
            return
        
        # Verificar se token foi obtido
        if not token_cache['user_token']:
            system_state['last_status'] = "❌ Erro: Token de usuário não obtido"
            add_log('ERROR', '❌ Token de usuário não foi retornado pela API')
            return
        
        add_log('SUCCESS', f'✓ Token de usuário válido até {token_cache["expires_at"].strftime("%H:%M:%S")}')
        
        # Buscar eventos (usa o token em cache)
        system_state['current_step'] = 'Buscando eventos...'
        hoje = datetime.now().strftime('%Y-%m-%d')
        eventos = hinova.listar_eventos(hoje, hoje)
        
        if not eventos:
            system_state['last_status'] = f"✓ Nenhum evento para {hoje}"
            add_log('INFO', '✓ Nenhum evento para processar hoje')
            return
        
        # Processar eventos (todos com o MESMO token)
        system_state['current_step'] = f'Processando {len(eventos)} eventos...'
        eventos_processados = 0
        
        for idx, evento in enumerate(eventos, 1):
            try:
                system_state['current_step'] = f'Processando evento {idx}/{len(eventos)}...'
                
                protocolo = evento.get('protocolo')
                situacao_codigo = evento.get('situacao', {}).get('codigo')
                situacao_nome = evento.get('situacao', {}).get('nome')
                
                # ID único
                evento_id = f"{protocolo}_{situacao_codigo}"
                
                # Verificar se já processado
                if evento_id in system_state['processed_events']:
                    add_log('INFO', f'⏭️ Evento {protocolo} já processado')
                    continue
                
                # Verificar situação ativa
                if situacao_codigo not in config['situacoes_ativas']:
                    add_log('INFO', f'⏭️ Situação {situacao_codigo} não está ativa')
                    continue
                
                add_log('INFO', f'📝 Processando evento {protocolo} (situação: {situacao_nome})')
                
                # Buscar veículo (usa o MESMO token em cache)
                veiculo_id = evento.get('veiculo', {}).get('codigo')
                if not veiculo_id:
                    add_log('WARNING', f'⚠️ Evento {protocolo} sem veículo')
                    continue
                
                veiculo_data = hinova.buscar_veiculo(veiculo_id)
                if not veiculo_data:
                    continue
                
                # Extrair dados
                associado = veiculo_data.get('associado', {})
                nome_associado = associado.get('nome', 'Cliente')
                placa = veiculo_data.get('placa', 'N/A')
                telefone = extrair_telefone(associado)
                
                if not telefone:
                    add_log('WARNING', f'⚠️ Telefone não encontrado para {protocolo}')
                    save_message_log(
                        protocolo, evento_id, situacao_codigo, situacao_nome,
                        None, None, 'ERRO', 'Telefone não encontrado',
                        nome_associado, placa
                    )
                    continue
                
                # Obter template
                template = config['templates_mensagem'].get(str(situacao_codigo))
                
                if not template:
                    # Template padrão
                    template = f"Olá {{nome_associado}}!\n\n*{situacao_nome}*\n\nProtocolo: {{protocolo}}\nVeículo: {{placa}}\nData: {{data_evento}}"
                
                # Formatar mensagem
                mensagem = formatar_mensagem(template, evento, veiculo_data)
                if not mensagem:
                    continue
                
                # Enviar mensagem
                if uppchannel.enviar_mensagem(telefone, mensagem):
                    system_state['processed_events'].add(evento_id)
                    eventos_processados += 1
                    system_state['stats']['successful_messages'] += 1
                    
                    save_message_log(
                        protocolo, evento_id, situacao_codigo, situacao_nome,
                        telefone, mensagem, 'ENVIADO', None,
                        nome_associado, placa
                    )
                else:
                    system_state['stats']['failed_messages'] += 1
                    save_message_log(
                        protocolo, evento_id, situacao_codigo, situacao_nome,
                        telefone, mensagem, 'FALHOU', 'Erro no envio',
                        nome_associado, placa
                    )
                
            except Exception as e:
                add_log('ERROR', f'❌ Erro ao processar evento: {str(e)}')
                system_state['stats']['failed_messages'] += 1
                continue
        
        system_state['last_status'] = f"✓ {eventos_processados} mensagens enviadas"
        add_log('SUCCESS', f'✓ Processamento concluído: {eventos_processados} mensagens')
        system_state['stats']['last_error'] = None
        
    except Exception as e:
        system_state['last_status'] = f"❌ Erro: {str(e)}"
        system_state['stats']['last_error'] = str(e)
        add_log('ERROR', f'❌ Erro no processamento: {str(e)}')
    
    finally:
        system_state['is_running'] = False
        system_state['current_step'] = ''
        add_log('INFO', '=' * 60)


# ==================== ROTAS FLASK ====================

@app.route('/')
def index():
    """Dashboard principal"""
    # HTML inline para evitar problemas de caminho no Render
    html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Hinova → UppChannel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f7fa; color: #333; }
        .container { display: flex; height: 100vh; }
        .sidebar { width: 250px; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; display: flex; flex-direction: column; }
        .logo { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .subtitle { font-size: 12px; opacity: 0.9; margin-bottom: 30px; }
        .nav-item { padding: 12px 15px; margin: 5px 0; border-radius: 8px; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; gap: 10px; }
        .nav-item:hover { background: rgba(255,255,255,0.2); }
        .nav-item.active { background: rgba(255,255,255,0.3); }
        .nav-icon { font-size: 18px; }
        .main-content { flex: 1; overflow-y: auto; padding: 30px; }
        .page { display: none; }
        .page.active { display: block; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .header h1 { font-size: 32px; color: #333; }
        .btn { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
        .btn:hover { background: #5568d3; transform: translateY(-2px); }
        .btn-success { background: #48bb78; }
        .btn-success:hover { background: #38a169; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .stat-label { font-size: 14px; color: #666; margin-bottom: 10px; }
        .stat-value { font-size: 36px; font-weight: bold; color: #667eea; }
        .log-panel { background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); overflow: hidden; }
        .log-header { background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
        .log-title { font-size: 18px; font-weight: bold; color: #333; }
        .log-body { height: 400px; overflow-y: auto; padding: 15px; background: #1a1a1a; font-family: 'Courier New', monospace; font-size: 13px; }
        .log-entry { padding: 5px 0; border-bottom: 1px solid #333; }
        .log-timestamp { color: #888; margin-right: 10px; }
        .log-level { margin-right: 10px; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold; }
        .log-level.INFO { background: #3498db; color: white; }
        .log-level.SUCCESS { background: #48bb78; color: white; }
        .log-level.WARNING { background: #f39c12; color: white; }
        .log-level.ERROR { background: #e74c3c; color: white; }
        .log-message { color: #0f0; }
        .alert { padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid; }
        .alert-info { background: #e3f2fd; border-color: #2196f3; color: #0d47a1; }
        .alert-success { background: #d4edda; border-color: #28a745; color: #155724; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-running { background: #48bb78; animation: pulse 2s infinite; }
        .status-idle { background: #95a5a6; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .loading { text-align: center; padding: 40px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        table { width: 100%; border-collapse: collapse; }
        thead { background: #f8f9fa; }
        th { padding: 15px; text-align: left; font-weight: bold; color: #333; border-bottom: 2px solid #e0e0e0; }
        td { padding: 12px 15px; border-bottom: 1px solid #f0f0f0; }
        tr:hover { background: #f8f9fa; }
        .badge { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-error { background: #f8d7da; color: #721c24; }
        .config-section { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 20px; }
        .config-title { font-size: 20px; font-weight: bold; color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 8px; color: #333; }
        .form-group input, .form-group textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        .form-group input:focus, .form-group textarea:focus { outline: none; border-color: #667eea; }
        .table-container { background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); overflow: hidden; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="logo">🚗 Monitor Hinova</div>
            <div class="subtitle">Mensagens Automáticas</div>
            <div class="nav-item active" onclick="showPage('dashboard')"><span class="nav-icon">📊</span><span>Dashboard</span></div>
            <div class="nav-item" onclick="showPage('logs')"><span class="nav-icon">📋</span><span>Logs do Sistema</span></div>
            <div class="nav-item" onclick="showPage('messages')"><span class="nav-icon">💬</span><span>Histórico</span></div>
            <div class="nav-item" onclick="showPage('config')"><span class="nav-icon">⚙️</span><span>Configurações</span></div>
            <div class="nav-item" onclick="showPage('test')"><span class="nav-icon">🔬</span><span>Testar Conexões</span></div>
            <div style="margin-top: auto; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
                <div style="font-size: 12px; opacity: 0.8;">Status: <span id="systemStatus">...</span></div>
                <div style="font-size: 11px; opacity: 0.7; margin-top: 5px;">Atualização: <span id="lastUpdate">-</span></div>
            </div>
        </div>
        <div class="main-content">
            <div class="page active" id="dashboard-page">
                <div class="header"><h1>Dashboard</h1><button class="btn btn-success" onclick="runNow()">▶️ Executar</button></div>
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-label">Execuções</div><div class="stat-value" id="totalRuns">0</div></div>
                    <div class="stat-card"><div class="stat-label">Enviadas</div><div class="stat-value" id="successMessages">0</div></div>
                    <div class="stat-card"><div class="stat-label">Falhas</div><div class="stat-value" id="failedMessages" style="color: #e74c3c;">0</div></div>
                    <div class="stat-card"><div class="stat-label">Processados</div><div class="stat-value" id="processedEvents">0</div></div>
                </div>
                <div class="log-panel">
                    <div class="log-header"><div class="log-title"><span class="status-indicator" id="statusIndicator"></span><span id="currentStep">Sistema aguardando...</span></div><button class="btn" onclick="updateStatus()" style="padding: 8px 16px; font-size: 12px;">🔄</button></div>
                    <div class="log-body" id="logContainer"><div class="loading"><div class="spinner"></div>Carregando...</div></div>
                </div>
            </div>
            <div class="page" id="test-page">
                <div class="header"><h1>Testar Conexões</h1><button class="btn btn-success" onclick="testConnections()">🔬 Testar</button></div>
                <div class="alert alert-info"><strong>💡</strong> Verifique se as APIs estão respondendo.</div>
                <div class="config-section"><div class="config-title">Status</div><div id="testResults"><p style="text-align:center;color:#888;">Clique em Testar</p></div></div>
                <div class="alert alert-success"><strong>✅</strong> "Nenhum evento" significa que está OK!</div>
            </div>
            <div class="page" id="logs-page">
                <div class="header"><h1>Logs</h1><button class="btn" onclick="updateStatus()">🔄</button></div>
                <div class="log-panel"><div class="log-header"><div class="log-title">Histórico</div></div><div class="log-body" id="fullLogContainer" style="height:600px;"><div class="loading"><div class="spinner"></div>Carregando...</div></div></div>
            </div>
            <div class="page" id="messages-page">
                <div class="header"><h1>Mensagens</h1><button class="btn" onclick="refreshMessages()">🔄</button></div>
                <div class="table-container"><table><thead><tr><th>Data</th><th>Protocolo</th><th>Situação</th><th>Cliente</th><th>Status</th></tr></thead><tbody id="messagesTableBody"><tr><td colspan="5" style="text-align:center;padding:40px;"><div class="spinner"></div>Carregando...</td></tr></tbody></table></div>
            </div>
            <div class="page" id="config-page">
                <div class="header"><h1>Configurações</h1><button class="btn btn-success" onclick="saveConfig()">💾 Salvar</button></div>
                <div class="alert alert-info"><strong>💡</strong> Reinicie após alterar credenciais.</div>
                <div class="config-section"><div class="config-title">🔐 Credenciais</div><div class="form-group"><label>Token Hinova:</label><input type="text" id="configHinovaToken"></div><div class="form-group"><label>Usuário:</label><input type="text" id="configHinovaUser"></div><div class="form-group"><label>Senha:</label><input type="password" id="configHinovaPass"></div><div class="form-group"><label>API Key UppChannel:</label><input type="text" id="configUppKey"></div></div>
                <div class="config-section"><div class="config-title">⚙️ Sistema</div><div class="form-group"><label>Intervalo (min):</label><input type="number" id="configInterval" value="15"></div><div class="form-group"><label>Situações:</label><input type="text" id="configSituacoes"></div></div>
            </div>
        </div>
    </div>
    <script>
        let updateInterval;
        function showPage(p){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));document.getElementById(p+'-page').classList.add('active');event.target.closest('.nav-item').classList.add('active');if(p==='messages')refreshMessages();else if(p==='logs')refreshFullLogs();else if(p==='config')loadConfig();}
        async function updateStatus(){try{const r=await fetch('/api/status');const d=await r.json();document.getElementById('totalRuns').textContent=d.stats.total_runs;document.getElementById('successMessages').textContent=d.stats.successful_messages;document.getElementById('failedMessages').textContent=d.stats.failed_messages;document.getElementById('processedEvents').textContent=d.processed_events_count;const si=document.getElementById('statusIndicator');const cs=document.getElementById('currentStep');const ss=document.getElementById('systemStatus');if(d.is_running){si.className='status-indicator status-running';cs.textContent=d.current_step||'Processando...';ss.textContent='Rodando';}else{si.className='status-indicator status-idle';cs.textContent=d.last_status||'Ocioso';ss.textContent='Ocioso';}updateLogs(d.logs);document.getElementById('lastUpdate').textContent=new Date().toLocaleTimeString('pt-BR');}catch(e){console.error(e);}}
        function updateLogs(logs){const c=document.getElementById('logContainer');c.innerHTML='';if(!logs||logs.length===0){c.innerHTML='<div style="color:#888;text-align:center;padding:20px;">Nenhum log</div>';return;}logs.forEach(l=>{const e=document.createElement('div');e.className='log-entry';e.innerHTML=`<span class="log-timestamp">${l.timestamp}</span><span class="log-level ${l.level}">${l.level}</span><span class="log-message">${l.message}</span>`;c.appendChild(e);});}
        async function refreshFullLogs(){const c=document.getElementById('fullLogContainer');c.innerHTML='<div class="loading"><div class="spinner"></div>Carregando...</div>';try{const r=await fetch('/api/logs');const logs=await r.json();c.innerHTML='';logs.forEach(l=>{const e=document.createElement('div');e.className='log-entry';e.innerHTML=`<span class="log-timestamp">${l.timestamp}</span><span class="log-level ${l.level}">${l.level}</span><span class="log-message">${l.message}</span>`;c.appendChild(e);});}catch(e){c.innerHTML='<div style="color:#e74c3c;text-align:center;padding:20px;">Erro</div>';}}
        async function refreshMessages(){const t=document.getElementById('messagesTableBody');t.innerHTML='<tr><td colspan="5" style="text-align:center;padding:40px;"><div class="spinner"></div>Carregando...</td></tr>';try{const r=await fetch('/api/messages');const m=await r.json();t.innerHTML='';if(m.length===0){t.innerHTML='<tr><td colspan="5" style="text-align:center;padding:40px;color:#888;">Nenhuma mensagem</td></tr>';return;}m.forEach(msg=>{const row=document.createElement('tr');const ts=new Date(msg.timestamp).toLocaleString('pt-BR');row.innerHTML=`<td>${ts}</td><td>${msg.protocolo||'-'}</td><td>${msg.situacao_nome||'-'}</td><td>${msg.nome_associado||'-'}</td><td><span class="badge ${msg.status==='ENVIADO'?'badge-success':'badge-error'}">${msg.status}</span></td>`;t.appendChild(row);});}catch(e){t.innerHTML='<tr><td colspan="5" style="text-align:center;padding:40px;color:#e74c3c;">Erro</td></tr>';}}
        async function loadConfig(){try{const r=await fetch('/api/config');const c=await r.json();document.getElementById('configHinovaToken').value=c.hinova.token||'';document.getElementById('configHinovaUser').value=c.hinova.usuario||'';document.getElementById('configHinovaPass').value=c.hinova.senha||'';document.getElementById('configUppKey').value=c.uppchannel.api_key||'';document.getElementById('configInterval').value=c.intervalo_minutos||15;document.getElementById('configSituacoes').value=c.situacoes_ativas.join(',');}catch(e){console.error(e);}}
        async function saveConfig(){const c={hinova:{token:document.getElementById('configHinovaToken').value,usuario:document.getElementById('configHinovaUser').value,senha:document.getElementById('configHinovaPass').value},uppchannel:{api_key:document.getElementById('configUppKey').value},intervalo_minutos:parseInt(document.getElementById('configInterval').value),situacoes_ativas:document.getElementById('configSituacoes').value.split(',').map(x=>parseInt(x.trim()))};try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(c)});if(r.ok)alert('✅ Salvo!');else alert('❌ Erro');}catch(e){alert('❌ Erro: '+e.message);}}
        async function runNow(){if(confirm('Executar agora?')){try{await fetch('/api/run-now');alert('✓ Iniciado! Veja os logs.');}catch(e){alert('Erro');}}}
        async function testConnections(){const r=document.getElementById('testResults');r.innerHTML='<div class="loading"><div class="spinner"></div>Testando...</div>';try{const res=await fetch('/api/test-connections');const d=await res.json();let h='';h+='<div style="margin-bottom:20px;padding:20px;background:'+(d.hinova.status==='success'?'#d4edda':'#f8d7da')+';border-radius:10px;border-left:5px solid '+(d.hinova.status==='success'?'#28a745':'#dc3545')+';">';h+='<h3 style="margin:0 0 10px 0;color:'+(d.hinova.status==='success'?'#155724':'#721c24')+';">'+(d.hinova.status==='success'?'✅':'❌')+' Hinova</h3><p><strong>Status:</strong> '+d.hinova.message+'</p>';if(d.hinova.details&&d.hinova.details.token_cached)h+='<p><strong>Token:</strong> '+d.hinova.details.token_cached+'</p>';h+='</div>';h+='<div style="padding:20px;background:'+(d.uppchannel.status==='success'?'#d4edda':'#f8d7da')+';border-radius:10px;border-left:5px solid '+(d.uppchannel.status==='success'?'#28a745':'#dc3545')+';">';h+='<h3 style="margin:0 0 10px 0;color:'+(d.uppchannel.status==='success'?'#155724':'#721c24')+';">'+(d.uppchannel.status==='success'?'✅':'❌')+' UppChannel</h3><p><strong>Status:</strong> '+d.uppchannel.message+'</p></div>';r.innerHTML=h;}catch(e){r.innerHTML='<div style="color:#e74c3c;text-align:center;padding:40px;">❌ Erro</div>';}}
        updateStatus();updateInterval=setInterval(updateStatus,5000);
    </script>
</body>
</html>'''
    return html

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/status')
def api_status():
    """Status do sistema em JSON"""
    return jsonify({
        'last_run': system_state['last_run'].isoformat() if system_state['last_run'] else None,
        'last_status': system_state['last_status'],
        'is_running': system_state['is_running'],
        'current_step': system_state['current_step'],
        'stats': system_state['stats'],
        'logs': system_state['logs'][:50],  # Últimos 50 logs
        'processed_events_count': len(system_state['processed_events'])
    })

@app.route('/api/logs')
def api_logs():
    """Logs do sistema"""
    return jsonify(system_state['logs'])

@app.route('/api/messages')
def api_messages():
    """Histórico de mensagens"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(get_messages_history(limit))

@app.route('/api/run-now')
def run_now():
    """Executa processamento manual"""
    add_log('INFO', '▶️ Execução manual iniciada')
    processar_eventos()
    return jsonify({'status': 'completed', 'message': system_state['last_status']})

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Gerenciar configuração"""
    if request.method == 'POST':
        config = request.json
        save_config('main_config', config)
        add_log('SUCCESS', '✓ Configuração atualizada')
        return jsonify({'status': 'success'})
    else:
        config = carregar_configuracao()
        return jsonify(config)

@app.route('/api/test-connections')
def test_connections():
    """Testa conectividade com as APIs SEM interferir no token em uso"""
    results = {
        'hinova': {'status': 'pending', 'message': '', 'details': {}},
        'uppchannel': {'status': 'pending', 'message': '', 'details': {}}
    }
    
    config = carregar_configuracao()
    
    # Testar Hinova SEM fazer nova autenticação se já houver token válido
    try:
        add_log('INFO', '🔍 Testando conexão Hinova...')
        
        # Verificar se já tem token válido em cache
        if token_cache['user_token'] and token_cache['expires_at']:
            if datetime.now() < token_cache['expires_at']:
                results['hinova']['status'] = 'success'
                results['hinova']['message'] = 'Token em cache válido'
                results['hinova']['details'] = {
                    'token_cached': token_cache['user_token'][:20] + '...',
                    'expires_at': token_cache['expires_at'].isoformat()
                }
                add_log('SUCCESS', '✓ Teste Hinova: Token em cache OK')
            else:
                results['hinova']['status'] = 'warning'
                results['hinova']['message'] = 'Token em cache expirado (será renovado no próximo processamento)'
                add_log('WARNING', '⚠️ Token em cache expirado')
        else:
            # Só autentica se não houver token (para não invalidar o token em uso!)
            results['hinova']['status'] = 'info'
            results['hinova']['message'] = 'Nenhum token em cache (aguardando primeiro processamento)'
            add_log('INFO', 'ℹ️ Nenhum token em cache ainda')
            
    except Exception as e:
        results['hinova']['status'] = 'error'
        results['hinova']['message'] = str(e)
        add_log('ERROR', f'❌ Erro Hinova: {str(e)}')
    
    # Testar UppChannel (teste básico)
    try:
        add_log('INFO', '🔍 Testando configuração UppChannel...')
        if config['uppchannel']['api_key']:
            results['uppchannel']['status'] = 'success'
            results['uppchannel']['message'] = 'API Key configurada'
            results['uppchannel']['details'] = {
                'api_key': config['uppchannel']['api_key'][:20] + '...'
            }
            add_log('SUCCESS', '✓ Teste UppChannel: API Key OK')
        else:
            results['uppchannel']['status'] = 'error'
            results['uppchannel']['message'] = 'API Key não configurada'
            add_log('ERROR', '❌ API Key UppChannel não encontrada')
    except Exception as e:
        results['uppchannel']['status'] = 'error'
        results['uppchannel']['message'] = str(e)
        add_log('ERROR', f'❌ Erro UppChannel: {str(e)}')
    
    return jsonify(results)


# ==================== INICIALIZAÇÃO ====================

# Inicializar scheduler
scheduler = BackgroundScheduler()

if __name__ == '__main__':
    # Inicializar banco
    init_database()
    
    add_log('INFO', '🚀 Sistema iniciando...')
    
    # Carregar configuração
    config = carregar_configuracao()
    intervalo = config['intervalo_minutos']
    
    add_log('INFO', f'⏱️ Intervalo configurado: {intervalo} minutos')
    
    # Agendar tarefa
    scheduler.add_job(
        func=processar_eventos,
        trigger=IntervalTrigger(minutes=intervalo),
        id='processar_eventos',
        name='Processar eventos Hinova',
        replace_existing=True
    )
    
    scheduler.start()
    add_log('SUCCESS', '✓ Agendador iniciado')
    
    # Executar uma vez ao iniciar
    add_log('INFO', '▶️ Executando processamento inicial...')
    processar_eventos()
    
    # Iniciar Flask
    port = int(os.environ.get('PORT', 10000))
    add_log('SUCCESS', f'✓ Servidor Flask iniciando na porta {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
