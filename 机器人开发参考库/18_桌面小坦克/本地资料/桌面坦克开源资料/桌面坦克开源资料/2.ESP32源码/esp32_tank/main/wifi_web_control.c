#include "wifi_web_control.h"

#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <sys/param.h>

#include "esp_event.h"
#include "esp_check.h"
#include "esp_http_server.h"
#if CONFIG_TANK_USE_HTTPS
#include "esp_https_server.h"
#endif
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "mdns.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "cJSON.h"

#include "sdkconfig.h"

extern const char index_html_start[] asm("_binary_index_html_start");
extern const char index_html_end[] asm("_binary_index_html_end");
extern const char setup_html_start[] asm("_binary_setup_html_start");
extern const char setup_html_end[] asm("_binary_setup_html_end");
#if CONFIG_TANK_USE_HTTPS
extern const unsigned char certs_server_crt_start[] asm("_binary_certs_server_crt_start");
extern const unsigned char certs_server_crt_end[] asm("_binary_certs_server_crt_end");
extern const unsigned char certs_server_key_start[] asm("_binary_certs_server_key_start");
extern const unsigned char certs_server_key_end[] asm("_binary_certs_server_key_end");
#endif

static const char *TAG = "WIFI_WEB";

#define NVS_NS "tank_wifi"
#define NVS_KEY_SSID "ssid"
#define NVS_KEY_PASS "pass"

#define NVS_MOTOR_NS "tank_motor"
#define NVS_KEY_INV_L "inv_l"
#define NVS_KEY_INV_R "inv_r"
#define NVS_KEY_SWAP "swap_lr"

#define NVS_PATH_NS "tank_path"
#define NVS_KEY_PATH "path_bin"
#define PATH_MAX_STEPS 20
#define PATH_NVS_MAGIC 0x54
#define PATH_NVS_VER 1

typedef enum {
	PATH_DIR_FORWARD = 0,
	PATH_DIR_BACKWARD = 1,
	PATH_DIR_LEFT = 2,
	PATH_DIR_RIGHT = 3,
	PATH_DIR_STOP = 4,
} path_dir_t;

typedef struct __attribute__((packed)) {
	uint8_t dir;
	uint8_t speed;
	uint16_t time_ms;
} path_step_t;

typedef struct __attribute__((packed)) {
	uint8_t magic;
	uint8_t version;
	uint8_t count;
	uint8_t loop;
	uint16_t loop_count;
	path_step_t steps[PATH_MAX_STEPS];
} path_blob_t;

#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT BIT1
#define WIFI_MAX_RETRY 10

#define AP_IP_ADDR "192.168.4.1"
#define DNS_PORT 53

static EventGroupHandle_t s_wifi_events;
static httpd_handle_t s_httpd = NULL;
#if CONFIG_TANK_USE_HTTPS
static httpd_handle_t s_http_redirect = NULL;
#endif
static int s_wifi_retry = 0;
static bool s_provisioning = false;
static bool s_wifi_connected = false;
static bool s_wifi_stack_ready = false;
static bool s_connecting_from_portal = false;
static bool s_watchdog_started = false;
static TaskHandle_t s_dns_task = NULL;
static gpio_num_t s_boot_gpio = GPIO_NUM_NC;

static TankControl *s_ctrl = NULL;
static DualMotor *s_motors = NULL;
static int s_speed_scale = 70;
static bool s_invert_left = false;
static bool s_invert_right = false;
static bool s_swap_lr = false;
static path_blob_t s_path = {
    .magic = PATH_NVS_MAGIC,
    .version = PATH_NVS_VER,
    .count = 0,
    .loop = 0,
    .loop_count = 0,
};
static int64_t s_last_cmd_us = 0;
static portMUX_TYPE s_cmd_lock = portMUX_INITIALIZER_UNLOCKED;

static void watchdog_task(void *arg);
static void nvs_load_motor_calib(void);
static esp_err_t nvs_save_motor_calib(void);
static void nvs_load_path(void);
static esp_err_t nvs_save_path(void);

/* ---------- motor control ---------- */

static void apply_drive(int left, int right)
{
	if (!s_ctrl || !s_motors) return;

	/* Wiring calibration: swap channels and/or reverse polarity. */
	if (s_swap_lr)
	{
		int tmp = left;
		left = right;
		right = tmp;
	}
	if (s_invert_left) left = -left;
	if (s_invert_right) right = -right;

	left = left * s_speed_scale / 100;
	right = right * s_speed_scale / 100;
	tank_drive_percents(s_ctrl, s_motors, left, right);
}

static void apply_stop(void)
{
	if (!s_ctrl || !s_motors) return;
	tank_stop(s_ctrl, s_motors);
}

static void mark_command_received(void)
{
	portENTER_CRITICAL(&s_cmd_lock);
	s_last_cmd_us = esp_timer_get_time();
	portEXIT_CRITICAL(&s_cmd_lock);
}

static bool parse_drive_json(const char *json, int *left, int *right)
{
	const char *lp = strstr(json, "\"left\"");
	const char *rp = strstr(json, "\"right\"");
	if (!lp || !rp) return false;
	lp = strchr(lp, ':');
	rp = strchr(rp, ':');
	if (!lp || !rp) return false;
	*left = (int)strtol(lp + 1, NULL, 10);
	*right = (int)strtol(rp + 1, NULL, 10);
	return true;
}

static bool parse_stop_json(const char *json)
{
	return strstr(json, "\"stop\"") != NULL && strstr(json, "true") != NULL;
}

