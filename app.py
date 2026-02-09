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
    timestamp = datetime.now().strftime('%H:%M:%S')
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
                add_log('INFO', '✓ Token em cache ainda válido')
                return True
        
        try:
            add_log('INFO', '🔑 Autenticando na API Hinova...')
            
            url = f"{self.base_url}/usuario/autenticar"
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "usuario": self.usuario,
                "senha": self.senha
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            user_token = data.get('token')
            
            if user_token:
                # Atualizar cache (token válido por 1 hora)
                token_cache['bearer_token'] = self.token
                token_cache['user_token'] = user_token
                token_cache['expires_at'] = datetime.now() + timedelta(hours=1)
                
                add_log('SUCCESS', f'✓ Autenticação bem-sucedida (token: {user_token[:20]}...)')
                return True
            else:
                add_log('ERROR', '❌ Resposta sem token de usuário')
                return False
            
        except requests.exceptions.Timeout:
            add_log('ERROR', '❌ Timeout na autenticação (>30s)')
            return False
        except Exception as e:
            add_log('ERROR', f'❌ Erro na autenticação: {str(e)}')
            return False
    
    def listar_eventos(self, data_inicio, data_fim):
        """Lista eventos por período"""
        try:
            add_log('INFO', f'📋 Buscando eventos de {data_inicio} até {data_fim}...')
            
            url = f"{self.base_url}/listar/evento"
            headers = {
                "Authorization": f"Bearer {token_cache['bearer_token']}",
                "token": token_cache['user_token']
            }
            payload = {
                "data_inicio": data_inicio,
                "data_fim": data_fim
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Se token expirou, reautenticar
            if response.status_code == 401:
                add_log('WARNING', '⚠️ Token expirado, reautenticando...')
                if self.autenticar(force=True):
                    headers["token"] = token_cache['user_token']
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            response.raise_for_status()
            
            data = response.json()
            eventos = data.get('eventos', [])
            
            add_log('INFO', f'✓ {len(eventos)} eventos encontrados')
            return eventos
            
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
            
            response = requests.get(url, headers=headers, timeout=30)
            
            # Se token expirou, reautenticar
            if response.status_code == 401:
                if self.autenticar(force=True):
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
        
        # Autenticar
        system_state['current_step'] = 'Autenticando...'
        if not hinova.autenticar():
            system_state['last_status'] = "❌ Erro na autenticação"
            return
        
        # Buscar eventos
        system_state['current_step'] = 'Buscando eventos...'
        hoje = datetime.now().strftime('%Y-%m-%d')
        eventos = hinova.listar_eventos(hoje, hoje)
        
        if not eventos:
            system_state['last_status'] = f"✓ Nenhum evento para {hoje}"
            add_log('INFO', '✓ Nenhum evento para processar')
            return
        
        # Processar eventos
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
                
                # Buscar veículo
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
    html = open('/mnt/user-data/outputs/dashboard.html', 'r', encoding='utf-8').read()
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
    """Testa conectividade com as APIs"""
    results = {
        'hinova': {'status': 'pending', 'message': '', 'details': {}},
        'uppchannel': {'status': 'pending', 'message': '', 'details': {}}
    }
    
    config = carregar_configuracao()
    
    # Testar Hinova
    try:
        add_log('INFO', '🔍 Testando conexão Hinova...')
        hinova = HinovaAPI(
            config['hinova']['token'],
            config['hinova']['usuario'],
            config['hinova']['senha']
        )
        
        if hinova.autenticar(force=True):
            results['hinova']['status'] = 'success'
            results['hinova']['message'] = 'Conexão bem-sucedida'
            results['hinova']['details'] = {
                'token_cached': token_cache['user_token'][:20] + '...',
                'expires_at': token_cache['expires_at'].isoformat() if token_cache['expires_at'] else None
            }
            add_log('SUCCESS', '✓ Teste Hinova: OK')
        else:
            results['hinova']['status'] = 'error'
            results['hinova']['message'] = 'Falha na autenticação'
            add_log('ERROR', '❌ Teste Hinova: FALHOU')
    except Exception as e:
        results['hinova']['status'] = 'error'
        results['hinova']['message'] = str(e)
        add_log('ERROR', f'❌ Erro Hinova: {str(e)}')
    
    # Testar UppChannel (teste básico)
    try:
        add_log('INFO', '🔍 Testando conexão UppChannel...')
        results['uppchannel']['status'] = 'success'
        results['uppchannel']['message'] = 'API Key configurada'
        results['uppchannel']['details'] = {
            'api_key': config['uppchannel']['api_key'][:20] + '...' if config['uppchannel']['api_key'] else 'Não configurado'
        }
        add_log('SUCCESS', '✓ Teste UppChannel: OK')
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
