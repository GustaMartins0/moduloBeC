import serial
import json
import csv
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import warnings
warnings.filterwarnings('ignore')

class SmartFactoryAI:
    def __init__(self):
        self.anomalias = 0
        self.dados_buffer = []
        self.ultima_temperatura = 0
        self.tendencia_superaquecimento = False
        
    def start(self):
        try:
            self.ser = serial.Serial("COM3", 115200, timeout=2)
            print("✅ Sistema SmartFactory Conectado!")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            print("🔧 Verifique a porta COM e a conexão do Arduino")
            return False

    def inicializar_csv(self):
        with open('dados_sensores.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'node', 'temperatura', 'umidade', 'emergencia', 'anomalia_temp', 'anomalia_umid', 'tipo_anomalia'])

    def detectar_anomalia_ai(self, temp, umid, node):
        """Detecção inteligente de anomalias com análise de tendência"""
        anomalias = []
        
        # Análise de temperatura
        if temp > 30:
            anomalias.append(("CRITICA", f"Superaquecimento em {node}"))
        elif temp > 28:
            anomalias.append(("ALERTA", f"Temperatura elevada em {node}"))
            
        # Análise de umidade
        if umid > 70:
            anomalias.append(("CRITICA", f"Umidade excessiva em {node}"))
        elif umid > 65:
            anomalias.append(("ALERTA", f"Umidade alta em {node}"))
        elif umid < 40:
            anomalias.append(("CRITICA", f"Umidade muito baixa em {node}"))
        elif umid < 45:
            anomalias.append(("ALERTA", f"Umidade baixa em {node}"))
            
        # Análise de tendência (simples IA)
        if len(self.dados_buffer) > 5:
            temps_recentes = [d['temp'] for d in self.dados_buffer[-5:]]
            if all(t > 27 for t in temps_recentes) and temp > temps_recentes[-1]:
                anomalias.append(("TENDENCIA", f"Aquecimento progressivo em {node}"))
                self.tendencia_superaquecimento = True
                
        return anomalias

    def processar_dados(self, dados):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp = dados['temperatura']
        umid = dados['umidade']
        node = dados['node']
        
        # Detectar anomalias
        anomalias = self.detectar_anomalia_ai(temp, umid, node)
        anomalia_temp = any("Superaquecimento" in msg for tipo, msg in anomalias)
        anomalia_umid = any("Umidade" in msg for tipo, msg in anomalias)
        
        # Registrar anomalias críticas
        for tipo, mensagem in anomalias:
            if tipo in ["CRITICA", "TENDENCIA"]:
                self.registrar_anomalia(timestamp, node, temp, umid, mensagem)
                self.anomalias += 1

        # Salvar dados no CSV
        with open('dados_sensores.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            tipo_anomalia = "; ".join([f"{tipo}:{msg}" for tipo, msg in anomalias]) if anomalias else "NORMAL"
            writer.writerow([timestamp, node, temp, umid, dados['emergencia'], 
                           anomalia_temp, anomalia_umid, tipo_anomalia])

        # Atualizar buffer para análise de tendência
        self.dados_buffer.append({'timestamp': timestamp, 'temp': temp, 'umid': umid, 'node': node})
        if len(self.dados_buffer) > 50:  # Manter apenas últimos 50 registros
            self.dados_buffer.pop(0)

        # Exibir status
        self.mostrar_status(timestamp, node, temp, umid, dados['emergencia'], anomalias)

    def registrar_anomalia(self, timestamp, node, temp, umid, mensagem):
        with open('anomalias.log', 'a') as log:
            log.write(f"[{timestamp}] {node} | Temp: {temp:.1f}°C | Umid: {umid:.1f}% | {mensagem}\n")

    def mostrar_status(self, timestamp, node, temp, umid, emergencia, anomalias):
        status_emoji = "🚨" if emergencia else "⚡"
        print(f"[{timestamp}] {node} | {temp:.1f}°C | {umid:.1f}% | {status_emoji}")
        
        for tipo, mensagem in anomalias:
            cor = "🟥" if tipo == "CRITICA" else "🟨" if tipo == "ALERTA" else "🟦"
            print(f"   {cor} {mensagem}")

    def gerar_graficos_tempo_real(self):
        """Gera gráficos em tempo real (executar em thread separada se necessário)"""
        try:
            df = pd.read_csv('dados_sensores.csv')
            
            plt.style.use('seaborn-v0_8')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Gráfico de temperatura
            ax1.plot(df['timestamp'], df['temperatura'], 'r-o', linewidth=2, markersize=4, label='Temperatura')
            ax1.axhline(y=30, color='red', linestyle='--', alpha=0.7, label='Limite Crítico (30°C)')
            ax1.axhline(y=28, color='orange', linestyle='--', alpha=0.7, label='Limite Alerta (28°C)')
            ax1.set_ylabel('Temperatura (°C)')
            ax1.set_title('Monitoramento de Temperatura - Tempo Real')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # Gráfico de umidade
            ax2.plot(df['timestamp'], df['umidade'], 'b-s', linewidth=2, markersize=4, label='Umidade')
            ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Limite Superior (70%)')
            ax2.axhline(y=40, color='red', linestyle='--', alpha=0.7, label='Limite Inferior (40%)')
            ax2.set_ylabel('Umidade (%)')
            ax2.set_xlabel('Tempo')
            ax2.set_title('Monitoramento de Umidade - Tempo Real')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            plt.savefig('graficos_tempo_real.png', dpi=300, bbox_inches='tight')
            plt.show()
            
        except Exception as e:
            print(f"⚠️  Erro ao gerar gráficos: {e}")

    def analisar_tendências(self):
        """Análise preditiva simples"""
        try:
            df = pd.read_csv('dados_sensores.csv')
            
            if len(df) < 5:
                return "Dados insuficientes para análise"
                
            insights = []
            
            # Análise de temperatura
            temp_media = df['temperatura'].mean()
            temp_max = df['temperatura'].max()
            temp_tendencia = df['temperatura'].iloc[-5:].mean() - df['temperatura'].iloc[:5].mean()
            
            if temp_tendencia > 0.5:
                insights.append("📈 Tendência de AQUECIMENTO detectada")
            elif temp_tendencia < -0.5:
                insights.append("📉 Tendência de RESFRIAMENTO detectada")
                
            if temp_max > 32:
                insights.append("🔥 SUPERAQUECIMENTO CRÍTICO - Verificar máquinas")
            elif temp_max > 30:
                insights.append("⚠️  Temperatura atingiu níveis críticos")
                
            # Análise de umidade
            if df['umidade'].max() > 75:
                insights.append("💧 UMIDADE EXCESSIVA - Risco para componentes")
            elif df['umidade'].min() < 35:
                insights.append("🏜️  UMIDADE MUITO BAIXA - Risco de estática")
                
            return insights
            
        except Exception as e:
            return [f"Erro na análise: {e}"]

    def gerar_relatorio_pdf(self):
        """Gera relatório PDF completo"""
        try:
            df = pd.read_csv('dados_sensores.csv')
            doc = SimpleDocTemplate("relatorio_smartfactory.pdf", pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            titulo = Paragraph("RELATÓRIO SMARTFACTORY - ANÁLISE COMPLETA", styles['Heading1'])
            story.append(titulo)
            
            # Estatísticas básicas
            stats = [
                ["MÉTRICA", "VALOR"],
                ["Total de Registros", len(df)],
                ["Anomalias Detectadas", self.anomalias],
                ["Temperatura Média", f"{df['temperatura'].mean():.2f}°C"],
                ["Temperatura Máxima", f"{df['temperatura'].max():.2f}°C"],
                ["Temperatura Mínima", f"{df['temperatura'].min():.2f}°C"],
                ["Umidade Média", f"{df['umidade'].mean():.2f}%"],
                ["Umidade Máxima", f"{df['umidade'].max():.2f}%"],
                ["Umidade Mínima", f"{df['umidade'].min():.2f}%"]
            ]
            
            tabela_stats = Table(stats)
            tabela_stats.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#4CAF50'),
                ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), '#F3F3F3'),
                ('GRID', (0, 0), (-1, -1), 1, 'black')
            ]))
            story.append(tabela_stats)
            
            # Insights e recomendações
            insights = self.analisar_tendências()
            if insights:
                story.append(Paragraph("<br/><br/><b>INSIGHTS E RECOMENDAÇÕES:</b>", styles['Heading2']))
                for insight in insights:
                    story.append(Paragraph(f"• {insight}", styles['BodyText']))
            
            doc.build(story)
            print("📄 Relatório PDF gerado: relatorio_smartfactory.pdf")
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")

    def run(self):
        """Loop principal de execução"""
        self.inicializar_csv()
        print("📊 Iniciando coleta de dados... Ctrl+C para parar\n")
        
        try:
            while True:
                if self.ser.in_waiting:
                    linha = self.ser.readline().decode().strip()
                    if linha.startswith('{'):
                        try:
                            dados = json.loads(linha)
                            self.processar_dados(dados)
                        except json.JSONDecodeError:
                            continue
                
                # Gerar gráficos a cada 30 segundos
                if int(time.time()) % 30 == 0:
                    self.gerar_graficos_tempo_real()
                    
        except KeyboardInterrupt:
            print(f"\n📈 Sistema finalizado!")
            print(f"🚨 Total de anomalias detectadas: {self.anomalias}")
            print("📁 Arquivos gerados: dados_sensores.csv, anomalias.log, graficos_tempo_real.png")
            
            # Gerar relatório final
            self.gerar_relatorio_pdf()

if __name__ == "__main__":
    factory = SmartFactoryAI()
    if factory.start():
        factory.run()