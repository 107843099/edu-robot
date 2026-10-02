#ifndef __OLED_DATA_H
#define __OLED_DATA_H

#include <stdint.h>

/*中文字符字节宽度*/
#define OLED_CHN_CHAR_WIDTH			2		//UTF-8编码格式给3，GB2312编码格式给2

/*字模基本单元*/
typedef struct 
{
	char Index[OLED_CHN_CHAR_WIDTH + 1];	//汉字索引
	uint8_t Data[32];						//字模数据
} ChineseCell_t;

/*ASCII字模数据声明*/
extern const uint8_t OLED_F8x16[][16];
extern const uint8_t OLED_F6x8[][6];

/*汉字字模数据声明*/
extern const ChineseCell_t OLED_CF16x16[];

/*图像数据声明*/
extern const uint8_t Diode[];
extern const uint8_t huaji[];
extern const uint8_t BMP1[];//立正脸
extern const uint8_t BMP2[];//前进脸
extern const uint8_t BMP3[];//右转脸
extern const uint8_t BMP4[];//左转脸
extern const uint8_t BMP5[];//特殊脸（嘿嘿脸）
extern const uint8_t BMP6[];//睡觉脸（普通）
extern const uint8_t BMP7[];//love花痴脸
extern const uint8_t BMP8[];//酣睡脸（流口水）
extern const uint8_t BMP9[];//开心脸
extern const uint8_t BMP10[];//调皮脸
extern const uint8_t BMP11[];//迷糊脸（开心得迷糊）
extern const uint8_t BMP12[];//猫猫脸
/*按照上面的格式，在这个位置加入新的图像数据声明*/
//...

extern const uint8_t BMPx1[];		//开心
extern const uint8_t BMPx2[];		//震惊
extern const uint8_t BMPx3[];		//wink
extern const uint8_t BMPx4[];		//安逸
extern const uint8_t BMPx5[];		//比耶
extern const uint8_t BMPx6[];		//呆呆
extern const uint8_t BMPx7[];		//得意
extern const uint8_t BMPx8[];		//愤怒
extern const uint8_t BMPx9[];		//搞怪
extern const uint8_t BMPx10[];		//坏笑
extern const uint8_t BMPx11[];		//灰心
extern const uint8_t BMPx12[];		//哭
extern const uint8_t BMPx13[];		//无语
extern const uint8_t BMPx14[];		//晕
extern const uint8_t BMPx15[];		//震惊

extern const uint8_t wink1[];
extern const uint8_t wink2[];
extern const uint8_t wink3[];
extern const uint8_t wink4[];
extern const uint8_t wink5[];
extern const uint8_t wink6[];
extern const uint8_t wink7[];
extern const uint8_t wink8[];
extern const uint8_t wink9[];
extern const uint8_t wink10[];
extern const uint8_t wink11[];


extern const uint8_t *winks[];












#endif


/*****************江协科技|版权所有****************/
/*****************jiangxiekeji.com*****************/