static bool parse_speed_json(const char *json, int *speed)
{
	const char *p = strstr(json, "\"speed\"");
	if (!p) return false;
	p = strchr(p, ':');
	if (!p) return false;
	*speed = (int)strtol(p + 1, NULL, 10);
	return true;
}

static bool json_extract_bool(const char *json, const char *key, bool *out)
{
	char pattern[32];
	snprintf(pattern, sizeof(pattern), "\"%s\"", key);
	const char *p = strstr(json, pattern);
	if (!p) return false;
	p = strchr(p + strlen(pattern), ':');
	if (!p) return false;
	p++;
	while (*p == ' ' || *p == '\t') p++;
	if (strncmp(p, "true", 4) == 0)
	{
		*out = true;
		return true;
	}
	if (strncmp(p, "false", 5) == 0)
	{
		*out = false;
		return true;
	}
	if (*p == '1')
	{
		*out = true;
		return true;
	}
	if (*p == '0')
	{
		*out = false;
		return true;
	}
	return false;
}

static bool parse_calib_json(const char *json)
{
	if (strstr(json, "\"calib\"") == NULL &&
	    strstr(json, "\"invert_left\"") == NULL &&
	    strstr(json, "\"invert_right\"") == NULL &&
	    strstr(json, "\"swap_lr\"") == NULL)
	{
		return false;
	}

	bool changed = false;
	bool v = false;
	if (json_extract_bool(json, "invert_left", &v))
	{
		s_invert_left = v;
		changed = true;
	}
	if (json_extract_bool(json, "invert_right", &v))
	{
		s_invert_right = v;
		changed = true;
	}
	if (json_extract_bool(json, "swap_lr", &v))
	{
		s_swap_lr = v;
		changed = true;
	}
	return changed;
}

static void handle_control_message(const char *payload)
{
	int left = 0;
	int right = 0;
	int speed = 0;

	if (parse_stop_json(payload))
	{
		apply_stop();
		mark_command_received();
		return;
	}
	if (parse_calib_json(payload))
	{
		nvs_save_motor_calib();
		ESP_LOGI(TAG, "Calib: inv_l=%d inv_r=%d swap=%d",
		         s_invert_left, s_invert_right, s_swap_lr);
		mark_command_received();
		return;
	}
	if (parse_speed_json(payload, &speed))
	{
		wifi_web_control_set_speed_scale(speed);
		mark_command_received();
		return;
	}
	if (parse_drive_json(payload, &left, &right))
	{
		apply_drive(left, right);
		mark_command_received();
	}
}

/* ---------- NVS WiFi storage ---------- */

static bool nvs_load_wifi(char *ssid, size_t ssid_len, char *pass, size_t pass_len)
{
	nvs_handle_t h;
	if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return false;

	size_t sl = ssid_len;
	size_t pl = pass_len;
	bool ok = nvs_get_str(h, NVS_KEY_SSID, ssid, &sl) == ESP_OK && ssid[0] != '\0';
	if (ok)
	{
		if (nvs_get_str(h, NVS_KEY_PASS, pass, &pl) != ESP_OK) pass[0] = '\0';
	}
	nvs_close(h);
	return ok;
}

static esp_err_t nvs_save_wifi(const char *ssid, const char *pass)
{
	nvs_handle_t h;
	ESP_RETURN_ON_ERROR(nvs_open(NVS_NS, NVS_READWRITE, &h), TAG, "nvs open");
	ESP_RETURN_ON_ERROR(nvs_set_str(h, NVS_KEY_SSID, ssid), TAG, "nvs ssid");
	ESP_RETURN_ON_ERROR(nvs_set_str(h, NVS_KEY_PASS, pass ? pass : ""), TAG, "nvs pass");
	ESP_RETURN_ON_ERROR(nvs_commit(h), TAG, "nvs commit");
	nvs_close(h);
	return ESP_OK;
}

static void nvs_load_motor_calib(void)
{
	nvs_handle_t h;
	if (nvs_open(NVS_MOTOR_NS, NVS_READONLY, &h) != ESP_OK) return;

	uint8_t v = 0;
	if (nvs_get_u8(h, NVS_KEY_INV_L, &v) == ESP_OK) s_invert_left = v != 0;
	if (nvs_get_u8(h, NVS_KEY_INV_R, &v) == ESP_OK) s_invert_right = v != 0;
	if (nvs_get_u8(h, NVS_KEY_SWAP, &v) == ESP_OK) s_swap_lr = v != 0;
	nvs_close(h);
	ESP_LOGI(TAG, "Loaded calib: inv_l=%d inv_r=%d swap=%d",
	         s_invert_left, s_invert_right, s_swap_lr);
}

static esp_err_t nvs_save_motor_calib(void)
{
	nvs_handle_t h;
	ESP_RETURN_ON_ERROR(nvs_open(NVS_MOTOR_NS, NVS_READWRITE, &h), TAG, "nvs motor open");
	ESP_RETURN_ON_ERROR(nvs_set_u8(h, NVS_KEY_INV_L, s_invert_left ? 1 : 0), TAG, "inv_l");
	ESP_RETURN_ON_ERROR(nvs_set_u8(h, NVS_KEY_INV_R, s_invert_right ? 1 : 0), TAG, "inv_r");
	ESP_RETURN_ON_ERROR(nvs_set_u8(h, NVS_KEY_SWAP, s_swap_lr ? 1 : 0), TAG, "swap");
	ESP_RETURN_ON_ERROR(nvs_commit(h), TAG, "nvs motor commit");
	nvs_close(h);
	return ESP_OK;
}

