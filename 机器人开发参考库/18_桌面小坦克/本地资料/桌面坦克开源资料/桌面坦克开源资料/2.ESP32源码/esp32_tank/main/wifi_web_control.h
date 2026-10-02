#pragma once

#include <stdbool.h>

#include "esp_err.h"
#include "motor.h"
#include "tank_control.h"

esp_err_t wifi_web_control_start(TankControl *ctrl, DualMotor *motors);

void wifi_web_control_set_boot_button(gpio_num_t gpio);

esp_err_t wifi_web_control_enter_provisioning(void);

void wifi_web_control_set_speed_scale(int percent);

int wifi_web_control_get_speed_scale(void);

bool wifi_web_control_is_provisioning(void);

bool wifi_web_control_is_wifi_connected(void);