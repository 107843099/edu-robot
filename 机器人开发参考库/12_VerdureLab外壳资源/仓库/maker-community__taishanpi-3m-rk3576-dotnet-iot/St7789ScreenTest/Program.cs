using System.Device.Gpio;
using System.Device.Gpio.Drivers;
using System.Device.Spi;
using St7789ScreenTest;

var options = TestOptions.Parse(args);

Console.WriteLine("ST7789 2.4 inch screen test for TaishanPi 3M / RK3576");
Console.WriteLine($"SPI: bus={options.SpiBus}, chip-select={options.SpiChipSelect}, clock={options.ClockFrequency:N0} Hz, mode=0");
Console.WriteLine($"GPIO: gpiochip={options.GpioChip}, dc-line={options.DcLine}, reset-line={options.ResetLine}, cs-line={options.CsLine}, backlight-line={options.BacklightLine}");

using var gpio = new GpioController(new LibGpiodV2Driver(options.GpioChip));

if (options.BacklightLine >= 0)
{
    gpio.OpenPin(options.BacklightLine, PinMode.Output);
    gpio.Write(options.BacklightLine, PinValue.High);
    Console.WriteLine("Backlight line set High.");
}

var spiSettings = new SpiConnectionSettings(options.SpiBus, options.SpiChipSelect)
{
    ClockFrequency = options.ClockFrequency,
    Mode = SpiMode.Mode0
};

using var display = new ST7789Display(spiSettings, gpio, options.DcLine, options.ResetLine, options.CsLine, useReset: !options.NoReset);

Console.WriteLine("Display initialized. Starting patterns...");
RunPatterns(display, options.DelayMs, options.Loops);
Console.WriteLine("Screen test completed.");

static void RunPatterns(ST7789Display display, int delayMs, int loops)
{
    int currentLoop = 0;
    while (loops < 0 || currentLoop < loops)
    {
        ShowColor(display, "Red", 0xF800, delayMs);
        ShowColor(display, "Green", 0x07E0, delayMs);
        ShowColor(display, "Blue", 0x001F, delayMs);
        ShowColor(display, "White", 0xFFFF, delayMs);
        ShowColor(display, "Black", 0x0000, delayMs);

        Console.WriteLine("Pattern: vertical color bars");
        display.DrawRgb565(Patterns.ColorBars(display.Width, display.Height));
        Thread.Sleep(delayMs);

        Console.WriteLine("Pattern: gradient");
        display.DrawRgb565(Patterns.Gradient(display.Width, display.Height));
        Thread.Sleep(delayMs);

        Console.WriteLine("Pattern: checkerboard");
        display.DrawRgb565(Patterns.Checkerboard(display.Width, display.Height, 20));
        Thread.Sleep(delayMs);

        currentLoop++;
    }
}

static void ShowColor(ST7789Display display, string name, ushort color, int delayMs)
{
    Console.WriteLine($"Pattern: {name}");
    display.FillScreen(color);
    Thread.Sleep(delayMs);
}

