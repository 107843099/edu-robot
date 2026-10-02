#include "stm32f10x.h"                  // Device header
#include "stdlib.h"
#include "LED.h"
#include "Delay.h"
#include "OLED.h"
#include "Servo.h"
#include "PWM.h"
#include "Movement.h"
#include "usart1.h"
#include "usart2.h"
#include "usart3.h"
#include "syn6288.h"
#include "stdio.h"
#include "Mode.h"

#define STEP_    5

extern uint8_t move_mode ;			//决定状态变量
extern uint8_t previous_mode ;		//用于保存上一次接收串口数据的变量

uint8_t dis_flag = 1;



uint8_t step_num = STEP_;			//动作循环次数

void mode_forward(void)//前进
{
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_forward();
		LED13_Turn();				//翻转电平状态，由1变为0，灯由灭变亮
		previous_mode = move_mode;
		step_num --;
		USART1_Printf("step:%d\r\n",step_num);		//串口打印日志
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}
}
void mode_behind(void)//后退
{
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_behind();
		LED13_Turn();
		OLED_Reverse();
		OLED_Update();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}
}
void mode_left(void)//左转
{
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_left();
		LED13_Turn();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}
}
void mode_right(void)//右转
{
	
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_right();
		LED13_Turn();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}

}

void mode_swing_qianhou(void)//前后摇摆
{
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_shake_qianhou();
		LED13_Turn();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}


}
void mode_swing_zuoyou(void)//左右摇摆
{
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_shake_zuoyou();
		LED13_Turn();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}
}

void mode_dance(void)//跳舞
{
	if(step_num != 0)
	{
		if(dis_flag)				//每次指令只切换一次表情
		{
			random_dis_expression();
			dis_flag = 0;
		}
		move_dance();
		LED13_Turn();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = STEP_;
		dis_flag = 1;
	}
}

void mode_stand(void)//立正
{
	OLED_ShowImage(0, 0, 128, 64, BMPx6); //立正脸
	move_stand();
	LED13_Turn();
	previous_mode = move_mode;
	move_mode = '0';
}
void mode_slowstand(void)//起身
{
	random_dis_expression();
	move_slow_stand(previous_mode);
	LED13_Turn();
	previous_mode = move_mode;
	move_mode = '0';
}

