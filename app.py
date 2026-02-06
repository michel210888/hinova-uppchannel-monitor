#!/usr/bin/env python3
"""
Aplicação Flask para rodar no Render.com
Monitora eventos da API Hinova e envia mensagens via UppChannel
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Estado global
last_run = None
last_status = "Aguardando primeira execução"
processed_events = set()
stats = {
    'total_runs': 0,
    'successful_messages': 0,
    'failed_messages': 0,
    'last_error': None
}

class HinovaAPI:
    """Cliente para API Hinova SGA"""
    
    def __init__(self, token, usuario, senha):
        self.token = token
        self.usuario = usuario
        self.senha = senha
        self.base_url = "https://api.hinova.com.br/api/sga/v2"
        self.bearer_token = None
        self.user_token = None
    
    def autenticar(self):
        """Autentica na API"""
        try:
            url = f"{self.base_url}/usuario/autenticar"
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "usuario": self.usuario,
                "senha": self.senha
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.bearer_token = self.token
            self.user_token = data.get('token')
            
            logger.info("✓ Autenticação Hinova realizada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na autenticação Hinova: {e}")
            return False
    
    def listar_eventos(self, data_inicio, data_fim):
        """Lista eventos por período"""
        try:
            url = f"{self.base_url}/listar/evento"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "token": self.user_token
            }
            payload = {
                "data_inicio": data_inicio,
                "data_fim": data_fim
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            eventos = data.get('eventos', [])
            logger.info(f"Encontrados {len(eventos)} eventos")
            return eventos
            
        except Exception as e:
            logger.error(f"Erro ao listar eventos: {e}")
            return []
    
    def buscar_veiculo(self, veiculo_id):
        """Busca dados do veículo"""
        try:
            url = f"{self.base_url}/veiculo/buscar/{veiculo_id}/codigo"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "token": self.user_token
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao buscar veículo {veiculo_id}: {e}")
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
            
            logger.info(f"✓ Mensagem enviada para {telefone}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para {telefone}: {e}")
            return False


def carregar_configuracao():
    """Carrega configuração das variáveis de ambiente"""
    config = {
        'hinova': {
            'token': os.getenv('HINOVA_TOKEN'),
            'usuario': os.getenv('HINOVA_USUARIO'),
            'senha': os.getenv('HINOVA_SENHA')
        },
        'uppchannel': {
            'api_key': os.getenv('UPPCHANNEL_API_KEY')
        },
        'situacoes_ativas': [int(x) for x in os.getenv('SITUACOES_ATIVAS', '1,9').split(',')],
        'intervalo_minutos': int(os.getenv('INTERVALO_MINUTOS', '15'))
    }
    
    # Templates padrão
    config['templates_mensagem'] = {
        '1': os.getenv('TEMPLATE_1', 'Olá {nome_associado}! 🚗\n\nSeu evento *{protocolo}* está ABERTO\nVeículo: {placa}\nMotivo: {motivo}'),
        '2': os.getenv('TEMPLATE_2', 'Olá {nome_associado}! 📋\n\nEvento *{protocolo}* EM ANÁLISE\nVeículo: {placa}'),
        '3': os.getenv('TEMPLATE_3', 'Olá {nome_associado}! ⚙️\n\nEvento *{protocolo}* EM ANDAMENTO\nVeículo: {placa}'),
        '9': os.getenv('TEMPLATE_9', 'Olá {nome_associado}! ✅\n\nEvento *{protocolo}* FINALIZADO!\nVeículo: {placa}\nConclusão: {data_evento}')
    }
    
    return config


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
        logger.error(f"Erro ao formatar mensagem: {e}")
        return None


def extrair_telefone(associado_data):
    """Extrai telefone do associado"""
    try:
        celular = associado_data.get('celular', '')
        if celular:
            # Remover caracteres não numéricos
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
        logger.error(f"Erro ao extrair telefone: {e}")
        return None


def processar_eventos():
    """Função principal de processamento"""
    global last_run, last_status, stats
    
    try:
        logger.info("=== Iniciando processamento de eventos ===")
        last_run = datetime.now()
        stats['total_runs'] += 1
        
        # Carregar configuração
        config = carregar_configuracao()
        
        # Validar configuração
        if not config['hinova']['token'] or not config['uppchannel']['api_key']:
            last_status = "❌ Erro: Credenciais não configuradas"
            logger.error("Credenciais não configuradas nas variáveis de ambiente")
            return
        
        # Inicializar APIs
        hinova = HinovaAPI(
            config['hinova']['token'],
            config['hinova']['usuario'],
            config['hinova']['senha']
        )
        
        uppchannel = UppChannelAPI(config['uppchannel']['api_key'])
        
        # Autenticar
        if not hinova.autenticar():
            last_status = "❌ Erro na autenticação Hinova"
            return
        
        # Buscar eventos do dia atual
        hoje = datetime.now().strftime('%Y-%m-%d')
        eventos = hinova.listar_eventos(hoje, hoje)
        
        if not eventos:
            last_status = f"✓ Nenhum evento encontrado para {hoje}"
            logger.info("Nenhum evento para processar")
            return
        
        # Processar eventos
        eventos_processados = 0
        for evento in eventos:
            try:
                # Gerar ID único do evento
                evento_id = f"{evento.get('protocolo')}_{evento.get('situacao', {}).get('codigo')}"
                
                # Verificar se já foi processado
                if evento_id in processed_events:
                    continue
                
                # Verificar situação
                situacao_codigo = evento.get('situacao', {}).get('codigo')
                if situacao_codigo not in config['situacoes_ativas']:
                    continue
                
                # Buscar dados do veículo
                veiculo_id = evento.get('veiculo', {}).get('codigo')
                if not veiculo_id:
                    continue
                
                veiculo_data = hinova.buscar_veiculo(veiculo_id)
                if not veiculo_data:
                    continue
                
                # Extrair telefone
                telefone = extrair_telefone(veiculo_data.get('associado', {}))
                if not telefone:
                    logger.warning(f"Telefone não encontrado para evento {evento.get('protocolo')}")
                    continue
                
                # Formatar mensagem
                template = config['templates_mensagem'].get(str(situacao_codigo))
                if not template:
                    continue
                
                mensagem = formatar_mensagem(template, evento, veiculo_data)
                if not mensagem:
                    continue
                
                # Enviar mensagem
                if uppchannel.enviar_mensagem(telefone, mensagem):
                    processed_events.add(evento_id)
                    eventos_processados += 1
                    stats['successful_messages'] += 1
                    logger.info(f"✓ Evento {evento.get('protocolo')} processado")
                else:
                    stats['failed_messages'] += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar evento: {e}")
                stats['failed_messages'] += 1
                continue
        
        last_status = f"✓ {eventos_processados} mensagens enviadas"
        logger.info(f"=== Processamento concluído: {eventos_processados} mensagens ===")
        stats['last_error'] = None
        
    except Exception as e:
        last_status = f"❌ Erro: {str(e)}"
        stats['last_error'] = str(e)
        logger.error(f"Erro no processamento: {e}")


# Rotas Flask
@app.route('/')
def index():
    """Página inicial com status"""
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="30">
        <title>Monitor Hinova - UppChannel</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 {
                color: #667eea;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
            }
            .status {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border-left: 5px solid #667eea;
            }
            .status-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
            .status-item:last-child {
                border-bottom: none;
            }
            .label {
                font-weight: bold;
                color: #555;
            }
            .value {
                color: #333;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-number {
                font-size: 36px;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                color: #666;
                margin-top: 5px;
            }
            .success {
                color: #28a745;
            }
            .error {
                color: #dc3545;
            }
            .footer {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #666;
                font-size: 12px;
            }
            .button {
                background: #667eea;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }
            .button:hover {
                background: #5568d3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Monitor Hinova → UppChannel</h1>
            <p class="subtitle">Sistema de Mensagens Automáticas</p>
            
            <div class="status">
                <div class="status-item">
                    <span class="label">📊 Status:</span>
                    <span class="value">{{ status }}</span>
                </div>
                <div class="status-item">
                    <span class="label">🕐 Última Execução:</span>
                    <span class="value">{{ last_run or 'Aguardando...' }}</span>
                </div>
                <div class="status-item">
                    <span class="label">⏱️ Intervalo:</span>
                    <span class="value">{{ intervalo }} minutos</span>
                </div>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{{ stats.total_runs }}</div>
                    <div class="stat-label">Execuções</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number success">{{ stats.successful_messages }}</div>
                    <div class="stat-label">Mensagens Enviadas</div>
                </div>
            </div>

            {% if stats.last_error %}
            <div class="status" style="border-left-color: #dc3545;">
                <div class="status-item">
                    <span class="label error">❌ Último Erro:</span>
                    <span class="value">{{ stats.last_error }}</span>
                </div>
            </div>
            {% endif %}

            <div style="text-align: center; margin-top: 30px;">
                <a href="/run-now" class="button">▶️ Executar Agora</a>
                <a href="/stats" class="button">📈 Estatísticas</a>
            </div>

            <div class="footer">
                Atualiza automaticamente a cada 30 segundos<br>
                Deploy: Render.com | Powered by Python + Flask
            </div>
        </div>
    </body>
    </html>
    """
    
    config = carregar_configuracao()
    
    return render_template_string(
        html,
        status=last_status,
        last_run=last_run.strftime('%d/%m/%Y %H:%M:%S') if last_run else None,
        intervalo=config['intervalo_minutos'],
        stats=stats
    )


@app.route('/health')
def health():
    """Health check para o Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/stats')
def statistics():
    """Retorna estatísticas em JSON"""
    return jsonify({
        'last_run': last_run.isoformat() if last_run else None,
        'last_status': last_status,
        'stats': stats,
        'processed_events_count': len(processed_events)
    })


@app.route('/run-now')
def run_now():
    """Executa o processamento manualmente"""
    processar_eventos()
    return jsonify({'status': 'completed', 'message': last_status})


# Inicializar scheduler
scheduler = BackgroundScheduler()

if __name__ == '__main__':
    # Carregar configuração
    config = carregar_configuracao()
    intervalo = config['intervalo_minutos']
    
    # Agendar tarefa
    scheduler.add_job(
        func=processar_eventos,
        trigger=IntervalTrigger(minutes=intervalo),
        id='processar_eventos',
        name='Processar eventos Hinova',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduler iniciado - Intervalo: {intervalo} minutos")
    
    # Executar uma vez ao iniciar
    processar_eventos()
    
    # Iniciar Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
