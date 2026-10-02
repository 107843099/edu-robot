$ErrorActionPreference = 'Stop'

$siteRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$listener = $null
$selectedPort = $null
$selectedHost = $null

function Get-ContentType([string]$path) {
    switch ([System.IO.Path]::GetExtension($path).ToLowerInvariant()) {
        '.html' { return 'text/html; charset=utf-8' }
        '.css'  { return 'text/css; charset=utf-8' }
        '.js'   { return 'text/javascript; charset=utf-8' }
        '.json' { return 'application/json; charset=utf-8' }
        '.txt'  { return 'text/plain; charset=utf-8' }
        '.svg'  { return 'image/svg+xml' }
        '.png'  { return 'image/png' }
        '.ico'  { return 'image/x-icon' }
        '.bin'  { return 'application/octet-stream' }
        '.woff' { return 'font/woff' }
        '.woff2' { return 'font/woff2' }
        default { return 'application/octet-stream' }
    }
}

function Send-Response($context, [int]$statusCode, [byte[]]$body, [string]$contentType) {
    $response = $context.Response
    $response.StatusCode = $statusCode
    $response.ContentType = $contentType
    $response.ContentLength64 = $body.Length
    $response.Headers['Cache-Control'] = 'no-store'

    if ($context.Request.HttpMethod -ne 'HEAD') {
        $response.OutputStream.Write($body, 0, $body.Length)
    }

    $response.Close()
}

function Send-TextResponse($context, [int]$statusCode, [string]$message) {
    $body = [System.Text.Encoding]::UTF8.GetBytes($message)
    Send-Response $context $statusCode $body 'text/plain; charset=utf-8'
}

try {
    for ($candidatePort = 39876; $candidatePort -le 39926 -and $null -eq $listener; $candidatePort++) {
        foreach ($candidateHost in @('127.0.0.1', 'localhost')) {
            $candidate = New-Object System.Net.HttpListener
            $candidate.Prefixes.Add("http://$candidateHost`:$candidatePort/")

            try {
                $candidate.Start()
                $listener = $candidate
                $selectedPort = $candidatePort
                $selectedHost = $candidateHost
                break
            }
            catch {
                $candidate.Close()
            }
        }
    }

    if ($null -eq $listener) {
        throw '无法占用本机 HTTP 端口。请关闭其他本地网页服务器后重试；如果仍失败，请右键以管理员身份运行此脚本。'
    }

    $url = "http://$selectedHost`:$selectedPort/"
    Write-Host ''
    Write-Host 'cardboard-bot 离线安装器已启动。' -ForegroundColor Green
    Write-Host "安装网页：$url" -ForegroundColor Cyan
    Write-Host '请保持此窗口打开，安装完成后关闭此窗口即可停止服务。' -ForegroundColor Yellow
    Write-Host '请使用最新版 Chrome 或 Edge；不要直接双击 index.html。' -ForegroundColor Yellow
    Write-Host ''

    try {
        Start-Process $url | Out-Null
    }
    catch {
        Write-Host '浏览器未能自动打开，请复制上面的地址到 Chrome 或 Edge。' -ForegroundColor Yellow
    }

    $rootWithSeparator = $siteRoot.TrimEnd('\') + '\'

    while ($listener.IsListening) {
        try {
            $context = $listener.GetContext()
        }
        catch [System.Net.HttpListenerException] {
            break
        }

        try {
            $requestPath = [System.Uri]::UnescapeDataString($context.Request.Url.AbsolutePath)
            $relativePath = $requestPath.TrimStart('/') -replace '/', '\'

            if ([string]::IsNullOrWhiteSpace($relativePath)) {
                $relativePath = 'index.html'
            }

            $requestedPath = [System.IO.Path]::GetFullPath((Join-Path $siteRoot $relativePath))
            $insideRoot = $requestedPath.Equals($siteRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
                $requestedPath.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)

            if (-not $insideRoot) {
                Send-TextResponse $context 403 'Forbidden'
                continue
            }

            if ((Test-Path -LiteralPath $requestedPath -PathType Container)) {
                $requestedPath = Join-Path $requestedPath 'index.html'
            }

            if (-not (Test-Path -LiteralPath $requestedPath -PathType Leaf)) {
                Send-TextResponse $context 404 'Not Found'
                continue
            }

            $body = [System.IO.File]::ReadAllBytes($requestedPath)
            Send-Response $context 200 $body (Get-ContentType $requestedPath)
        }
        catch {
            try {
                Send-TextResponse $context 500 '本地安装器服务器发生错误。'
            }
            catch {
                # The browser may have closed the connection already.
            }
        }
    }
}
catch {
    Write-Host "启动失败：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    if ($null -ne $listener) {
        $listener.Stop()
        $listener.Close()
    }
}