static void nvs_load_path(void)
{
	nvs_handle_t h;
	if (nvs_open(NVS_PATH_NS, NVS_READONLY, &h) != ESP_OK) return;

	path_blob_t blob = {0};
	size_t len = sizeof(blob);
	esp_err_t err = nvs_get_blob(h, NVS_KEY_PATH, &blob, &len);
	nvs_close(h);
	if (err != ESP_OK) return;
	if (len < 6 || blob.magic != PATH_NVS_MAGIC || blob.version != PATH_NVS_VER) return;
	if (blob.count > PATH_MAX_STEPS) blob.count = PATH_MAX_STEPS;

	s_path = blob;
	s_path.magic = PATH_NVS_MAGIC;
	s_path.version = PATH_NVS_VER;
	ESP_LOGI(TAG, "Loaded path: %u steps, loop=%u count=%u",
	         s_path.count, s_path.loop, s_path.loop_count);
}

static esp_err_t nvs_save_path(void)
{
	nvs_handle_t h;
	ESP_RETURN_ON_ERROR(nvs_open(NVS_PATH_NS, NVS_READWRITE, &h), TAG, "nvs path open");
	s_path.magic = PATH_NVS_MAGIC;
	s_path.version = PATH_NVS_VER;
	size_t len = offsetof(path_blob_t, steps) + (size_t)s_path.count * sizeof(path_step_t);
	ESP_RETURN_ON_ERROR(nvs_set_blob(h, NVS_KEY_PATH, &s_path, len), TAG, "nvs path blob");
	ESP_RETURN_ON_ERROR(nvs_commit(h), TAG, "nvs path commit");
	nvs_close(h);
	ESP_LOGI(TAG, "Saved path: %u steps", s_path.count);
	return ESP_OK;
}

static const char *path_dir_to_str(uint8_t dir)
{
	switch (dir)
	{
	case PATH_DIR_BACKWARD: return "backward";
	case PATH_DIR_LEFT: return "left";
	case PATH_DIR_RIGHT: return "right";
	case PATH_DIR_STOP: return "stop";
	case PATH_DIR_FORWARD:
	default: return "forward";
	}
}

static bool path_dir_from_str(const char *s, uint8_t *out)
{
	if (!s || !out) return false;
	if (strcmp(s, "forward") == 0) { *out = PATH_DIR_FORWARD; return true; }
	if (strcmp(s, "backward") == 0) { *out = PATH_DIR_BACKWARD; return true; }
	if (strcmp(s, "left") == 0) { *out = PATH_DIR_LEFT; return true; }
	if (strcmp(s, "right") == 0) { *out = PATH_DIR_RIGHT; return true; }
	if (strcmp(s, "stop") == 0) { *out = PATH_DIR_STOP; return true; }
	return false;
}

static bool kconfig_has_fallback_wifi(void)
{
	return strcmp(CONFIG_TANK_WIFI_SSID, "myssid") != 0 && CONFIG_TANK_WIFI_SSID[0] != '\0';
}

static void stop_webservers(void)
{
#if CONFIG_TANK_USE_HTTPS
	if (s_http_redirect)
	{
		httpd_stop(s_http_redirect);
		s_http_redirect = NULL;
	}
#endif
	if (s_httpd)
	{
		httpd_stop(s_httpd);
		s_httpd = NULL;
	}
}

static bool boot_button_pressed(void)
{
	if (s_boot_gpio == GPIO_NUM_NC) return false;
	if (gpio_get_level(s_boot_gpio) != 0) return false;
	vTaskDelay(pdMS_TO_TICKS(30));
	if (gpio_get_level(s_boot_gpio) != 0) return false;
	return true;
}

static void boot_button_wait_release(void)
{
	if (s_boot_gpio == GPIO_NUM_NC) return;
	while (gpio_get_level(s_boot_gpio) == 0)
	{
		vTaskDelay(pdMS_TO_TICKS(20));
	}
}

static void ensure_watchdog_task(void)
{
	if (s_watchdog_started) return;
	xTaskCreate(watchdog_task, "web_wd", 2048, NULL, 5, NULL);
	s_watchdog_started = true;
}

static esp_err_t connect_sta_while_provisioning(const char *ssid, const char *pass,
                                                char *ip_out, size_t ip_out_len,
                                                uint32_t timeout_ms)
{
	esp_netif_create_default_wifi_sta();
	xEventGroupClearBits(s_wifi_events, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT);
	s_wifi_retry = 0;
	s_connecting_from_portal = true;

	wifi_config_t sta_cfg = {0};
	strncpy((char *)sta_cfg.sta.ssid, ssid, sizeof(sta_cfg.sta.ssid) - 1);
	strncpy((char *)sta_cfg.sta.password, pass ? pass : "", sizeof(sta_cfg.sta.password) - 1);
	sta_cfg.sta.threshold.authmode = (pass && pass[0] != '\0') ? WIFI_AUTH_WPA2_PSK : WIFI_AUTH_OPEN;

	ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_APSTA));
	ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &sta_cfg));
	ESP_ERROR_CHECK(esp_wifi_connect());

	ESP_LOGI(TAG, "Portal: connecting STA -> %s", ssid);

	uint32_t waited_ms = 0;
	esp_err_t result = ESP_FAIL;
	while (waited_ms < timeout_ms)
	{
		EventBits_t bits = xEventGroupWaitBits(s_wifi_events,
		                                       WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
		                                       pdFALSE, pdFALSE,
		                                       pdMS_TO_TICKS(100));
		waited_ms += 100;
		if (bits & WIFI_CONNECTED_BIT)
		{
			esp_netif_t *sta_netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
			if (sta_netif)
			{
				esp_netif_ip_info_t ip_info;
				if (esp_netif_get_ip_info(sta_netif, &ip_info) == ESP_OK)
				{
					snprintf(ip_out, ip_out_len, IPSTR, IP2STR(&ip_info.ip));
					result = ESP_OK;
				}
			}
			break;
		}
		if (bits & WIFI_FAIL_BIT) break;
	}

	s_connecting_from_portal = false;
	return result;
}

