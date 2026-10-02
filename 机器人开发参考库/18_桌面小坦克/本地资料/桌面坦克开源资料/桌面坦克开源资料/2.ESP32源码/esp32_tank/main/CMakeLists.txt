idf_component_register(SRCS "tank_control.c" "motor.c" "wifi_web_control.c" "main.c"
                    INCLUDE_DIRS "."
                    REQUIRES esp_wifi esp_http_server mdns nvs_flash esp_netif esp_event esp_timer esp_driver_gpio esp_driver_ledc json)

target_add_binary_data(${COMPONENT_LIB} "web/index.html" TEXT)
target_add_binary_data(${COMPONENT_LIB} "web/setup.html" TEXT)
