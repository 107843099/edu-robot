#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <BluetoothSerial.h>
#include <math.h>

#include "traj_fwd.h"
#include "traj_bwd.h"
#include "traj_right.h"
#include "traj_left.h"

#define SERVOMIN      30
#define SERVOMAX      650
#define CENTER        325
#define NUM_SERVOS    8
#define DELAY_TIME    5

#define PULSE_PER_RAD 160.f
#define HIP_INIT_RAD  0.900000f
#define KNEE_INIT_RAD -1.400000f

#define BT_DEVICE_NAME "Albert"

static const float JOINT_DIR[NUM_SERVOS] = {
  1.0f, 1.0f, -1.0f, -1.0f, 1.0f, 1.0f, -1.0f, -1.0f
};

static const float JOINT_OFFSET_RAD[NUM_SERVOS] = {
  HIP_INIT_RAD, KNEE_INIT_RAD, HIP_INIT_RAD, KNEE_INIT_RAD,
  HIP_INIT_RAD, KNEE_INIT_RAD, HIP_INIT_RAD, KNEE_INIT_RAD
};

// policy order [FL_hip, FL_knee, FR_hip, FR_knee, RL_hip, RL_knee, RR_hip, RR_knee]
static const int TRAJ_TO_SERVO[TRAJ_JOINTS] = { 2, 3, 0, 1, 6, 7, 4, 5 };

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x7F);
BluetoothSerial         BT;

float currentPos[NUM_SERVOS];
float targetPos[NUM_SERVOS];

// ── State ─────────────────────────────────────────────────────────────

enum RobotState { STATE_STILL, STATE_MOVING };
static RobotState    robotState   = STATE_STILL;
static int           traj_step    = 0;
static unsigned long traj_last_ms = 0;

// Active trajectory pointer — set by handleCmd before enterMoving()
static const int16_t (*active_traj)[8] = nullptr;
static int            active_steps     = 0;

// ── Helpers ───────────────────────────────────────────────────────────

static void broadcast(const char* msg) {
  Serial.println(msg);
  if (BT.connected()) BT.println(msg);
}

void setServo(int ch, int pulse) {
  pulse = constrain(pulse, SERVOMIN, SERVOMAX);
  pwm.setPWM(ch, 0, pulse);
  currentPos[ch] = (float)pulse;
  targetPos[ch]  = (float)pulse;
}

void moveToTargets(int durationMs) {
  int steps = max(1, durationMs / DELAY_TIME);
  float startPos[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++) startPos[i] = currentPos[i];
  for (int s = 1; s <= steps; s++) {
    float t    = (float)s / (float)steps;
    float ease = t * t * (3.0f - 2.0f * t);
    for (int i = 0; i < NUM_SERVOS; i++) {
      int pulse = (int)(startPos[i] + ease * (targetPos[i] - startPos[i]));
      setServo(i, pulse);
    }
    delay(DELAY_TIME);
  }
}

void poseStand() {
  for (int i = 0; i < NUM_SERVOS; i++) targetPos[i] = CENTER;
  moveToTargets(400);
}

// ── State transitions ─────────────────────────────────────────────────

static void enterStill() {
  for (int i = 0; i < NUM_SERVOS; i++) targetPos[i] = CENTER;
  moveToTargets(400);
  robotState = STATE_STILL;
  broadcast("[Albert] State: STILL");
}

static void enterMoving() {
  if (active_traj == nullptr) {
    broadcast("[Albert] No trajectory selected");
    return;
  }
  for (int j = 0; j < TRAJ_JOINTS; j++) {
    int   ch      = TRAJ_TO_SERVO[j];
    float rel_rad = (float)active_traj[0][j] / (float)TRAJ_SCALE;
    targetPos[ch] = (float)constrain(
      CENTER + (int)(rel_rad * PULSE_PER_RAD * JOINT_DIR[ch]), SERVOMIN, SERVOMAX);
  }
  moveToTargets(500);
  delay(100);
  traj_step    = 0;
  traj_last_ms = millis();
  robotState   = STATE_MOVING;
}

// ── Trajectory tick ───────────────────────────────────────────────────

static void trajWriteStep(int step) {
  for (int j = 0; j < TRAJ_JOINTS; j++) {
    int   ch      = TRAJ_TO_SERVO[j];
    float rel_rad = (float)active_traj[step][j] / (float)TRAJ_SCALE;
    int   pulse   = constrain(
      CENTER + (int)(rel_rad * PULSE_PER_RAD * JOINT_DIR[ch]), SERVOMIN, SERVOMAX);
    pwm.setPWM(ch, 0, pulse);
    currentPos[ch] = (float)pulse;
    targetPos[ch]  = (float)pulse;
  }
}

static void tickTrajectory() {
  unsigned long now = millis();
  if ((now - traj_last_ms) < (unsigned long)TRAJ_DT_MS) return;
  traj_last_ms = now;
  trajWriteStep(traj_step);
  if (++traj_step >= active_steps) traj_step = 0;
}

// ── Command handler ───────────────────────────────────────────────────

static void handleCmd(char cmd) {
  switch (cmd) {
    case 's': case 'S':
      enterStill();
      break;
    case 'f': case 'F':
      active_traj  = traj_fwd;
      active_steps = TRAJ_FWD_STEPS;
      enterMoving();
      broadcast("[Albert] Moving: FWD");
      break;
    case 'b': case 'B':
      active_traj  = traj_bwd;
      active_steps = TRAJ_BWD_STEPS;
      enterMoving();
      broadcast("[Albert] Moving: BWD");
      break;
    case 'r': case 'R':
      active_traj  = traj_right;
      active_steps = TRAJ_RIGHT_STEPS;
      enterMoving();
      broadcast("[Albert] Moving: RIGHT");
      break;
    case 'l': case 'L':
      active_traj  = traj_left;
      active_steps = TRAJ_LEFT_STEPS;
      enterMoving();
      broadcast("[Albert] Moving: LEFT");
      break;
    default:
      broadcast("[Albert] Commands: 's'=still | 'f'=fwd | 'b'=bwd | 'r'=right | 'l'=left");
      break;
  }
}

static void handleSerial() {
  if (Serial.available()) {
    char cmd = Serial.read();
    while (Serial.available()) Serial.read();
    handleCmd(cmd);
  }
  if (BT.connected() && BT.available()) {
    char cmd = BT.read();
    while (BT.available()) BT.read();
    handleCmd(cmd);
  }
}

// ── Setup / Loop ──────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  BT.begin(BT_DEVICE_NAME);
  Serial.println("[Albert] Bluetooth started, device name: " BT_DEVICE_NAME);

  pwm.begin();
  pwm.setPWMFreq(50);
  for (int i = 0; i < NUM_SERVOS; i++) {
    currentPos[i] = CENTER;
    targetPos[i]  = CENTER;
    pwm.setPWM(i, 0, CENTER);
  }
  delay(500);
  poseStand();
  delay(500);

  while (Serial.available()) Serial.read();
  if (BT.connected()) while (BT.available()) BT.read();

  robotState = STATE_STILL;
  broadcast("[Albert] Ready. Commands: 's'=still | 'f'=fwd | 'b'=bwd | 'r'=right | 'l'=left");
}

void loop() {
  handleSerial();
  if (robotState == STATE_MOVING) tickTrajectory();
}