void mode_strech(void)//坐下擦脸
{
	OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
	move_slow_stand(previous_mode);
	OLED_ShowImage(0, 0, 128, 64, BMP2);//前进脸
	move_stretch();
	OLED_ShowImage(0, 0, 128, 64, BMP12);//猫猫脸
	LED13_Turn();
	previous_mode = move_mode;
	move_mode = '0';
}
void mode_hello(void)//打招呼
{
	int i;
	if (previous_mode != '5' && previous_mode != 'D') 
	{
		OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
		move_slow_stand(previous_mode);
	}
	OLED_ShowImage(0, 0, 128, 64, BMP12);//猫猫脸

	for(i=0;i<20;i++)//
	{
		Servo_SetAngle1(90-i);
		Servo_SetAngle2(90+i);
		//Servo_SetAngle3(90+i);
		Servo_SetAngle4(90-i);
		Delay_ms(7);
	}
	for(i=0;i<40;i++)//
	{
		Servo_SetAngle2(110+i);
		Servo_SetAngle4(70-i);
		Delay_ms(7);
	}
	for(i=0;i<60;i++)//右前足缓慢抬起
	{
		Servo_SetAngle1(70+i);
		Delay_ms(4);
	}
	Delay_ms(50);
	//下面是摇五次次右前足
	for(int j = 0;j<5;j++)
	{
		for(int i = 0;i < 10;i++)
		{
			Servo_SetAngle1(180-i*5);
			Delay_ms(40);
		}
		for(int i = 0;i < 10;i++)
		{
			Servo_SetAngle1(130+i*5);
			Delay_ms(40);
		}
	}
	Servo_SetAngle1(70);
	Delay_ms(500);
	LED13_Turn();
	previous_mode = move_mode;
	move_mode = '0';

}
void mode_twohands(void)//交替抬手
{
	OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
	move_stand();
	move_two_hands();
	LED13_Turn();
	previous_mode = move_mode;
	move_mode = '0';
}
void mode_lanyao(void)//懒腰
{
	OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
	move_slow_stand(previous_mode);
	OLED_ShowImage(0, 0, 128, 64, BMP9);//开心脸
	lan_yao();
	OLED_ShowImage(0, 0, 128, 64, BMP1);//立正脸
	LED13_Turn();
	previous_mode = move_mode;
	move_mode = '0';
}
void mode_headup(void)//抬头
{
	if(step_num != 0)
	{
		OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
		move_slow_stand(previous_mode);
		OLED_ShowImage(0, 0, 128, 64, BMP10);//调皮脸
		move_head_up();
		LED13_Turn();
		previous_mode = move_mode;
		step_num --;
	}else
	{
		move_mode = '5';			//步数为0则切换为立正动作
		step_num = 5;
	}

}
void mode_sleeppa(void)//趴下睡觉
{
	if (previous_mode != '5' && previous_mode != 'q') {
		OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
		move_slow_stand(previous_mode);
	}
	if (rand()%2) {//随机产生两种表情中的一种
		OLED_ShowImage(0, 0, 128, 64, BMP6); //普通睡觉脸
	}
	else{
		OLED_ShowImage(0, 0, 128, 64, BMP8); //酣睡脸
	}
	move_sleep_p();
	previous_mode = move_mode;
	move_mode = '0';
}
void mode_sleepwo(void)//卧下睡觉
{
	if (previous_mode != '5' && previous_mode != 'q') {
		OLED_ShowImage(0, 0, 128, 64, BMP1); //立正脸
		move_slow_stand(previous_mode);
		Delay_s(1);
	}
	if (rand()%2) {//随机产生两种表情中的一种
		OLED_ShowImage(0, 0, 128, 64, BMP6); //普通睡觉脸
	}
	else{
		OLED_ShowImage(0, 0, 128, 64 , BMP8); //酣睡脸
	}
	move_sleep_w();
	previous_mode = move_mode;
	move_mode = '0';
}

void mode_biaobai(void)//表白
{
	OLED_ShowImage(0, 0, 128, 64, BMP7); //love花痴脸	
	Servo_SetAngle1(135);//抬起右前脚
	OLED_ShowImage(0, 0, 128, 64, BMP11); //开心迷糊脸	
	Servo_SetAngle3(45);//抬起左前脚
	Servo_SetAngle1(90);//
	Servo_SetAngle3(90);//收回两只前脚
	OLED_ShowImage(0, 0, 128, 64, BMP9); //开心脸	
	OLED_ShowImage(0, 0, 128, 64, BMP7); //love花痴脸
	move_shake_qianhou();
	move_shake_qianhou();
	Delay_s(5);
	previous_mode = move_mode;
	move_mode = '0';

}

void do_wink(void)
{
	move_stand();

	OLED_ShowImage(0, 0, 128, 64, winks[0]); 
	Delay_s(5);
	OLED_ShowImage(0, 0, 128, 64, BMPx3); 
	Delay_s(1);
	OLED_ShowImage(0, 0, 128, 64, winks[0]); 
	Delay_s(1);
	Servo_SetAngle2(135);//右后脚向后抬
	Servo_SetAngle4(45);//左后脚向后抬
	
	for(int i = 0 ;i<3;i++)
	{
		for(int i = 0 ;i<45;i++)
		{
			Servo_SetAngle1(90+i);//右后脚向后抬
			Servo_SetAngle3(90-i);//左后脚向后抬
			Delay_ms(5);
		}
		for(int i = 0 ;i<90;i++)
		{
			Servo_SetAngle1(135-i);//右后脚向后抬
			Servo_SetAngle3(45+i);//左后脚向后抬
			Delay_ms(5);
		}
		for(int i = 0 ;i<45;i++)
		{
			Servo_SetAngle1(45+i);//右后脚向后抬
			Servo_SetAngle3(135-i);//左后脚向后抬
			Delay_ms(5);
		}
	}
	previous_mode = move_mode;
	move_mode = '5';

}