static void switch_from_provision_to_control(void)
{
	s_provisioning = false;

	stop_webservers();

	ESP_ERROR_CHECK(esp_wifi_stop());
	vTaskDelay(pdMS_TO_TICKS(200));

	ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
	ESP_ERROR_CHECK(esp_wifi_start());
}

/* ---------- HTTP handlers ---------- */

static esp_err_t send_embedded(httpd_req_t *req, const char *start, const char *end)
{
	const size_t len = (size_t)(end - start);
	httpd_resp_set_type(req, "text/html");
	return httpd_resp_send(req, start, len);
}

static esp_err_t index_handler(httpd_req_t *req)
{
	return send_embedded(req, index_html_start, index_html_end);
}

static esp_err_t calib_get_handler(httpd_req_t *req)
{
	char body[128];
	snprintf(body, sizeof(body),
	         "{\"invert_left\":%s,\"invert_right\":%s,\"swap_lr\":%s}",
	         s_invert_left ? "true" : "false",
	         s_invert_right ? "true" : "false",
	         s_swap_lr ? "true" : "false");
	httpd_resp_set_type(req, "application/json");
	httpd_resp_set_hdr(req, "Cache-Control", "no-store");
	return httpd_resp_send(req, body, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t path_get_handler(httpd_req_t *req)
{
	cJSON *root = cJSON_CreateObject();
	if (!root) return ESP_ERR_NO_MEM;

	cJSON_AddBoolToObject(root, "loop", s_path.loop != 0);
	cJSON_AddNumberToObject(root, "loop_count", s_path.loop_count);

	cJSON *steps = cJSON_AddArrayToObject(root, "steps");
	if (!steps)
	{
		cJSON_Delete(root);
		return ESP_ERR_NO_MEM;
	}

	for (uint8_t i = 0; i < s_path.count; ++i)
	{
		cJSON *item = cJSON_CreateObject();
		if (!item) continue;
		cJSON_AddStringToObject(item, "dir", path_dir_to_str(s_path.steps[i].dir));
		cJSON_AddNumberToObject(item, "speed", s_path.steps[i].speed);
		cJSON_AddNumberToObject(item, "time", s_path.steps[i].time_ms / 1000.0);
		cJSON_AddItemToArray(steps, item);
	}

	char *body = cJSON_PrintUnformatted(root);
	cJSON_Delete(root);
	if (!body) return ESP_ERR_NO_MEM;

	httpd_resp_set_type(req, "application/json");
	httpd_resp_set_hdr(req, "Cache-Control", "no-store");
	esp_err_t ret = httpd_resp_send(req, body, HTTPD_RESP_USE_STRLEN);
	free(body);
	return ret;
}

static esp_err_t path_post_handler(httpd_req_t *req)
{
	if (req->content_len <= 0 || req->content_len > 2048)
	{
		httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "bad body");
		return ESP_FAIL;
	}

	char *buf = calloc(1, req->content_len + 1);
	if (!buf) return ESP_ERR_NO_MEM;

	int received = 0;
	while (received < req->content_len)
	{
		int r = httpd_req_recv(req, buf + received, req->content_len - received);
		if (r <= 0)
		{
			free(buf);
			httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR, "recv fail");
			return ESP_FAIL;
		}
		received += r;
	}

	cJSON *root = cJSON_Parse(buf);
	free(buf);
	if (!root)
	{
		httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "bad json");
		return ESP_FAIL;
	}

	path_blob_t next = {
	    .magic = PATH_NVS_MAGIC,
	    .version = PATH_NVS_VER,
	    .count = 0,
	    .loop = 0,
	    .loop_count = 0,
	};

	cJSON *loop = cJSON_GetObjectItem(root, "loop");
	if (cJSON_IsBool(loop)) next.loop = cJSON_IsTrue(loop) ? 1 : 0;

	cJSON *loop_count = cJSON_GetObjectItem(root, "loop_count");
	if (cJSON_IsNumber(loop_count))
	{
		int v = loop_count->valueint;
		if (v < 0) v = 0;
		if (v > 9999) v = 9999;
		next.loop_count = (uint16_t)v;
	}

	cJSON *steps = cJSON_GetObjectItem(root, "steps");
	if (!cJSON_IsArray(steps))
	{
		cJSON_Delete(root);
		httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "steps required");
		return ESP_FAIL;
	}

	const int n = cJSON_GetArraySize(steps);
	if (n > PATH_MAX_STEPS)
	{
		cJSON_Delete(root);
		httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "too many steps");
		return ESP_FAIL;
	}

	for (int i = 0; i < n; ++i)
	{
		cJSON *item = cJSON_GetArrayItem(steps, i);
		if (!cJSON_IsObject(item)) continue;

		cJSON *dir = cJSON_GetObjectItem(item, "dir");
		cJSON *speed = cJSON_GetObjectItem(item, "speed");
		cJSON *time = cJSON_GetObjectItem(item, "time");
		if (!cJSON_IsString(dir) || !cJSON_IsNumber(speed) || !cJSON_IsNumber(time))
		{
			cJSON_Delete(root);
			httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "bad step");
			return ESP_FAIL;
		}

		uint8_t d = PATH_DIR_FORWARD;
		if (!path_dir_from_str(dir->valuestring, &d))
		{
			cJSON_Delete(root);
			httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "bad dir");
			return ESP_FAIL;
		}

		int sp = speed->valueint;
		if (sp < 10) sp = 10;
		if (sp > 100) sp = 100;

		double t = time->valuedouble;
		if (t < 0.1) t = 0.1;
		if (t > 60.0) t = 60.0;
		uint16_t time_ms = (uint16_t)(t * 1000.0 + 0.5);

		next.steps[next.count].dir = d;
		next.steps[next.count].speed = (uint8_t)sp;
		next.steps[next.count].time_ms = time_ms;
		next.count++;
	}

	cJSON_Delete(root);
	s_path = next;

	if (nvs_save_path() != ESP_OK)
	{
		httpd_resp_send_err(req, HTTPD_500_INTERNAL_SERVER_ERROR, "nvs fail");
		return ESP_FAIL;
	}

	httpd_resp_set_type(req, "application/json");
	return httpd_resp_sendstr(req, "{\"ok\":true}");
}

