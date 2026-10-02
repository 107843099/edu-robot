#include "motor.h"

static const char *TAG = "MOTOR";

static void configure_gpio_pair(gpio_num_t a, gpio_num_t b)
{
	gpio_config_t io = {
	    .pin_bit_mask = (1ULL << a) | (1ULL << b),
	    .mode = GPIO_MODE_OUTPUT,
	    .pull_up_en = GPIO_PULLUP_DISABLE,
	    .pull_down_en = GPIO_PULLDOWN_DISABLE,
	    .intr_type = GPIO_INTR_DISABLE,
	};
	gpio_config(&io);
	// default both low (coast)
	gpio_set_level(a, 0);
	gpio_set_level(b, 0);
}

DualMotorConfig dual_motor_default_config(void)
{
	// ESP32-S3-WROOM-1U + TB6612FNG (see schematic)
	DualMotorConfig cfg = {
	    .left =
	        {
	            .pin_dir_a = GPIO_NUM_5,  // AIN1
	            .pin_dir_b = GPIO_NUM_6,  // AIN2
	            .pwm_gpio = GPIO_NUM_4,   // PWMA
	            .pwm_channel = LEDC_CHANNEL_0,
	        },
	    .right =
	        {
	            .pin_dir_a = GPIO_NUM_15, // BIN1
	            .pin_dir_b = GPIO_NUM_2,  // BIN2
	            .pwm_gpio = GPIO_NUM_7,   // PWMB
	            .pwm_channel = LEDC_CHANNEL_1,
	        },
	    .pin_stby = GPIO_NUM_3, // STBY
	    .pwm_timer = LEDC_TIMER_0,
	    .pwm_frequency_hz = 20000, // 20kHz for quiet operation
	    .pwm_resolution_bits = 10, // 0..1023
	    .pwm_max_duty = (1 << 10) - 1,
	    .invert_left = false,
	    .invert_right = false,
	};
	return cfg;
}

static esp_err_t configure_pwm(const DualMotorConfig *cfg)
{
	ledc_timer_config_t tcfg = {
	    .speed_mode = LEDC_LOW_SPEED_MODE,
	    .duty_resolution = (ledc_timer_bit_t)cfg->pwm_resolution_bits,
	    .timer_num = cfg->pwm_timer,
	    .freq_hz = cfg->pwm_frequency_hz,
	    .clk_cfg = LEDC_AUTO_CLK,
	};
	ESP_RETURN_ON_ERROR(ledc_timer_config(&tcfg), TAG, "timer config failed");

	ledc_channel_config_t lch = {
	    .gpio_num = cfg->left.pwm_gpio,
	    .speed_mode = LEDC_LOW_SPEED_MODE,
	    .channel = cfg->left.pwm_channel,
	    .intr_type = LEDC_INTR_DISABLE,
	    .timer_sel = cfg->pwm_timer,
	    .duty = 0,
	    .hpoint = 0,
	};
	ESP_RETURN_ON_ERROR(ledc_channel_config(&lch), TAG, "left channel failed");

	lch.channel = cfg->right.pwm_channel;
	lch.gpio_num = cfg->right.pwm_gpio;
	ESP_RETURN_ON_ERROR(ledc_channel_config(&lch), TAG, "right channel failed");

	return ESP_OK;
}

static inline int clamp_int(int val, int lo, int hi)
{
	if (val < lo) return lo;
	if (val > hi) return hi;
	return val;
}

esp_err_t dual_motor_init(DualMotor *driver, const DualMotorConfig *config)
{
	if (driver == NULL || config == NULL) return ESP_ERR_INVALID_ARG;
	driver->cfg = *config;
	driver->cfg.pwm_max_duty = (1 << driver->cfg.pwm_resolution_bits) - 1;

	configure_gpio_pair(driver->cfg.left.pin_dir_a, driver->cfg.left.pin_dir_b);
	configure_gpio_pair(driver->cfg.right.pin_dir_a, driver->cfg.right.pin_dir_b);
	if (driver->cfg.pin_stby != GPIO_NUM_NC)
	{
		gpio_config_t stby_io = {
		    .pin_bit_mask = (1ULL << driver->cfg.pin_stby),
		    .mode = GPIO_MODE_OUTPUT,
		    .pull_up_en = GPIO_PULLUP_DISABLE,
		    .pull_down_en = GPIO_PULLDOWN_DISABLE,
		    .intr_type = GPIO_INTR_DISABLE,
		};
		gpio_config(&stby_io);
		gpio_set_level(driver->cfg.pin_stby, 1); // enable TB6612
	}
	ESP_RETURN_ON_ERROR(configure_pwm(&driver->cfg), TAG, "pwm setup failed");
	driver->initialized = true;
	ESP_LOGI(TAG, "initialized: freq=%dHz, res=%dbit, max=%d", driver->cfg.pwm_frequency_hz, driver->cfg.pwm_resolution_bits, driver->cfg.pwm_max_duty);
	return ESP_OK;
}

