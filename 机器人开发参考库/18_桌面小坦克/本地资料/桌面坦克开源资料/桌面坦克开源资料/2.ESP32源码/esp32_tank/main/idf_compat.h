#pragma once

// This header provides editor/linter-friendly fallbacks when not compiling under ESP-IDF.
// When building with ESP-IDF, ESP_PLATFORM is defined and real headers are used.

#ifdef ESP_PLATFORM
#include "esp_err.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_check.h"
#include "esp_log.h"
#else
#include <stdint.h>
#include <stddef.h>
typedef int esp_err_t;
#define ESP_OK (0)
#define ESP_FAIL (-1)
#define ESP_ERR_INVALID_ARG (-2)
#define ESP_ERR_INVALID_STATE (-3)

// GPIO fallbacks
typedef int gpio_num_t;
typedef struct
{
	uint64_t pin_bit_mask;
	int mode;
	int pull_up_en;
	int pull_down_en;
	int intr_type;
} gpio_config_t;
static inline int gpio_config(const gpio_config_t *io) { (void)io; return 0; }
static inline int gpio_set_level(gpio_num_t pin, int level) { (void)pin; (void)level; return 0; }
static inline int gpio_get_level(gpio_num_t pin) { (void)pin; return 1; }

// LEDC fallbacks
typedef int ledc_channel_t;
typedef int ledc_timer_t;
typedef int ledc_timer_bit_t;
typedef struct
{
	int speed_mode;
	ledc_timer_bit_t duty_resolution;
	ledc_timer_t timer_num;
	int freq_hz;
	int clk_cfg;
} ledc_timer_config_t;
typedef struct
{
	int gpio_num;
	int speed_mode;
	ledc_channel_t channel;
	int intr_type;
	ledc_timer_t timer_sel;
	unsigned int duty;
	unsigned int hpoint;
} ledc_channel_config_t;
static inline int ledc_timer_config(const ledc_timer_config_t *c) { (void)c; return 0; }
static inline int ledc_channel_config(const ledc_channel_config_t *c) { (void)c; return 0; }
static inline int ledc_set_duty(int m, ledc_channel_t ch, unsigned int d) { (void)m; (void)ch; (void)d; return 0; }
static inline int ledc_update_duty(int m, ledc_channel_t ch) { (void)m; (void)ch; return 0; }

// constants fallbacks
#define GPIO_NUM_NC (-1)
#define GPIO_NUM_0 0
#define GPIO_NUM_1 1
#define GPIO_NUM_2 2
#define GPIO_NUM_3 3
#define GPIO_NUM_4 4
#define GPIO_NUM_5 5
#define GPIO_NUM_6 6
#define GPIO_NUM_7 7
#define GPIO_NUM_8 8
#define GPIO_NUM_9 9
#define GPIO_NUM_10 10
#define GPIO_NUM_15 15

#define GPIO_MODE_OUTPUT 1
#define GPIO_MODE_INPUT 2
#define GPIO_PULLUP_DISABLE 0
#define GPIO_PULLUP_ENABLE 1
#define GPIO_PULLDOWN_DISABLE 0
#define GPIO_INTR_DISABLE 0

#define LEDC_LOW_SPEED_MODE 0
#define LEDC_INTR_DISABLE 0
#define LEDC_CHANNEL_0 0
#define LEDC_CHANNEL_1 1
#define LEDC_TIMER_0 0
#define LEDC_USE_RC_FAST_CLK 0
#define LEDC_AUTO_CLK 0

#define ESP_RETURN_ON_ERROR(x, tag, msg) (void)(x); (void)(tag); (void)(msg)

// FreeRTOS fallbacks
typedef int TickType_t;
#define pdMS_TO_TICKS(ms) (ms)
static inline void vTaskDelay(TickType_t x) { (void)x; }

// Logging fallbacks
#define ESP_LOGI(tag, fmt, ...) (void)(tag); (void)(fmt)
#endif

