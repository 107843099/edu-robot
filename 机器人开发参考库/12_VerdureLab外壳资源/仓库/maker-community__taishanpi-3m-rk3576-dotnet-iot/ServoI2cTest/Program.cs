using System.Device.I2c;
using System.Globalization;

var options = Options.Parse(args);

if (options.ShowHelp)
{
    PrintHelp();
    return;
}

Console.WriteLine("ServoF030 minimal I2C test for TaishanPi 3M / RK3576");
Console.WriteLine($"I2C bus: {options.BusId}");
Console.WriteLine($"Targets: {string.Join(", ", options.Targets.Select(FormatTarget))}");
Console.WriteLine($"Retries: {options.Retries}");
Console.WriteLine($"Delay: {options.DelayMs} ms");

if (!options.Enable && !options.Disable && options.Angle is null && !options.Sweep)
{
    Console.WriteLine("Mode: read-only probe. No movement command will be sent.");
}

foreach (ServoTarget target in options.Targets)
{
    Console.WriteLine();
    Console.WriteLine($"== {FormatTarget(target)} ==");

    try
    {
        using I2cDevice device = I2cDevice.Create(new I2cConnectionSettings(options.BusId, target.Address));

        if (options.Enable)
        {
            SendEnable(device, true, options.Retries);
            Thread.Sleep(options.DelayMs);
        }

        if (options.Disable)
        {
            SendEnable(device, false, options.Retries);
            Thread.Sleep(options.DelayMs);
        }

        if (options.Angle is float angle)
        {
            SendAngle(device, angle, options.Retries);
            Thread.Sleep(options.DelayMs);
        }

        if (options.Sweep)
        {
            float center = options.Angle ?? target.DefaultCenterAngle;
            float low = Math.Clamp(center - options.SweepDelta, 0.0f, 180.0f);
            float high = Math.Clamp(center + options.SweepDelta, 0.0f, 180.0f);

            for (int cycle = 1; cycle <= options.Cycles; cycle++)
            {
                Console.WriteLine($"cycle {cycle}/{options.Cycles}: low={low:F1}, high={high:F1}, center={center:F1}");

                SendAngle(device, low, options.Retries);
                Thread.Sleep(options.DelayMs);
                SendAngle(device, high, options.Retries);
                Thread.Sleep(options.DelayMs);
                SendAngle(device, center, options.Retries);
                Thread.Sleep(options.DelayMs);
            }
        }

        ReadAngle(device, options.Retries);
    }
    catch (Exception ex)
    {
        Console.WriteLine($"open failed: {ex.GetType().Name}: {ex.Message}");
    }
}

static void SendEnable(I2cDevice device, bool enable, int retries)
{
    Span<byte> tx = stackalloc byte[5] { 0xff, enable ? (byte)0x01 : (byte)0x00, 0x00, 0x00, 0x00 };
    Span<byte> rx = stackalloc byte[5];

    if (TryWriteRead(device, tx, rx, retries, out string? error))
    {
        Console.WriteLine($"enable={(enable ? 1 : 0)} ok, rx={FormatBytes(rx)}");
    }
    else
    {
        Console.WriteLine($"enable={(enable ? 1 : 0)} failed: {error}");
    }
}

static void SendAngle(I2cDevice device, float angle, int retries)
{
    Span<byte> tx = stackalloc byte[5];
    Span<byte> rx = stackalloc byte[5];
    tx[0] = 0x01;
    BitConverter.TryWriteBytes(tx[1..], angle);

    if (TryWriteRead(device, tx, rx, retries, out string? error))
    {
        Console.WriteLine($"angle={angle:F1} ok, rx={FormatBytes(rx)}, reported={ReadFloatOrNaN(rx):F2}");
    }
    else
    {
        Console.WriteLine($"angle={angle:F1} failed: {error}");
    }
}

static void ReadAngle(I2cDevice device, int retries)
{
    Span<byte> tx = stackalloc byte[5] { 0x11, 0x00, 0x00, 0x00, 0x00 };
    Span<byte> rx = stackalloc byte[5];

    if (TryWriteRead(device, tx, rx, retries, out string? error))
    {
        Console.WriteLine($"read ok, rx={FormatBytes(rx)}, reported={ReadFloatOrNaN(rx):F2}");
    }
    else
    {
        Console.WriteLine($"read failed: {error}");
    }
}