void random_dis_expression(void)//随机显示一个表情
{
	// 生成一个随机数，范围在0到14之间（对应BMPx1到BMPx15）
	int random_index = rand() % 15; // 生成0到14之间的随机数

	// 使用随机索引选择对应的表情
	switch(random_index)
	{
		case 0: OLED_ShowImage(0, 0, 128, 64, BMPx1); break;
		case 1: OLED_ShowImage(0, 0, 128, 64, BMPx2); break;
		case 2: OLED_ShowImage(0, 0, 128, 64, BMPx3); break;
		case 3: OLED_ShowImage(0, 0, 128, 64, BMPx4); break;
		case 4: OLED_ShowImage(0, 0, 128, 64, BMPx5); break;
		case 5: OLED_ShowImage(0, 0, 128, 64, BMPx6); break;
		case 6: OLED_ShowImage(0, 0, 128, 64, BMPx7); break;
		case 7: OLED_ShowImage(0, 0, 128, 64, BMPx8); break;
		case 8: OLED_ShowImage(0, 0, 128, 64, BMPx9); break;
		case 9: OLED_ShowImage(0, 0, 128, 64, BMPx10); break;
		case 10: OLED_ShowImage(0, 0, 128, 64, BMPx11); break;
		case 11: OLED_ShowImage(0, 0, 128, 64, BMPx12); break;
		case 12: OLED_ShowImage(0, 0, 128, 64, BMPx13); break;
		case 13: OLED_ShowImage(0, 0, 128, 64, BMPx14); break;
		case 14: OLED_ShowImage(0, 0, 128, 64, BMPx15); break;
	}
}

void random_dis_expression_s(void)//随机显示一个表情
{
	int i = 0;
	while(i<25)//1秒的切换动画		
	{
		i++;
		// 生成一个随机数，范围在0到14之间（对应BMPx1到BMPx15）
		int random_index = rand() % 15; // 生成0到14之间的随机数

		// 使用随机索引选择对应的表情
		switch(random_index)
		{
			case 0: OLED_ShowImage(0, 0, 128, 64, BMPx1); break;
			case 1: OLED_ShowImage(0, 0, 128, 64, BMPx2); break;
			case 2: OLED_ShowImage(0, 0, 128, 64, BMPx3); break;
			case 3: OLED_ShowImage(0, 0, 128, 64, BMPx4); break;
			case 4: OLED_ShowImage(0, 0, 128, 64, BMPx5); break;
			case 5: OLED_ShowImage(0, 0, 128, 64, BMPx6); break;
			case 6: OLED_ShowImage(0, 0, 128, 64, BMPx7); break;
			case 7: OLED_ShowImage(0, 0, 128, 64, BMPx8); break;
			case 8: OLED_ShowImage(0, 0, 128, 64, BMPx9); break;
			case 9: OLED_ShowImage(0, 0, 128, 64, BMPx10); break;
			case 10: OLED_ShowImage(0, 0, 128, 64, BMPx11); break;
			case 11: OLED_ShowImage(0, 0, 128, 64, BMPx12); break;
			case 12: OLED_ShowImage(0, 0, 128, 64, BMPx13); break;
			case 13: OLED_ShowImage(0, 0, 128, 64, BMPx14); break;
			case 14: OLED_ShowImage(0, 0, 128, 64, BMPx15); break;
		}
		Delay_ms(1);
	}
	random_dis_expression();
	move_mode = '0';
}


void reverse_OLED(void)
{
	OLED_Reverse();
	OLED_Update();
	move_mode = '0';
}