internal sealed record TestOptions(
    int SpiBus,
    int SpiChipSelect,
    int ClockFrequency,
    int GpioChip,
    int DcLine,
    int ResetLine,
    int CsLine,
    int BacklightLine,
    bool NoReset,
    int DelayMs,
    int Loops)
{
    public static TestOptions Parse(string[] args)
    {
        var options = new TestOptions(
            SpiBus: 1,
            SpiChipSelect: 0,
            ClockFrequency: 24_000_000,
            GpioChip: 2,
            DcLine: 30,
            ResetLine: 22,
            CsLine: -1,
            BacklightLine: -1,
            NoReset: false,
            DelayMs: 1000,
            Loops: 1);

        for (int index = 0; index < args.Length; index++)
        {
            string arg = args[index];
            string value = index + 1 < args.Length ? args[index + 1] : string.Empty;

            options = arg switch
            {
                "--spi-bus" => options with { SpiBus = ReadInt(arg, value, ref index) },
                "--spi-cs" => options with { SpiChipSelect = ReadInt(arg, value, ref index) },
                "--clock" => options with { ClockFrequency = ReadInt(arg, value, ref index) },
                "--gpiochip" => options with { GpioChip = ReadInt(arg, value, ref index) },
                "--dc" => options with { DcLine = ReadInt(arg, value, ref index) },
                "--reset" => options with { ResetLine = ReadInt(arg, value, ref index) },
                "--cs-line" => options with { CsLine = ReadInt(arg, value, ref index) },
                "--backlight-line" => options with { BacklightLine = ReadInt(arg, value, ref index) },
                "--delay" => options with { DelayMs = ReadInt(arg, value, ref index) },
                "--loops" => options with { Loops = ReadInt(arg, value, ref index) },
                "--no-reset" => options with { NoReset = true },
                "--help" or "-h" => PrintHelpAndExit(),
                _ => throw new ArgumentException($"Unknown argument: {arg}")
            };
        }

        return options;
    }

    private static int ReadInt(string name, string value, ref int index)
    {
        if (!int.TryParse(value, out int result))
        {
            throw new ArgumentException($"{name} requires an integer value.");
        }

        index++;
        return result;
    }

    private static TestOptions PrintHelpAndExit()
    {
        Console.WriteLine("Usage: sudo dotnet run -- [options]");
        Console.WriteLine("Defaults target TaishanPi 3M SPI1_M1 + Raspberry Pi-style ST7789 2.4 inch wiring:");
        Console.WriteLine("  --spi-bus 1 --spi-cs 0 --clock 24000000 --gpiochip 2 --dc 30 --reset 22 --cs-line -1");
        Console.WriteLine("Other options: --backlight-line <line>, --no-reset, --delay 1000, --loops 1, use --loops -1 for endless loop.");
        Environment.Exit(0);
        throw new UnreachableException();
    }
}

internal static class Patterns
{
    public static byte[] ColorBars(int width, int height)
    {
        ushort[] colors =
        {
            0xF800,
            0xFFE0,
            0x07E0,
            0x07FF,
            0x001F,
            0xF81F,
            0xFFFF,
            0x0000
        };

        byte[] buffer = new byte[width * height * 2];
        for (int y = 0; y < height; y++)
        {
            for (int x = 0; x < width; x++)
            {
                int bar = x * colors.Length / width;
                WriteRgb565(buffer, x, y, width, colors[bar]);
            }
        }

        return buffer;
    }

    public static byte[] Gradient(int width, int height)
    {
        byte[] buffer = new byte[width * height * 2];
        for (int y = 0; y < height; y++)
        {
            for (int x = 0; x < width; x++)
            {
                byte red = (byte)(x * 255 / Math.Max(width - 1, 1));
                byte green = (byte)(y * 255 / Math.Max(height - 1, 1));
                byte blue = (byte)((x + y) * 255 / Math.Max(width + height - 2, 1));
                WriteRgb565(buffer, x, y, width, ToRgb565(red, green, blue));
            }
        }

        return buffer;
    }

    public static byte[] Checkerboard(int width, int height, int cellSize)
    {
        byte[] buffer = new byte[width * height * 2];
        for (int y = 0; y < height; y++)
        {
            for (int x = 0; x < width; x++)
            {
                bool light = ((x / cellSize) + (y / cellSize)) % 2 == 0;
                WriteRgb565(buffer, x, y, width, light ? (ushort)0xFFFF : (ushort)0x0000);
            }
        }

        return buffer;
    }

    private static ushort ToRgb565(byte red, byte green, byte blue)
    {
        return (ushort)(((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3));
    }

    private static void WriteRgb565(byte[] buffer, int x, int y, int width, ushort color)
    {
        int offset = ((y * width) + x) * 2;
        buffer[offset] = (byte)(color >> 8);
        buffer[offset + 1] = (byte)(color & 0xFF);
    }
}

internal sealed class UnreachableException : Exception
{
}
