#include "tank_control.h"
#include <math.h>

static int clampi(int v, int lo, int hi)
{
	if (v < lo) return lo;
	if (v > hi) return hi;
	return v;
}

void tank_control_init(TankControl *tc)
{
	tc->max_linear = 1.0f;
	tc->max_angular = 2.0f;
	tc->max_percent = 85; // leave headroom
	tc->deadzone_percent = 8;
	tc->ramp_percent_per_step = 8;
	tc->last_left_percent = 0;
	tc->last_right_percent = 0;
}

static int apply_deadzone(int p, int dead)
{
	if (p == 0) return 0;
	if (p > 0) return p + dead;
	return p - dead;
}

static int ramp_step(int target, int current, int step)
{
	if (target > current)
	{
		int n = current + step;
		return n > target ? target : n;
	}
	else if (target < current)
	{
		int n = current - step;
		return n < target ? target : n;
	}
	return current;
}

void tank_drive_linear_angular(TankControl *tc, DualMotor *drv, float linear, float angular)
{
	float l = fmaxf(-tc->max_linear, fminf(tc->max_linear, linear));
	float a = fmaxf(-tc->max_angular, fminf(tc->max_angular, angular));

	// differential: v_left = l - k*a, v_right = l + k*a
	float k = tc->max_linear / tc->max_angular;
	float v_left = l - k * a;
	float v_right = l + k * a;

	// normalize to [-1,1]
	float maxmag = fmaxf(fabsf(v_left), fabsf(v_right));
	if (maxmag > tc->max_linear && maxmag > 0.0f)
	{
		v_left /= maxmag / tc->max_linear;
		v_right /= maxmag / tc->max_linear;
	}

	int lp = (int)(v_left / tc->max_linear * tc->max_percent);
	int rp = (int)(v_right / tc->max_linear * tc->max_percent);

	tank_drive_percents(tc, drv, lp, rp);
}

void tank_drive_percents(TankControl *tc, DualMotor *drv, int left_percent, int right_percent)
{
	int tl = clampi(left_percent, -tc->max_percent, tc->max_percent);
	int tr = clampi(right_percent, -tc->max_percent, tc->max_percent);

	if (tl != 0) tl = apply_deadzone(tl, tc->deadzone_percent);
	if (tr != 0) tr = apply_deadzone(tr, tc->deadzone_percent);

	// ramp for smoothness
	tc->last_left_percent = ramp_step(tl, tc->last_left_percent, tc->ramp_percent_per_step);
	tc->last_right_percent = ramp_step(tr, tc->last_right_percent, tc->ramp_percent_per_step);

	motor_set_left_percent(drv, tc->last_left_percent);
	motor_set_right_percent(drv, tc->last_right_percent);
}

void tank_stop(TankControl *tc, DualMotor *drv)
{
	tc->last_left_percent = 0;
	tc->last_right_percent = 0;
	motor_stop(drv);
}

