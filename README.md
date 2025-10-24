# Projeto modulob_PrimeTrio
 
Projeto: *IIoT / Monitoramento e Controle* — Node único (expandível para 3 nós)

## Visão geral
Protótipo de sistema IIoT para monitoramento de temperatura e umidade em linha de produção, com comunicação via NRF24L01 entre nós sensores (Arduino) e uma estação central. Dados são coletados via Serial por um script Python, armazenados, analisados (detecção de anomalias) e exportados em relatório PDF.

Este repositório contém:
- Código Arduino:
  - `transmissor.ino` (Node1 — sensor, servo, buzzer, LEDs, envio RF e escuta de comandos)
  - `receptor.ino` (Estação central — recebe RF e imprime JSON no Serial; aceita comandos via Serial e repassa por RF)
- Script Python:
  - `analise_sensores.py` — coleta via Serial, armazena em CSV/SQLite, plot em tempo real, detecção de anomalias.
  - `create_report.py` — (novo) gera `relatorio.pdf` com métricas, gráficos e sugestões.
- Saída (exemplos gerados durante execução):
  - `dados_sensores.csv`
  - `anomalias.log`
  - `relatorio.pdf`

---

## Componentes (hardware)
- 2x Arduino Uno (1x nó transmissor, 1x receptor/estação)
- 1x DHT11 (temperatura/umidade)
- 2x Módulo NRF24L01 (**NÃO LIGAR EM 5V** — VCC 3.3V)
- 1x Buzzer
- 1x Micro Servo
- LEDs (verde/vermelho) + resistores 220Ω
- Protoboard e fios
- Fonte/regulador 3.3V estável para NRF24L01 (recomendado com capacitor 10µF)

---

## Bibliotecas necessárias (Arduino IDE)
- `DHT sensor library` (Adafruit) ou `DHT.h`
- `RF24` (TMRh20)
- `SPI.h` (builtin)
- `Servo.h` (builtin)

> Atenção: NRF24L01 requer alimentação 3.3V. Use regulador/decoupling e não ligue direto no 5V.

---

## Dependências Python
Recomendado criar ambiente virtual.

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt`


---

## 🔹 moduloC_PrimeTrio

- **Link Vídeo Pitch:** [YouTube](https://youtu.be/1flPGpY7s5Q)  
- **Link Figma:** [Protótipo UI](https://www.figma.com/proto/DpgRyIj2Ih6ygYx7qEyThv/Minimal-Landing-Page-Design-%7C-Website-Home-Page-Design-%7C-Agency-Website-UI-Design--Community---Copy-?node-id=1533-104&t=H451xpYJzxchxDiT-0&scaling=min-zoom&content-scaling=fixed&page-id=1%3A2&starting-point-node-id=1533%3A104&show-proto-sidebar=1)