static esp_err_t setup_handler(httpd_req_t *req)
{
	return send_embedded(req, setup_html_start, setup_html_end);
}

static esp_err_t captive_redirect_handler(httpd_req_t *req)
{
	(void)req;
	httpd_resp_set_status(req, "302 Found");
	httpd_resp_set_hdr(req, "Location", "http://" AP_IP_ADDR "/");
	httpd_resp_send(req, NULL, 0);
	return ESP_OK;
}

#if CONFIG_TANK_USE_HTTPS
static esp_err_t https_redirect_handler(httpd_req_t *req)
{
	char loc[96];
	snprintf(loc, sizeof(loc), "https://%s.local/", CONFIG_TANK_MDNS_HOSTNAME);
	httpd_resp_set_status(req, "301 Moved Permanently");
	httpd_resp_set_hdr(req, "Location", loc);
	httpd_resp_send(req, NULL, 0);
	return ESP_OK;
}
#endif

static bool json_extract_string(const char *json, const char *key, char *out, size_t out_len)
{
	char pattern[32];
	snprintf(pattern, sizeof(pattern), "\"%s\"", key);
	const char *p = strstr(json, pattern);
	if (!p) return false;
	p = strchr(p + strlen(pattern), '"');
	if (!p) return false;
	p++;
	const char *end = strchr(p, '"');
	if (!end || (size_t)(end - p) >= out_len) return false;
	memcpy(out, p, (size_t)(end - p));
	out[end - p] = '\0';
	return true;
}

static esp_err_t wifi_save_handler(httpd_req_t *req)
{
	if (req->content_len <= 0 || req->content_len > 512)
	{
		httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "bad body");
		return ESP_FAIL;
	}

	char *buf = calloc(1, req->content_len + 1);
	if (!buf) return ESP_ERR_NO_MEM;

	int received = httpd_req_recv(req, buf, req->content_len);
	if (received <= 0)
	{
		free(buf);
		return ESP_FAIL;
	}

	char ssid[33] = {0};
	char pass[65] = {0};
	if (!json_extract_string(buf, "ssid", ssid, sizeof(ssid)) || ssid[0] == '\0')
	{
		free(buf);
		httpd_resp_set_type(req, "application/json");
		httpd_resp_sendstr(req, "{\"ok\":false,\"error\":\"SSID required\"}");
		return ESP_OK;
	}
	json_extract_string(buf, "password", pass, sizeof(pass));
	free(buf);

	if (nvs_save_wifi(ssid, pass) != ESP_OK)
	{
		httpd_resp_set_type(req, "application/json");
		httpd_resp_sendstr(req, "{\"ok\":false,\"error\":\"NVS save failed\"}");
		return ESP_OK;
	}

	char ip_str[16] = {0};
	if (connect_sta_while_provisioning(ssid, pass, ip_str, sizeof(ip_str), 30000) != ESP_OK)
	{
		httpd_resp_set_type(req, "application/json");
		httpd_resp_sendstr(req, "{\"ok\":false,\"error\":\"WiFi connect failed\"}");
		return ESP_OK;
	}

	char resp[96];
	snprintf(resp, sizeof(resp), "{\"ok\":true,\"ip\":\"%s\"}", ip_str);
	httpd_resp_set_type(req, "application/json");
	httpd_resp_sendstr(req, resp);

	ESP_LOGI(TAG, "Provision OK, visit http://%s", ip_str);
	switch_from_provision_to_control();
	return ESP_OK;
}

static esp_err_t ws_handler(httpd_req_t *req)
{
	if (req->method == HTTP_GET)
	{
		ESP_LOGI(TAG, "WebSocket connected");
		return ESP_OK;
	}

	httpd_ws_frame_t frame = {0};
	esp_err_t ret = httpd_ws_recv_frame(req, &frame, 0);
	if (ret != ESP_OK) return ret;
	if (frame.len == 0) return ESP_OK;

	uint8_t *buf = calloc(1, frame.len + 1);
	if (!buf) return ESP_ERR_NO_MEM;

	frame.payload = buf;
	ret = httpd_ws_recv_frame(req, &frame, frame.len);
	if (ret == ESP_OK && frame.type == HTTPD_WS_TYPE_TEXT)
	{
		handle_control_message((const char *)buf);
	}
	free(buf);
	return ret;
}