static bool TryWriteRead(I2cDevice device, ReadOnlySpan<byte> tx, Span<byte> rx, int retries, out string? error)
{
    error = null;

    for (int attempt = 1; attempt <= retries; attempt++)
    {
        try
        {
            device.WriteRead(tx, rx);
            return true;
        }
        catch (Exception ex)
        {
            error = $"attempt {attempt}/{retries}: {ex.GetType().Name}: {ex.Message}";
            Thread.Sleep(10);
        }
    }

    return false;
}

static float ReadFloatOrNaN(ReadOnlySpan<byte> rx)
{
    return rx.Length >= 5 ? BitConverter.ToSingle(rx[1..5]) : float.NaN;
}

static string FormatBytes(ReadOnlySpan<byte> bytes)
{
    return string.Join('-', bytes.ToArray().Select(x => x.ToString("X2", CultureInfo.InvariantCulture)));
}

static string ToHex(int value)
{
    return $"0x{value:X2}";
}

static string FormatTarget(ServoTarget target)
{
    return target.JointId is int jointId
        ? $"joint {jointId} ({target.Name}) -> {ToHex(target.Address)}"
        : ToHex(target.Address);
}

static void PrintHelp()
{
    Console.WriteLine("ServoF030 minimal I2C test");
    Console.WriteLine();
    Console.WriteLine("Usage:");
    Console.WriteLine("  sudo dotnet run --project ServoI2cTest -- [options]");
    Console.WriteLine();
    Console.WriteLine("Options:");
    Console.WriteLine("  --bus <n>              I2C bus id. Default: 1");
    Console.WriteLine("  --address <addr>       Single address, e.g. 0x03");
    Console.WriteLine("  --addresses <list>     Address list or range, e.g. 0x01-0x06 or 0x02,0x03");
    Console.WriteLine("  --joint <id>           Single joint id, e.g. 6");
    Console.WriteLine("  --joints <list>        Joint id list or range, e.g. 2,4,6 or 2-12");
    Console.WriteLine("  --enable               Send FF 01 00 00 00 before other commands");
    Console.WriteLine("  --disable              Send FF 00 00 00 00 before other commands");
    Console.WriteLine("  --angle <degrees>      Send angle command 01 + float32");
    Console.WriteLine("  --sweep                Move angle-delta, angle+delta, then angle");
    Console.WriteLine("  --cycles <n>           Sweep loop count. Default: 1");
    Console.WriteLine("  --delta <degrees>      Sweep delta. Default: 5");
    Console.WriteLine("  --delay <ms>           Delay between commands. Default: 500");
    Console.WriteLine("  --retries <n>          I2C retry count. Default: 3");
    Console.WriteLine("  --help                 Show help");
    Console.WriteLine();
    Console.WriteLine("Joint map from Verdure sample:");
    Console.WriteLine("  2  -> 0x01");
    Console.WriteLine("  4  -> 0x02");
    Console.WriteLine("  6  -> 0x03");
    Console.WriteLine("  8  -> 0x04");
    Console.WriteLine("  10 -> 0x05");
    Console.WriteLine("  12 -> 0x06");
}

