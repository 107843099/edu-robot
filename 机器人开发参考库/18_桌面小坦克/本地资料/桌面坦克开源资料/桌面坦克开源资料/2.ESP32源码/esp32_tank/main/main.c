#include <stdio.h>
#include "motor.h"
#include "tank_control.h"
#include "wifi_web_control.h"
#include "sdkconfig.h"

#define BOOT_BUTTON_GPIO GPIO_NUM_0  // BOOT (IO0)
#define LED_GPIO GPIO_NUM_1          // LED (IO1)

static const int k_speed_levels[] = {50, 70, 90, 100};
static const int k_speed_levels_count = sizeof(k_speed_levels) / sizeof(k_speed_levels[0]);

static void configure_led(void)
{
	gpio_config_t io = {
	    .pin_bit_mask = (1ULL << LED_GPIO),
	    .mode = GPIO_MODE_OUTPUT,
	    .pull_up_en = GPIO_PULLUP_DISABLE,
	    .pull_down_en = GPIO_PULLDOWN_DISABLE,
	    .intr_type = GPIO_INTR_DISABLE,
	};
	gpio_config(&io);
	gpio_set_level(LED_GPIO, 0);
}

static void led_status_task(void *arg)
{
	(void)arg;
	bool on = false;

	while (1)
	{
		if (wifi_web_control_is_wifi_connected())
		{
			gpio_set_level(LED_GPIO, 1);
			vTaskDelay(pdMS_TO_TICKS(200));
		}
		else
		{
			on = !on;
			gpio_set_level(LED_GPIO, on ? 1 : 0);
			vTaskDelay(pdMS_TO_TICKS(400));
		}
	}
}

static void configure_boot_button(void)
{
	gpio_config_t io = {
	    .pin_bit_mask = (1ULL << BOOT_BUTTON_GPIO),
	    .mode = GPIO_MODE_INPUT,
	    .pull_up_en = GPIO_PULLUP_ENABLE,
	    .pull_down_en = GPIO_PULLDOWN_DISABLE,
	    .intr_type = GPIO_INTR_DISABLE,
	};
	gpio_config(&io);
}

static void handle_boot_button(int *speed_idx)
{
	if (gpio_get_level(BOOT_BUTTON_GPIO) != 0) return;

	vTaskDelay(pdMS_TO_TICKS(30));
	if (gpio_get_level(BOOT_BUTTON_GPIO) != 0) return;

	if (!wifi_web_control_is_wifi_connected())
	{
		if (!wifi_web_control_is_provisioning())
		{
			if (wifi_web_control_enter_provisioning() == ESP_OK)
			{
				ESP_LOGI("MAIN", "BOOT: provisioning mode, connect AP [%s]", CONFIG_TANK_AP_SSID);
			}
		}
		while (gpio_get_level(BOOT_BUTTON_GPIO) == 0)
		{
			vTaskDelay(pdMS_TO_TICKS(20));
		}
		return;
	}

	*speed_idx = (*speed_idx + 1) % k_speed_levels_count;
	wifi_web_control_set_speed_scale(k_speed_levels[*speed_idx]);
	ESP_LOGI("MAIN", "Speed level switched to %d%%", k_speed_levels[*speed_idx]);
	while (gpio_get_level(BOOT_BUTTON_GPIO) == 0)
	{
		vTaskDelay(pdMS_TO_TICKS(20));
	}
}

void app_main(void)
{
	DualMotor motors = {0};
	DualMotorConfig cfg = dual_motor_default_config();

	if (dual_motor_init(&motors, &cfg) != ESP_OK)
	{
		printf("Motor init failed\n");
		return;
	}

	TankControl ctrl;
	tank_control_init(&ctrl);
	configure_led();
	configure_boot_button();
	xTaskCreate(led_status_task, "led_sta", 2048, NULL, 3, NULL);

	int speed_idx = 1;
	wifi_web_control_set_speed_scale(k_speed_levels[speed_idx]);
	wifi_web_control_set_boot_button(BOOT_BUTTON_GPIO);

	if (wifi_web_control_start(&ctrl, &motors) != ESP_OK)
	{
		ESP_LOGE("MAIN", "Network init failed");
		return;
	}

	if (wifi_web_control_is_provisioning())
	{
		ESP_LOGI("MAIN", "Provisioning mode: connect AP [%s], open http://192.168.4.1", CONFIG_TANK_AP_SSID);
	}
	else
	{
		ESP_LOGI("MAIN", "Control ready. BOOT key cycles speed, current=%d%%", k_speed_levels[speed_idx]);
	}

	while (1)
	{
		handle_boot_button(&speed_idx);
		vTaskDelay(pdMS_TO_TICKS(50));
	}
}