static void register_common_control_uris(httpd_handle_t server)
{
	httpd_uri_t index_uri = {.uri = "/", .method = HTTP_GET, .handler = index_handler};
	httpd_register_uri_handler(server, &index_uri);

	httpd_uri_t calib_uri = {.uri = "/api/calib", .method = HTTP_GET, .handler = calib_get_handler};
	httpd_register_uri_handler(server, &calib_uri);

	httpd_uri_t path_get_uri = {.uri = "/api/path", .method = HTTP_GET, .handler = path_get_handler};
	httpd_register_uri_handler(server, &path_get_uri);

	httpd_uri_t path_post_uri = {.uri = "/api/path", .method = HTTP_POST, .handler = path_post_handler};
	httpd_register_uri_handler(server, &path_post_uri);

	httpd_uri_t ws_uri = {
	    .uri = "/ws",
	    .method = HTTP_GET,
	    .handler = ws_handler,
	    .is_websocket = true,
	    .handle_ws_control_frames = true,
	};
	httpd_register_uri_handler(server, &ws_uri);
}

static void register_provision_uris(httpd_handle_t server)
{
	httpd_uri_t setup_uri = {.uri = "/", .method = HTTP_GET, .handler = setup_handler};
	httpd_register_uri_handler(server, &setup_uri);

	httpd_uri_t api_uri = {.uri = "/api/wifi", .method = HTTP_POST, .handler = wifi_save_handler};
	httpd_register_uri_handler(server, &api_uri);

	const char *captive_paths[] = {
	    "/generate_204", "/gen_204", "/hotspot-detect.html",
	    "/connecttest.txt", "/redirect", "/ncsi.txt", "/fwlink",
	};
	for (size_t i = 0; i < sizeof(captive_paths) / sizeof(captive_paths[0]); ++i)
	{
		httpd_uri_t u = {
		    .uri = captive_paths[i],
		    .method = HTTP_GET,
		    .handler = captive_redirect_handler,
		};
		httpd_register_uri_handler(server, &u);
	}
}

static httpd_handle_t start_http_server(bool provision)
{
	httpd_config_t config = HTTPD_DEFAULT_CONFIG();
	config.max_uri_handlers = 16;
	config.stack_size = 8192;
	config.lru_purge_enable = true;

	if (httpd_start(&s_httpd, &config) != ESP_OK)
	{
		ESP_LOGE(TAG, "HTTP server start failed");
		return NULL;
	}

	if (provision) register_provision_uris(s_httpd);
	else register_common_control_uris(s_httpd);

	ESP_LOGI(TAG, "HTTP server on port %d (%s)", config.server_port, provision ? "provision" : "control");
	return s_httpd;
}

#if CONFIG_TANK_USE_HTTPS
static httpd_handle_t start_https_server(void)
{
	httpd_ssl_config_t conf = HTTPD_SSL_CONFIG_DEFAULT();
	conf.httpd.max_uri_handlers = 8;
	conf.httpd.stack_size = 10240;
	conf.httpd.lru_purge_enable = true;
	conf.port_secure = 443;
	conf.cacert_pem = certs_server_crt_start;
	conf.cacert_len = (size_t)(certs_server_crt_end - certs_server_crt_start);
	conf.prvtkey_pem = certs_server_key_start;
	conf.prvtkey_len = (size_t)(certs_server_key_end - certs_server_key_start);

	if (httpd_ssl_start(&s_httpd, &conf) != ESP_OK)
	{
		ESP_LOGE(TAG, "HTTPS server start failed");
		return NULL;
	}

	register_common_control_uris(s_httpd);
	ESP_LOGI(TAG, "HTTPS server on port 443");
	return s_httpd;
}

static void start_http_redirect_server(void)
{
	httpd_config_t config = HTTPD_DEFAULT_CONFIG();
	config.server_port = 80;
	config.max_uri_handlers = 4;
	config.stack_size = 4096;

	if (httpd_start(&s_http_redirect, &config) != ESP_OK) return;

	httpd_uri_t root = {.uri = "/", .method = HTTP_GET, .handler = https_redirect_handler};
	httpd_uri_t ws = {.uri = "/ws", .method = HTTP_GET, .handler = https_redirect_handler};
	httpd_register_uri_handler(s_http_redirect, &root);
	httpd_register_uri_handler(s_http_redirect, &ws);

	ESP_LOGI(TAG, "HTTP:80 redirects to HTTPS");
}
#endif

static esp_err_t start_mdns(bool https)
{
	ESP_ERROR_CHECK(mdns_init());
	ESP_ERROR_CHECK(mdns_hostname_set(CONFIG_TANK_MDNS_HOSTNAME));
	ESP_ERROR_CHECK(mdns_instance_name_set("ESP32 Tank"));

	mdns_txt_item_t txt = {.key = "path", .value = "/"};
	if (https)
	{
		ESP_ERROR_CHECK(mdns_service_add(NULL, "_https", "_tcp", 443, &txt, 1));
		ESP_LOGI(TAG, "mDNS: https://%s.local", CONFIG_TANK_MDNS_HOSTNAME);
	}
	else
	{
		ESP_ERROR_CHECK(mdns_service_add(NULL, "_http", "_tcp", 80, &txt, 1));
		ESP_LOGI(TAG, "mDNS: http://%s.local (provision)", CONFIG_TANK_MDNS_HOSTNAME);
	}
	return ESP_OK;
}

/* ---------- Captive DNS (all queries -> AP IP) ---------- */

