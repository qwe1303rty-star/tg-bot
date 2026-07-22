$ErrorActionPreference = "SilentlyContinue"
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Stop-Process -Force

Start-Process -FilePath "py" `
  -ArgumentList "-3", "-m", "bot.main" `
  -WorkingDirectory "C:\Users\Директ Лайн\Desktop\tg bot" `
  -RedirectStandardOutput "C:\Users\Директ Лайн\Desktop\tg bot\bot.log" `
  -RedirectStandardError "C:\Users\Директ Лайн\Desktop\tg bot\bot_err.log" `
  -NoNewWindow:$false

Write-Host "Bot started. Check bot.log"
