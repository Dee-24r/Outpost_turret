/*
  ============================================================
  TORRETA - FIRMWARE ESP32-C3
  ------------------------------------------------------------
  Recibe por serial lo que manda tracker.py:
    "T,<error_x>,<error_y>\n"   -> hay cara, con su error en pixeles
    "N\n"                        -> no hay cara

  Hace 3 cosas:
    1. Mueve 2 servos (pan/tilt) proporcional al error (control P)
    2. Mientras el boton esta presionado ("armado"), las llantas
       (DRV8833) giran SIN PARAR. La bala se mete a mano entre
       las llantas cuando ya esta centrado -> se dispara sola.
    3. El LED se prende cuando esta CENTRADO, para que la persona
       que mete la bala no tenga que ver la laptop.

  ---- CABLEADO (ajusta los pines a los tuyos) ----
    Servo PAN  (izq/der) -> GPIO4
    Servo TILT (arriba/abajo) -> GPIO5
    DRV8833 IN1 (llanta) -> GPIO6
    DRV8833 IN2 (llanta) -> GPIO7
    Boton (a GND, usa pull-up interno) -> GPIO10
    LED "CENTRADO" (con resistencia, a GND) -> GPIO3
  ============================================================
*/

#include <ESP32Servo.h>

// ==================== PINES ====================
const int PIN_SERVO_PAN  = 4;
const int PIN_SERVO_TILT = 5;
const int PIN_MOTOR_IN1  = 6;
const int PIN_MOTOR_IN2  = 7;
const int PIN_BOTON      = 10;
const int PIN_LED        = 3;

// ==================== SERVOS ====================
const int PAN_CENTRO  = 90;   // angulo de reposo (grados)
const int TILT_CENTRO = 90;
const int PAN_MIN = 20, PAN_MAX = 160;
const int TILT_MIN = 30, TILT_MAX = 150;

// Ganancia: pixeles de error -> grados de correccion.
// Si se mueve muy brusco, bajale. Si no alcanza a corregir, subele.
const float GANANCIA_PAN  = 0.03f;
const float GANANCIA_TILT = 0.03f;

// ==================== CENTRADO / LED ====================
const int ZONA_MUERTA_X = 35;   // igual que ZONA_MUERTA en tracker.py
const int ZONA_MUERTA_Y = 35;

// Si no llega nada del PC en este tiempo, se asume conexion perdida
const unsigned long TIMEOUT_SERIAL_MS = 500;

// =======================================================

Servo servoPan;
Servo servoTilt;

float panActual  = PAN_CENTRO;
float tiltActual = TILT_CENTRO;

String buffer = "";
unsigned long ultimoDatoValido = 0;
bool centrado = false;

void motorParar() {
  digitalWrite(PIN_MOTOR_IN1, LOW);
  digitalWrite(PIN_MOTOR_IN2, LOW);
}

void motorGirar() {
  digitalWrite(PIN_MOTOR_IN1, HIGH);
  digitalWrite(PIN_MOTOR_IN2, LOW);
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);

  pinMode(PIN_MOTOR_IN1, OUTPUT);
  pinMode(PIN_MOTOR_IN2, OUTPUT);
  motorParar();

  pinMode(PIN_BOTON, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  servoPan.setPeriodHertz(50);
  servoTilt.setPeriodHertz(50);
  servoPan.attach(PIN_SERVO_PAN, 500, 2400);
  servoTilt.attach(PIN_SERVO_TILT, 500, 2400);
  servoPan.write(PAN_CENTRO);
  servoTilt.write(TILT_CENTRO);

  Serial.println("Torreta lista.");
}

void procesarLinea(String linea) {
  linea.trim();
  if (linea.length() == 0) return;

  if (linea[0] == 'N') {
    // sin cara: no corrige, apaga el LED de centrado
    ultimoDatoValido = millis();
    centrado = false;
    return;
  }

  if (linea[0] == 'T') {
    int coma1 = linea.indexOf(',');
    int coma2 = linea.indexOf(',', coma1 + 1);
    if (coma1 < 0 || coma2 < 0) return;

    int errorX = linea.substring(coma1 + 1, coma2).toInt();
    int errorY = linea.substring(coma2 + 1).toInt();

    ultimoDatoValido = millis();

    // ---- control proporcional simple ----
    panActual  -= errorX * GANANCIA_PAN;   // ajusta signo si se mueve al reves
    tiltActual -= errorY * GANANCIA_TILT;  // ajusta signo si se mueve al reves

    panActual  = constrain(panActual, PAN_MIN, PAN_MAX);
    tiltActual = constrain(tiltActual, TILT_MIN, TILT_MAX);

    servoPan.write((int)panActual);
    servoTilt.write((int)tiltActual);

    centrado = (abs(errorX) < ZONA_MUERTA_X) && (abs(errorY) < ZONA_MUERTA_Y);
  }
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      procesarLinea(buffer);
      buffer = "";
    } else {
      buffer += c;
    }
  }

  // si se perdio la conexion con el PC, para todo por seguridad
  if (ultimoDatoValido != 0 && millis() - ultimoDatoValido > TIMEOUT_SERIAL_MS) {
    centrado = false;
  }

  // ---- llantas: giran sin parar mientras el boton este presionado ----
  bool armado = (digitalRead(PIN_BOTON) == LOW); // presionado = armado
  if (armado) {
    motorGirar();
  } else {
    motorParar();
  }

  // ---- LED: prendido cuando la cara esta centrada ----
  digitalWrite(PIN_LED, centrado ? HIGH : LOW);
}
