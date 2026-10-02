#include "stm32f10x.h"                  // Device header
#include "stdlib.h"
#include <stdio.h>
#include "LED.h"
#include "Delay.h"
#include "OLED.h"
#include "Servo.h"
#include "PWM.h"
#include "Movement.h"
#include "usart1.h"
#include "usart2.h"
#include "Mode.h"

/****************************************************
*
*程序名称：电子桌面宠物“小呆”
*当前版本：V1.0-2024/6/9
*
*****************************************************
*/
/*
1.表情 	1
2.动作	
3.语音
*/


uint8_t RxData;					//用于接收串口数据的变量
uint8_t move_mode1 = '0';		//用于接收蓝牙串口数据的变量
uint8_t move_mode2 = '0';		//用于接收语音识别串口数据的变量
uint8_t move_mode = '0';		//决定状态变量
uint8_t previous_mode = '0';	//用于保存上一次接收串口数据的变量


uint16_t Time; //记录时间



int main(void)
{
	/*模块初始化*/
	LED_Init();									//LED初始化
	OLED_Init();								//OLED初始化
	USART1_Init();								//蓝牙串口初始化
	USART2_Init();								//语音合成串口初始化
	Servo_Init();								//舵机初始化
	mode_stand();								//站立状态
	/*初始化状态*/
	OLED_Clear();
	OLED_ShowImage(0, 0, 128, 64, BMP2); 		
	
	USART1_Printf("hello man bo dog\r\n");		//串口打印日志
	
	while (1)
	{  
		if (USART1_GetRxFlag()) 				//设置蓝牙接收优先级大于语音识别
		{	
			move_mode = USART1_GetRxData();		//获取蓝牙串口接收的数据			
			USART1_Printf("uart1_command:c:%c\r\n",move_mode);
		}
		else if (USART2_GetRxFlag()){
			move_mode = USART2_GetRxData();		//获取语音识别串口接收的数据
			USART1_Printf("uart2_command:c:%c\r\n",move_mode);
		}
		int random_index = rand() % 2;
		//***互动设置***//
		switch (move_mode) {
			case 'f': //前进
				mode_forward();
				break;
			case 'b': //后退
				mode_behind();
				break;
			case 'l': //左转
				mode_left();
				break;
			case 'r': //右转
				mode_right();
				break;
			case 'w': //前后摇摆
				mode_swing_qianhou();
				break;
			case 'z': //左右摇摆
				mode_swing_zuoyou();
				break;
			case 'd': //跳舞
				if(random_index) 	mode_dance();
				else 				mode_biaobai();
				break;
			case '5': //立正
				mode_stand();
				break;
			case 'q': //起身
				if (previous_mode != '0') {
					mode_slowstand();
				}
				break;
			case 's': //坐下
				if (previous_mode != 's') {
					mode_strech();
				}
				break;
			case 'j': //交替抬手
				mode_twohands();
				break;
			case 'y': //伸懒腰
				mode_lanyao();
				break;
			case '1': //抬头
				mode_headup();
				break;
			case 'p': //趴下睡觉
				if (previous_mode != 'p') {
					mode_sleeppa();
				}
				break;
			case '2': //卧下睡觉
				if (previous_mode != '2') {
					mode_sleepwo();
				}
				break;
			case 'B': //表白
				mode_biaobai();
				break;
			case 'o': //打招呼
				mode_hello();
				break;
			case 'K': //开心
				mode_biaobai();
				break;
			case 'R':
				random_dis_expression_s();//随机切换表情
				break;
			case 'Q':
				reverse_OLED();//随机切换表情
				break;
			case 'W':
				do_wink();//随机切换表情
				break;
		}
		

	}
}


