#include <SPI.h>
#include <RF24.h>
#include <Servo.h>

#define CE_PIN 7
#define CSN_PIN 8
#define LED_RECEPCAO 6

RF24 radio(CE_PIN, CSN_PIN);
const byte endereco[6] = "12345";

struct DadosSensor {
  char id[10];
  float temperatura;
  float umidade;
  bool emergencia;
  unsigned long timestamp;
};

struct ComandoControle {
  char acao[15];
};

unsigned long ultimaRecepcao = 0;
bool sinalPerdido = false;

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  
  pinMode(LED_RECEPCAO, OUTPUT);
  
  Serial.println("=== ESTACAO RECEPTORA CENTRAL ===");
  
  if (!radio.begin()) {
    Serial.println("❌ NRF24 falhou - verifique hardware");
    while(1);
  }
  
  radio.openReadingPipe(0, endereco);
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_250KBPS);
  radio.startListening();
  
  Serial.println("✅ Pronto - Aguardando dados dos sensores...");
  Serial.println("📊 Formato: JSON para Python");
}

void enviarComando(const char* comando) {
  radio.stopListening();
  
  ComandoControle cmd;
  strncpy(cmd.acao, comando, sizeof(cmd.acao)-1);
  cmd.acao[sizeof(cmd.acao)-1] = '\0';
  
  bool enviado = radio.write(&cmd, sizeof(cmd));
  Serial.print(enviado ? "✅ " : "❌ ");
  Serial.print("Comando enviado: ");
  Serial.println(comando);
  
  radio.startListening();
}

void loop() {
  if (radio.available()) {
    DadosSensor dados;
    radio.read(&dados, sizeof(dados));
    
    ultimaRecepcao = millis();
    
    if (sinalPerdido) {
      sinalPerdido = false;
      digitalWrite(LED_RECEPCAO, HIGH);
    }
    
    // Enviar JSON para Python
    Serial.print("{\"node\":\"");
    Serial.print(dados.id);
    Serial.print("\",\"temperatura\":");
    Serial.print(dados.temperatura, 1);
    Serial.print(",\"umidade\":");
    Serial.print(dados.umidade, 1);
    Serial.print(",\"emergencia\":");
    Serial.print(dados.emergencia ? "true" : "false");
    Serial.print(",\"timestamp\":");
    Serial.print(dados.timestamp);
    Serial.println("}");

    // Controle automático baseado nos dados
    if (dados.emergencia) {
      enviarComando("DESLIGAR_MOTOR");
      enviarComando("ALARME_ON");
    } else {
      enviarComando("LIGAR_MOTOR");
      enviarComando("ALARME_OFF");
    }
  }
  
  // Detectar perda de sinal
  if (!sinalPerdido && millis() - ultimaRecepcao > 10000) {
    sinalPerdido = true;
    digitalWrite(LED_RECEPCAO, LOW);
    Serial.println("⚠️  ALERTA: Sinal do sensor perdido!");
  }
  
  delay(50);
}