static void dns_server_task(void *arg)
{
	(void)arg;
	int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
	if (sock < 0)
	{
		ESP_LOGE(TAG, "DNS socket failed");
		vTaskDelete(NULL);
		return;
	}

	struct sockaddr_in addr = {
	    .sin_family = AF_INET,
	    .sin_port = htons(DNS_PORT),
	    .sin_addr.s_addr = htonl(INADDR_ANY),
	};
	if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0)
	{
		close(sock);
		ESP_LOGE(TAG, "DNS bind failed");
		vTaskDelete(NULL);
		return;
	}

	uint8_t rx[256];
	uint8_t tx[256];

	while (s_provisioning)
	{
		struct sockaddr_in source;
		socklen_t slen = sizeof(source);
		int len = recvfrom(sock, rx, sizeof(rx), 0, (struct sockaddr *)&source, &slen);
		if (len <= 12) continue;

		memcpy(tx, rx, (size_t)len);
		tx[2] = 0x81;
		tx[3] = 0x80;

		uint16_t qd = (uint16_t)((rx[4] << 8) | rx[5]);
		uint16_t an = qd;
		tx[6] = (uint8_t)(an >> 8);
		tx[7] = (uint8_t)(an & 0xff);

		int pos = 12;
		while (pos < len && rx[pos] != 0) pos += rx[pos] + 1;
		pos += 5;

		for (uint16_t i = 0; i < an && pos + 16 <= (int)sizeof(tx); ++i)
		{
			tx[pos++] = 0xc0;
			tx[pos++] = 0x0c;
			tx[pos++] = 0x00;
			tx[pos++] = 0x01;
			tx[pos++] = 0x00;
			tx[pos++] = 0x01;
			tx[pos++] = 0x00;
			tx[pos++] = 0x00;
			tx[pos++] = 0x00;
			tx[pos++] = 0x3c;
			tx[pos++] = 0x00;
			tx[pos++] = 0x04;
			tx[pos++] = 192;
			tx[pos++] = 168;
			tx[pos++] = 4;
			tx[pos++] = 1;
		}

		sendto(sock, tx, (size_t)pos, 0, (struct sockaddr *)&source, slen);
	}

	close(sock);
	s_dns_task = NULL;
	vTaskDelete(NULL);
}

static void start_captive_dns(void)
{
	if (s_dns_task) return;
	xTaskCreate(dns_server_task, "dns_srv", 3072, NULL, 5, &s_dns_task);
}

/* ---------- WiFi events ---------- */

static void on_got_ip(void *arg, esp_event_base_t base, int32_t id, void *data)
{
	(void)arg;
	(void)base;
	(void)id;

	ip_event_got_ip_t *event = (ip_event_got_ip_t *)data;
	ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));

	xEventGroupSetBits(s_wifi_events, WIFI_CONNECTED_BIT);

	if (s_connecting_from_portal)
	{
		return;
	}

	s_wifi_retry = 0;
	s_provisioning = false;
	s_wifi_connected = true;

	if (s_httpd == NULL)
	{
#if CONFIG_TANK_USE_HTTPS
		start_https_server();
		start_http_redirect_server();
		start_mdns(true);
#else
		start_http_server(false);
		start_mdns(false);
#endif
		ensure_watchdog_task();
	}
}

static void on_wifi_event(void *arg, esp_event_base_t base, int32_t id, void *data)
{
	(void)arg;
	(void)base;
	(void)data;

	if (id == WIFI_EVENT_STA_START)
	{
		esp_wifi_connect();
	}
	else if (id == WIFI_EVENT_STA_DISCONNECTED)
	{
		if (!s_provisioning && !s_connecting_from_portal)
		{
			s_wifi_connected = false;
		}

		if (s_provisioning && !s_connecting_from_portal) return;

		if (s_wifi_retry < WIFI_MAX_RETRY)
		{
			esp_wifi_connect();
			s_wifi_retry++;
			ESP_LOGW(TAG, "WiFi retry %d/%d", s_wifi_retry, WIFI_MAX_RETRY);
		}
		else
		{
			xEventGroupSetBits(s_wifi_events, WIFI_FAIL_BIT);
		}
	}
}

static esp_err_t wifi_stack_init_once(void)
{
	if (s_wifi_stack_ready) return ESP_OK;

	s_wifi_events = xEventGroupCreate();
	ESP_ERROR_CHECK(esp_netif_init());
	ESP_ERROR_CHECK(esp_event_loop_create_default());

	wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
	ESP_ERROR_CHECK(esp_wifi_init(&cfg));
	ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &on_wifi_event, NULL, NULL));
	ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &on_got_ip, NULL, NULL));

	s_wifi_stack_ready = true;
	return ESP_OK;
}

static esp_err_t try_connect_sta(const char *ssid, const char *pass, uint32_t timeout_ms)
{
	xEventGroupClearBits(s_wifi_events, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT);
	s_wifi_retry = 0;
	s_provisioning = false;

	esp_netif_create_default_wifi_sta();
	wifi_config_t wifi_config = {0};
	strncpy((char *)wifi_config.sta.ssid, ssid, sizeof(wifi_config.sta.ssid) - 1);
	strncpy((char *)wifi_config.sta.password, pass ? pass : "", sizeof(wifi_config.sta.password) - 1);
	wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

	ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
	ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
	ESP_ERROR_CHECK(esp_wifi_start());

	ESP_LOGI(TAG, "Connecting STA -> %s (press BOOT to enter provisioning)", ssid);

	uint32_t waited_ms = 0;
	while (waited_ms < timeout_ms)
	{
		if (boot_button_pressed())
		{
			boot_button_wait_release();
			ESP_LOGI(TAG, "BOOT pressed during connect, switching to provisioning");
			esp_wifi_stop();
			return ESP_ERR_INVALID_STATE;
		}

		EventBits_t bits = xEventGroupWaitBits(s_wifi_events,
		                                       WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
		                                       pdFALSE, pdFALSE,
		                                       pdMS_TO_TICKS(50));
		waited_ms += 50;
		if (bits & WIFI_CONNECTED_BIT) return ESP_OK;
		if (bits & WIFI_FAIL_BIT) break;
	}
	return ESP_FAIL;
}

