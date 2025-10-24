#include <SPI.h>
#include <RF24.h>
#include <DHT.h>
#include <Servo.h>

// === CONFIGURAÇÕES ===
#define DHTPIN 2
#define DHTTYPE DHT11
#define CE_PIN 7
#define CSN_PIN 8
#define BUZZER 5
#define LED_VERDE 4
#define LED_VERMELHO 3
#define SERVO_PIN 9

DHT dht(DHTPIN, DHTTYPE);
RF24 radio(CE_PIN, CSN_PIN);
Servo esteira;

const byte endereco[6] = "12345";
const float LIMITE_TEMP = 30.0;
const unsigned long INTERVALO_ENVIO = 5000; // 5 segundos

struct DadosSensor {
  char id[10] = "Node1";
  float temperatura;
  float umidade;
  bool emergencia = false;
  unsigned long timestamp;
};

struct ComandoControle {
  char acao[15]; // LIGAR_MOTOR, DESLIGAR_MOTOR, ALARME_ON, ALARME_OFF
};

bool motorLigado = true;
bool alarmeAtivo = false;
unsigned long ultimoEnvio = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("=== SMARTFACTORY NODE1 ===");
  
  // Inicializar sensores e atuadores
  dht.begin();
  pinMode(BUZZER, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);
  
  esteira.attach(SERVO_PIN);
  esteira.write(90); // Motor ligado
  digitalWrite(LED_VERDE, HIGH);
  digitalWrite(LED_VERMELHO, LOW);

  // Configurar NRF24
  if (!radio.begin()) {
    Serial.println("❌ NRF24: Verifique conexoes 3.3V/GND/CE/CSN");
    while(1);
  }
  
  radio.openWritingPipe(endereco);
  radio.openReadingPipe(1, endereco); // Para receber comandos
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_250KBPS);
  radio.stopListening();
  
  Serial.println("✅ Sistema OK - Enviando dados...");
}

void processarComando(const char* comando) {
  Serial.print("📡 Comando recebido: ");
  Serial.println(comando);
  
  if (strcmp(comando, "LIGAR_MOTOR") == 0) {
    esteira.write(90);
    motorLigado = true;
    digitalWrite(LED_VERDE, HIGH);
  } 
  else if (strcmp(comando, "DESLIGAR_MOTOR") == 0) {
    esteira.write(0);
    motorLigado = false;
    digitalWrite(LED_VERDE, LOW);
  }
  else if (strcmp(comando, "ALARME_ON") == 0) {
    tone(BUZZER, 1000);
    alarmeAtivo = true;
  }
  else if (strcmp(comando, "ALARME_OFF") == 0) {
    noTone(BUZZER);
    alarmeAtivo = false;
  }
}

void verificarComandos() {
  radio.startListening();
  delay(20); // Pequena pausa para recepção
  
  if (radio.available()) {
    ComandoControle comando;
    radio.read(&comando, sizeof(comando));
    processarComando(comando.acao);
  }
  
  radio.stopListening();
}

void loop() {
  unsigned long agora = millis();
  
  // Verificar comandos a cada ciclo
  verificarComandos();
  
  // Enviar dados no intervalo programado
  if (agora - ultimoEnvio >= INTERVALO_ENVIO) {
    float umidade = dht.readHumidity();
    float temperatura = dht.readTemperature();

    if (isnan(umidade) || isnan(temperatura)) {
      Serial.println("❌ Erro na leitura do DHT11");
      ultimoEnvio = agora;
      return;
    }

    // Controle local de emergência
    bool alerta = temperatura > LIMITE_TEMP;
    
    if (alerta && !alarmeAtivo) {
      digitalWrite(LED_VERMELHO, HIGH);
      tone(BUZZER, 1000, 500);
      if (motorLigado) {
        esteira.write(0);
        motorLigado = false;
      }
    } else if (!alerta && alarmeAtivo) {
      digitalWrite(LED_VERMELHO, LOW);
      noTone(BUZZER);
      alarmeAtivo = false;
      if (!motorLigado) {
        esteira.write(90);
        motorLigado = true;
      }
    }

    // Preparar e enviar dados
    DadosSensor dados;
    dados.temperatura = temperatura;
    dados.umidade = umidade;
    dados.emergencia = alerta;
    dados.timestamp = agora;

    bool sucesso = false;
    for (int i = 0; i < 3 && !sucesso; i++) {
      sucesso = radio.write(&dados, sizeof(dados));
      if (!sucesso) delay(10);
    }
    
    // Log no serial
    Serial.print(sucesso ? "✅ " : "❌ ");
    Serial.print("Temp: ");
    Serial.print(temperatura);
    Serial.print("C | Umidade: ");
    Serial.print(umidade);
    Serial.print("% | Motor: ");
    Serial.print(motorLigado ? "LIGADO" : "PARADO");
    Serial.println(alerta ? " | 🚨 ALERTA" : " | ✅ NORMAL");

    ultimoEnvio = agora;
  }
  
  delay(100);
}