sealed record Options(
    int BusId,
    IReadOnlyList<ServoTarget> Targets,
    bool Enable,
    bool Disable,
    float? Angle,
    bool Sweep,
    int Cycles,
    float SweepDelta,
    int DelayMs,
    int Retries,
    bool ShowHelp)
{
    public static Options Parse(string[] args)
    {
        int busId = 1;
        List<ServoTarget> targets = BuildAddressTargets(ParseNumberList("0x01-0x06"));
        bool enable = false;
        bool disable = false;
        float? angle = null;
        bool sweep = false;
        int cycles = 1;
        float sweepDelta = 5.0f;
        int delayMs = 500;
        int retries = 3;
        bool showHelp = false;

        for (int i = 0; i < args.Length; i++)
        {
            string arg = args[i];
            string? next = i + 1 < args.Length ? args[i + 1] : null;

            switch (arg)
            {
                case "--bus":
                    busId = ParseInt(RequireValue(arg, next));
                    i++;
                    break;
                case "--address":
                    targets = BuildAddressTargets([ParseInt(RequireValue(arg, next))]);
                    i++;
                    break;
                case "--addresses":
                    targets = BuildAddressTargets(ParseNumberList(RequireValue(arg, next)));
                    i++;
                    break;
                case "--joint":
                    targets = BuildJointTargets([ParseInt(RequireValue(arg, next))]);
                    i++;
                    break;
                case "--joints":
                    targets = BuildJointTargets(ParseNumberList(RequireValue(arg, next)));
                    i++;
                    break;
                case "--enable":
                    enable = true;
                    break;
                case "--disable":
                    disable = true;
                    break;
                case "--angle":
                    angle = float.Parse(RequireValue(arg, next), CultureInfo.InvariantCulture);
                    i++;
                    break;
                case "--sweep":
                    sweep = true;
                    break;
                case "--cycles":
                    cycles = ParseInt(RequireValue(arg, next));
                    i++;
                    break;
                case "--delta":
                    sweepDelta = float.Parse(RequireValue(arg, next), CultureInfo.InvariantCulture);
                    i++;
                    break;
                case "--delay":
                    delayMs = ParseInt(RequireValue(arg, next));
                    i++;
                    break;
                case "--retries":
                    retries = ParseInt(RequireValue(arg, next));
                    i++;
                    break;
                case "--help":
                case "-h":
                    showHelp = true;
                    break;
                default:
                    throw new ArgumentException($"Unknown argument: {arg}");
            }
        }

        if (cycles < 1)
        {
            throw new ArgumentException("--cycles must be >= 1");
        }

        return new Options(busId, targets, enable, disable, angle, sweep, cycles, sweepDelta, delayMs, retries, showHelp);
    }

    static string RequireValue(string option, string? value)
    {
        return string.IsNullOrWhiteSpace(value) || value.StartsWith("--", StringComparison.Ordinal)
            ? throw new ArgumentException($"Missing value for {option}")
            : value;
    }

    static List<int> ParseNumberList(string value)
    {
        if (value.Contains('-', StringComparison.Ordinal))
        {
            string[] parts = value.Split('-', 2, StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);
            int start = ParseInt(parts[0]);
            int end = ParseInt(parts[1]);

            if (end < start)
            {
                throw new ArgumentException($"Invalid range: {value}");
            }

            return Enumerable.Range(start, end - start + 1).ToList();
        }

        return value.Split(',', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries)
            .Select(ParseInt)
            .ToList();
    }

    static List<ServoTarget> BuildAddressTargets(IEnumerable<int> addresses)
    {
        return addresses.Select(address => ServoTarget.FromAddress(address)).ToList();
    }

    static List<ServoTarget> BuildJointTargets(IEnumerable<int> jointIds)
    {
        return jointIds.Select(ServoTarget.FromJointId).ToList();
    }

    static int ParseInt(string value)
    {
        return value.StartsWith("0x", StringComparison.OrdinalIgnoreCase)
            ? Convert.ToInt32(value, 16)
            : int.Parse(value, CultureInfo.InvariantCulture);
    }
}

sealed record ServoTarget(int? JointId, string Name, int Address, float DefaultCenterAngle)
{
    private static readonly Dictionary<int, ServoTarget> JointMap = new()
    {
        [2] = new ServoTarget(2, "头部/预留", 0x01, 82.5f),
        [4] = new ServoTarget(4, "左耳", 0x02, 60.0f),
        [6] = new ServoTarget(6, "左臂", 0x03, 90.0f),
        [8] = new ServoTarget(8, "右耳", 0x04, 150.0f),
        [10] = new ServoTarget(10, "右臂", 0x05, 90.0f),
        [12] = new ServoTarget(12, "脖子", 0x06, 90.0f),
    };

    public static ServoTarget FromJointId(int jointId)
    {
        if (!JointMap.TryGetValue(jointId, out ServoTarget? target))
        {
            throw new ArgumentException($"Unknown joint id: {jointId}. Supported: {string.Join(", ", JointMap.Keys.OrderBy(x => x))}");
        }

        return target;
    }

    public static ServoTarget FromAddress(int address)
    {
        ServoTarget? target = JointMap.Values.FirstOrDefault(x => x.Address == address);
        return target ?? new ServoTarget(null, "raw-address", address, 90.0f);
    }
}