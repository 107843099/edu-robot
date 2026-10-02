#pragma once

#include "idf_compat.h"
#include <stdbool.h>
#include <stdint.h>

typedef struct
{
	gpio_num_t pin_dir_a;
	gpio_num_t pin_dir_b;
	gpio_num_t pwm_gpio;      // PWM enable pin connected to driver EN/ON or one IN pin
	ledc_channel_t pwm_channel;
} MotorChannelConfig;

typedef struct
{
	MotorChannelConfig left;
	MotorChannelConfig right;
	gpio_num_t pin_stby;      // TB6612 STBY pin, set to GPIO_NUM_NC if hard-wired to 3V3
	ledc_timer_t pwm_timer;
	int pwm_frequency_hz;
	int pwm_resolution_bits; // e.g. LEDC_TIMER_10_BIT -> 10
	int pwm_max_duty;        // computed as (1 << resolution) - 1
	bool invert_left;        // if wiring inverted
	bool invert_right;       // if wiring inverted
} DualMotorConfig;

typedef struct
{
	DualMotorConfig cfg;
	bool initialized;
} DualMotor;

// Create a default config (pins to be adjusted as needed)
DualMotorConfig dual_motor_default_config(void);

esp_err_t dual_motor_init(DualMotor *driver, const DualMotorConfig *config);
void dual_motor_deinit(DualMotor *driver);

// speed in [-pwm_max_duty, pwm_max_duty]
esp_err_t motor_set_left(DualMotor *driver, int speed);
esp_err_t motor_set_right(DualMotor *driver, int speed);

// convenience: percent in [-100, 100]
esp_err_t motor_set_left_percent(DualMotor *driver, int percent);
esp_err_t motor_set_right_percent(DualMotor *driver, int percent);

// brake both motors (active braking by setting both H-bridge inputs high if supported; here: short brake)
void motor_brake(DualMotor *driver);

// stop both motors (coast)
void motor_stop(DualMotor *driver);

