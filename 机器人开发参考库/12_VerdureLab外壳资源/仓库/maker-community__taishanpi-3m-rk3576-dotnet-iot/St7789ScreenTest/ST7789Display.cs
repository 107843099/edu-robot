using System.Device.Gpio;
using System.Device.Spi;

namespace St7789ScreenTest;

public sealed class ST7789Display : IDisposable
{
    private const int MaxTransferSize = 4096;

    private readonly SpiDevice _spiDevice;
    private readonly GpioController _gpio;
    private readonly int _dcLine;
    private readonly int _resetLine;
    private readonly int _csLine;
    private bool _disposed;

    public int Width { get; } = 320;
    public int Height { get; } = 240;

    public ST7789Display(SpiConnectionSettings settings, GpioController gpio, int dcLine, int resetLine, int csLine = -1, bool useReset = true)
    {
        _spiDevice = SpiDevice.Create(settings);
        _gpio = gpio;
        _dcLine = dcLine;
        _resetLine = resetLine;
        _csLine = csLine;

        _gpio.OpenPin(_dcLine, PinMode.Output);

        if (useReset)
        {
            _gpio.OpenPin(_resetLine, PinMode.Output);
            Reset();
        }

        if (_csLine >= 0)
        {
            _gpio.OpenPin(_csLine, PinMode.Output);
            _gpio.Write(_csLine, PinValue.High);
        }

        Initialize24Inch();
    }

    public void Reset()
    {
        _gpio.Write(_resetLine, PinValue.High);
        Thread.Sleep(20);
        _gpio.Write(_resetLine, PinValue.Low);
        Thread.Sleep(20);
        _gpio.Write(_resetLine, PinValue.High);
        Thread.Sleep(150);
    }

    public void Initialize24Inch()
    {
        SendCommand(0x01);
        Thread.Sleep(150);

        WriteCommandData(0x36, 0x70);
        WriteCommandData(0x3A, 0x05);
        SendCommand(0x21);

        SendCommand(0x2A);
        SendData(0x00, 0x00, 0x01, 0x3F);

        SendCommand(0x2B);
        SendData(0x00, 0x00, 0x00, 0xEF);

        WriteCommandData(0xB2, 0x0C, 0x0C, 0x00, 0x33, 0x33);
        WriteCommandData(0xB7, 0x35);
        WriteCommandData(0xBB, 0x1F);
        WriteCommandData(0xC0, 0x2C);
        WriteCommandData(0xC2, 0x01);
        WriteCommandData(0xC3, 0x12);
        WriteCommandData(0xC4, 0x20);
        WriteCommandData(0xC6, 0x0F);
        WriteCommandData(0xD0, 0xA4, 0xA1);

        WriteCommandData(0xE0,
            0xD0, 0x08, 0x11, 0x08, 0x0C, 0x15, 0x39,
            0x33, 0x50, 0x36, 0x13, 0x14, 0x29, 0x2D);

        WriteCommandData(0xE1,
            0xD0, 0x08, 0x10, 0x08, 0x06, 0x06, 0x39,
            0x44, 0x51, 0x0B, 0x16, 0x14, 0x2F, 0x31);

        SendCommand(0x11);
        Thread.Sleep(120);

        SetAddressWindow(0, 0, Width, Height);

        SendCommand(0x29);
        Thread.Sleep(100);
    }

    public void SetAddressWindow(int x0, int y0, int x1, int y1)
    {
        SendCommand(0x2A);
        SendData((byte)(x0 >> 8));
        SendData((byte)(x0 & 0xFF));
        SendData((byte)(x1 >> 8));
        SendData((byte)((x1 - 1) & 0xFF));

        SendCommand(0x2B);
        SendData((byte)(y0 >> 8));
        SendData((byte)(y0 & 0xFF));
        SendData((byte)(y1 >> 8));
        SendData((byte)((y1 - 1) & 0xFF));

        SendCommand(0x2C);
    }

    public void FillScreen(ushort color)
    {
        SetAddressWindow(0, 0, Width, Height);

        byte high = (byte)(color >> 8);
        byte low = (byte)(color & 0xFF);
        byte[] buffer = new byte[Math.Min(Width * Height * 2, 32768)];

        for (int index = 0; index < buffer.Length; index += 2)
        {
            buffer[index] = high;
            buffer[index + 1] = low;
        }

        int totalBytes = Width * Height * 2;
        int bytesWritten = 0;
        while (bytesWritten < totalBytes)
        {
            int length = Math.Min(buffer.Length, totalBytes - bytesWritten);
            SendData(buffer.AsSpan(0, length));
            bytesWritten += length;
        }
    }

    public void DrawRgb565(ReadOnlySpan<byte> data)
    {
        if (data.Length != Width * Height * 2)
        {
            throw new ArgumentException($"RGB565 data must be exactly {Width * Height * 2} bytes.", nameof(data));
        }

        SetAddressWindow(0, 0, Width, Height);
        SendData(data);
    }

    public void SetRotation(byte rotation)
    {
        SendCommand(0x36);
        SendData((rotation % 4) switch
        {
            0 => (byte)0x70,
            1 => (byte)0x00,
            2 => (byte)0xC0,
            _ => (byte)0xA0
        });
    }

    public void SendCommand(byte command)
    {
        Select();
        _gpio.Write(_dcLine, PinValue.Low);
        _spiDevice.WriteByte(command);
        Deselect();
        Thread.Sleep(1);
    }

    public void SendData(byte data)
    {
        Select();
        _gpio.Write(_dcLine, PinValue.High);
        _spiDevice.WriteByte(data);
        Deselect();
    }

    public void SendData(params byte[] data)
    {
        SendData((ReadOnlySpan<byte>)data);
    }

    public void SendData(ReadOnlySpan<byte> data)
    {
        Select();
        _gpio.Write(_dcLine, PinValue.High);

        for (int offset = 0; offset < data.Length; offset += MaxTransferSize)
        {
            int length = Math.Min(MaxTransferSize, data.Length - offset);
            _spiDevice.Write(data.Slice(offset, length));
        }

        Deselect();
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }

        _spiDevice.Dispose();
        _disposed = true;
    }

    private void WriteCommandData(byte command, params byte[] data)
    {
        SendCommand(command);
        SendData(data);
    }

    private void Select()
    {
        if (_csLine >= 0)
        {
            _gpio.Write(_csLine, PinValue.Low);
        }
    }

    private void Deselect()
    {
        if (_csLine >= 0)
        {
            _gpio.Write(_csLine, PinValue.High);
        }
    }
}