void dual_motor_deinit(DualMotor *driver)
{
	if (!driver || !driver->initialized) return;
	motor_stop(driver);
	driver->initialized = false;
}

static void set_dir_and_duty(const MotorChannelConfig *m,
                             bool invert,
                             int signed_duty,
                             int max_duty)
{
	int duty = clamp_int(signed_duty, -max_duty, max_duty);
	bool forward = duty >= 0;
	int absduty = forward ? duty : -duty;

	if (invert) forward = !forward;

	// For TB6612 wiring: IN1/IN2 decide direction, PWMA/PWMB provide speed PWM.

	// Direction pins (coast vs drive)
	if (absduty == 0)
	{
		// coast
		gpio_set_level(m->pin_dir_a, 0);
		gpio_set_level(m->pin_dir_b, 0);
	}
	else
	{
		if (forward)
		{
			gpio_set_level(m->pin_dir_a, 1);
			gpio_set_level(m->pin_dir_b, 0);
		}
		else
		{
			gpio_set_level(m->pin_dir_a, 0);
			gpio_set_level(m->pin_dir_b, 1);
		}
	}

	// Apply PWM duty to the motor channel.
	ledc_set_duty(LEDC_LOW_SPEED_MODE, m->pwm_channel, absduty);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, m->pwm_channel);
}

esp_err_t motor_set_left(DualMotor *driver, int speed)
{
	if (!driver || !driver->initialized) return ESP_ERR_INVALID_STATE;
	set_dir_and_duty(&driver->cfg.left, driver->cfg.invert_left, speed, driver->cfg.pwm_max_duty);
	return ESP_OK;
}

esp_err_t motor_set_right(DualMotor *driver, int speed)
{
	if (!driver || !driver->initialized) return ESP_ERR_INVALID_STATE;
	set_dir_and_duty(&driver->cfg.right, driver->cfg.invert_right, speed, driver->cfg.pwm_max_duty);
	return ESP_OK;
}

static int percent_to_duty(const DualMotor *driver, int percent)
{
	int p = clamp_int(percent, -100, 100);
	long duty = (long)driver->cfg.pwm_max_duty * (p >= 0 ? p : -p) / 100;
	return p >= 0 ? (int)duty : -(int)duty;
}

esp_err_t motor_set_left_percent(DualMotor *driver, int percent)
{
	if (!driver || !driver->initialized) return ESP_ERR_INVALID_STATE;
	return motor_set_left(driver, percent_to_duty(driver, percent));
}

esp_err_t motor_set_right_percent(DualMotor *driver, int percent)
{
	if (!driver || !driver->initialized) return ESP_ERR_INVALID_STATE;
	return motor_set_right(driver, percent_to_duty(driver, percent));
}

void motor_brake(DualMotor *driver)
{
	if (!driver || !driver->initialized) return;
	// short brake: both pins high
	gpio_set_level(driver->cfg.left.pin_dir_a, 1);
	gpio_set_level(driver->cfg.left.pin_dir_b, 1);
	gpio_set_level(driver->cfg.right.pin_dir_a, 1);
	gpio_set_level(driver->cfg.right.pin_dir_b, 1);
	ledc_set_duty(LEDC_LOW_SPEED_MODE, driver->cfg.left.pwm_channel, 0);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, driver->cfg.left.pwm_channel);
	ledc_set_duty(LEDC_LOW_SPEED_MODE, driver->cfg.right.pwm_channel, 0);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, driver->cfg.right.pwm_channel);
}

void motor_stop(DualMotor *driver)
{
	if (!driver || !driver->initialized) return;
	gpio_set_level(driver->cfg.left.pin_dir_a, 0);
	gpio_set_level(driver->cfg.left.pin_dir_b, 0);
	gpio_set_level(driver->cfg.right.pin_dir_a, 0);
	gpio_set_level(driver->cfg.right.pin_dir_b, 0);
	ledc_set_duty(LEDC_LOW_SPEED_MODE, driver->cfg.left.pwm_channel, 0);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, driver->cfg.left.pwm_channel);
	ledc_set_duty(LEDC_LOW_SPEED_MODE, driver->cfg.right.pwm_channel, 0);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, driver->cfg.right.pwm_channel);
}