static esp_err_t start_provisioning_ap(void)
{
	if (s_provisioning && s_httpd != NULL) return ESP_OK;

	stop_webservers();
	s_provisioning = true;
	s_wifi_connected = false;
	xEventGroupClearBits(s_wifi_events, WIFI_CONNECTED_BIT | WIFI_FAIL_BIT);

	ESP_ERROR_CHECK(esp_wifi_stop());
	esp_netif_create_default_wifi_ap();

	wifi_config_t ap_cfg = {0};
	strncpy((char *)ap_cfg.ap.ssid, CONFIG_TANK_AP_SSID, sizeof(ap_cfg.ap.ssid) - 1);
	ap_cfg.ap.ssid_len = (uint8_t)strlen(CONFIG_TANK_AP_SSID);
	ap_cfg.ap.channel = 1;
	ap_cfg.ap.max_connection = 4;
	ap_cfg.ap.beacon_interval = 100;

	if (strlen(CONFIG_TANK_AP_PASSWORD) >= 8)
	{
		strncpy((char *)ap_cfg.ap.password, CONFIG_TANK_AP_PASSWORD, sizeof(ap_cfg.ap.password) - 1);
		ap_cfg.ap.authmode = WIFI_AUTH_WPA2_PSK;
	}
	else
	{
		ap_cfg.ap.authmode = WIFI_AUTH_OPEN;
	}

	ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
	ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap_cfg));
	ESP_ERROR_CHECK(esp_wifi_start());

	start_captive_dns();
	start_http_server(true);
	start_mdns(false);

	ESP_LOGI(TAG, "Captive Portal: connect WiFi [%s], open http://" AP_IP_ADDR, CONFIG_TANK_AP_SSID);
	return ESP_OK;
}

static void watchdog_task(void *arg)
{
	(void)arg;
	const int timeout_ms = CONFIG_TANK_CMD_TIMEOUT_MS;

	while (1)
	{
		vTaskDelay(pdMS_TO_TICKS(100));
		if (s_provisioning) continue;

		int64_t last_us;
		portENTER_CRITICAL(&s_cmd_lock);
		last_us = s_last_cmd_us;
		portEXIT_CRITICAL(&s_cmd_lock);

		if (last_us == 0) continue;

		if ((esp_timer_get_time() - last_us) / 1000 > timeout_ms)
		{
			apply_stop();
			portENTER_CRITICAL(&s_cmd_lock);
			s_last_cmd_us = 0;
			portEXIT_CRITICAL(&s_cmd_lock);
		}
	}
}

/* ---------- public API ---------- */

esp_err_t wifi_web_control_start(TankControl *ctrl, DualMotor *motors)
{
	if (!ctrl || !motors) return ESP_ERR_INVALID_ARG;

	s_ctrl = ctrl;
	s_motors = motors;

	esp_err_t ret = nvs_flash_init();
	if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
	{
		ESP_ERROR_CHECK(nvs_flash_erase());
		ret = nvs_flash_init();
	}
	ESP_ERROR_CHECK(ret);
	nvs_load_motor_calib();
	nvs_load_path();
	ESP_ERROR_CHECK(wifi_stack_init_once());

	char ssid[33] = {0};
	char pass[65] = {0};
	bool from_nvs = nvs_load_wifi(ssid, sizeof(ssid), pass, sizeof(pass));
	bool have_creds = from_nvs;

	if (!have_creds && kconfig_has_fallback_wifi())
	{
		strncpy(ssid, CONFIG_TANK_WIFI_SSID, sizeof(ssid) - 1);
		strncpy(pass, CONFIG_TANK_WIFI_PASSWORD, sizeof(pass) - 1);
		have_creds = true;
	}

	if (have_creds && try_connect_sta(ssid, pass, 30000) == ESP_OK)
	{
		if (!from_nvs)
		{
			nvs_save_wifi(ssid, pass);
		}
		ensure_watchdog_task();
#if CONFIG_TANK_USE_HTTPS
		ESP_LOGI(TAG, "Ready: https://%s.local (accept self-signed cert)", CONFIG_TANK_MDNS_HOSTNAME);
#else
		ESP_LOGI(TAG, "Ready: http://%s.local", CONFIG_TANK_MDNS_HOSTNAME);
#endif
		return ESP_OK;
	}

	ESP_LOGW(TAG, "Starting Captive Portal");
	ESP_ERROR_CHECK(start_provisioning_ap());
	return ESP_OK;
}

void wifi_web_control_set_boot_button(gpio_num_t gpio)
{
	s_boot_gpio = gpio;
}

esp_err_t wifi_web_control_enter_provisioning(void)
{
	if (s_provisioning) return ESP_OK;
	if (s_wifi_connected) return ESP_ERR_INVALID_STATE;

	ESP_LOGI(TAG, "Enter provisioning mode (BOOT key)");
	apply_stop();
	s_wifi_retry = WIFI_MAX_RETRY;
	ESP_ERROR_CHECK(start_provisioning_ap());
	return ESP_OK;
}

void wifi_web_control_set_speed_scale(int percent)
{
	if (percent < 10) percent = 10;
	if (percent > 100) percent = 100;
	s_speed_scale = percent;
	ESP_LOGI(TAG, "Speed scale %d%%", s_speed_scale);
}

int wifi_web_control_get_speed_scale(void)
{
	return s_speed_scale;
}

bool wifi_web_control_is_provisioning(void)
{
	return s_provisioning;
}

bool wifi_web_control_is_wifi_connected(void)
{
	return s_wifi_connected;
}
