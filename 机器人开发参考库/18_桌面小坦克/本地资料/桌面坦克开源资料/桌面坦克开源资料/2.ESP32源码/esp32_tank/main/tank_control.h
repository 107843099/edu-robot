#pragma once

#include "motor.h"

typedef struct
{
	float max_linear;   // m/s or abstract units
	float max_angular;  // rad/s or abstract units
	int max_percent;    // absolute percent limit per wheel [0..100]
	int deadzone_percent; // deadzone to overcome static friction
	int ramp_percent_per_step; // simple ramp per call
	int last_left_percent;
	int last_right_percent;
} TankControl;

void tank_control_init(TankControl *tc);

// linear in [-max_linear, max_linear], angular in [-max_angular, max_angular]
void tank_drive_linear_angular(TankControl *tc, DualMotor *drv, float linear, float angular);

// direct percent control with ramp + deadzone handling
void tank_drive_percents(TankControl *tc, DualMotor *drv, int left_percent, int right_percent);

// stop helper
void tank_stop(TankControl *tc, DualMotor *drv);

