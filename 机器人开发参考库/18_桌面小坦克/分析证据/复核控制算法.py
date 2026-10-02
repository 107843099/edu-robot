"""Compile the unchanged vendor controller with a mock motor driver; no ESP32/USB access."""
from pathlib import Path
import tempfile,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
source=next(ROOT.glob('本地资料/**/main/tank_control.c'))
harness=r'''
#include "tank_control.h"
#include <assert.h>
#include <stdio.h>
void motor_set_left_percent(DualMotor *d,int p){d->left=p;}
void motor_set_right_percent(DualMotor *d,int p){d->right=p;}
void motor_stop(DualMotor *d){d->left=d->right=0;d->stops++;}
int main(void){TankControl t;DualMotor d={0};tank_control_init(&t);
 tank_drive_percents(&t,&d,85,85);assert(d.left==8&&d.right==8);puts("PASS first_call_ramp_8");
 for(int i=0;i<20;i++)tank_drive_percents(&t,&d,1000,1000);
 assert(d.left==93&&d.right==93);puts("PASS nominal_85_limit_becomes_93_after_deadzone");
 tank_stop(&t,&d);assert(d.left==0&&d.right==0&&t.last_left_percent==0&&d.stops==1);puts("PASS stop_resets_ramp_state");
 for(int i=0;i<20;i++)tank_drive_linear_angular(&t,&d,0,2);
 assert(d.left==-93&&d.right==93);puts("PASS in_place_rotation");tank_stop(&t,&d);
 for(int i=0;i<20;i++)tank_drive_linear_angular(&t,&d,1,2);
 assert(d.left==0&&d.right==93);puts("PASS differential_normalization");
 return 0;}
'''
with tempfile.TemporaryDirectory(prefix='tank-host-') as td:
 p=Path(td);(p/'tank_control.c').write_bytes(source.read_bytes());(p/'tank_control.h').write_bytes(source.with_suffix('.h').read_bytes())
 (p/'motor.h').write_text('#pragma once\ntypedef struct { int left,right,stops; } DualMotor;\nvoid motor_set_left_percent(DualMotor*,int);\nvoid motor_set_right_percent(DualMotor*,int);\nvoid motor_stop(DualMotor*);\n');(p/'check.c').write_text(harness)
 build=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','tank_control.c','check.c','-lm','-o','check'],cwd=p,capture_output=True,text=True)
 assert build.returncode==0,build.stderr
 run=subprocess.run([str(p/'check')],capture_output=True,text=True);assert run.returncode==0,run.stderr
 report={'date':'2026-10-03','scope':'Unchanged vendor tank_control.c compiled for host using a mock motor driver. Does not compile the full ESP-IDF firmware or validate watchdog timing, WiFi, PWM, current, motion or hardware.','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'compile_exit_code':build.returncode,'run_exit_code':run.returncode,'checks':run.stdout.splitlines(),'hardware_test':False}
 (ROOT/'分析证据/控制算法主机复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
