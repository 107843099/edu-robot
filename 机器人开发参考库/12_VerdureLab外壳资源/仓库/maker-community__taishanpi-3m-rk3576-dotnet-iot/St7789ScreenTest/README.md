# ST7789 2.4 Inch Screen Test

This project is a TaishanPi 3M / RK3576 adaptation of the `DualDisplayExample` 2.4 inch display path from `GreenShadeZhang/dotnet-iot-tutorial-code`.

Defaults match Raspberry Pi-style physical wiring moved to TaishanPi SPI1_M1:

- SPI device: `/dev/spidev1.0`
- SPI bus/chip-select: `1,0`
- SPI mode: `Mode0`
- SPI clock: `24 MHz`
- GPIO driver: `LibGpiodV2Driver(2)`
- DC: `gpiochip2 line 30`, physical pin 22, `GPIO2_D6`
- RESET: `gpiochip2 line 22`, physical pin 13, `GPIO2_C6`
- CS: hardware CS0 on physical pin 24, app `cs-line = -1`

Raspberry Pi mapping used by the upstream sample:

| Signal | Raspberry Pi BCM | Physical pin | TaishanPi mapping |
|---|---:|---:|---|
| DC | GPIO25 | 22 | `gpiochip2 line 30` |
| RESET | GPIO27 | 13 | `gpiochip2 line 22` |
| CS0 | GPIO8 / CE0 | 24 | SPI1 CS0 `/dev/spidev1.0` |
| MOSI | GPIO10 | 19 | SPI1 MOSI |
| MISO | GPIO9 | 21 | SPI1 MISO, optional |
| SCLK | GPIO11 | 23 | SPI1 CLK |

Run on the board:

```bash
cd St7789ScreenTest
sudo dotnet run
```

Useful options:

```bash
sudo dotnet run -- --clock 6000000 --delay 1500
sudo dotnet run -- --loops -1
sudo dotnet run -- --spi-bus 1 --spi-cs 0 --gpiochip 2 --dc 30 --reset 22 --cs-line -1
```

If your backlight is wired to a GPIO line on the same gpiochip, add:

```bash
sudo dotnet run -- --backlight-line <line>
```

The app shows red, green, blue, white, black, color bars, gradient, and checkerboard patterns.
