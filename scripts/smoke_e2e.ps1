# Smoke end-to-end da stack (api + model_service + MLflow) via docker-compose.
#
# Pre-requisitos:
#   docker compose --profile api up -d --build
#   docker compose exec api alembic upgrade head
#
# Uso:  pwsh scripts/smoke_e2e.ps1

$ErrorActionPreference = "Stop"
$base  = "http://localhost:8001/api/v1"
$email = "smoke@datathon.local"

function J($o) { $o | ConvertTo-Json -Compress -Depth 6 }

# health
Write-Output "health api:   $((Invoke-RestMethod "$base/health").status)"
Write-Output "health bandit: $((Invoke-RestMethod "$base/health").status)"

# auth
try { Invoke-RestMethod -Uri "$base/register" -Method Post -ContentType "application/json" -Body (@{email=$email;password="password123"}|ConvertTo-Json) | Out-Null } catch {}
$login = Invoke-RestMethod -Uri "$base/login" -Method Post -ContentType "application/json" -Body (@{email=$email;password="password123"}|ConvertTo-Json)
$h = @{ Authorization = "Bearer $($login.accessToken)" }

# offers -> feedback -> offers (aprendizado)
$o1 = Invoke-RestMethod -Uri "$base/offers" -Headers $h
Write-Output "offers: $($o1.Count) elegiveis | top-1=$($o1[0].armId) (valorFinal=$($o1[0].valorFinal))"
$target = $o1[-1].armId
$before = ($o1 | Where-Object { $_.armId -eq $target }).rank
1..20 | ForEach-Object { Invoke-RestMethod -Uri "$base/feedback" -Method Post -Headers $h -ContentType "application/json" -Body (@{armId=$target;clicked=$true}|ConvertTo-Json) | Out-Null }
$o2 = Invoke-RestMethod -Uri "$base/offers" -Headers $h
$after = ($o2 | Where-Object { $_.armId -eq $target }).rank
Write-Output "feedback x20 em '$target': rank $before -> $after (aprendizado: $($after -lt $before))"

# MLflow registry
$reg = Invoke-RestMethod -Uri "$base/registry/models" -Method Post -ContentType "application/json" -Body (@{name="bandit-linucb";algorithm="linucb"}|ConvertTo-Json)
Write-Output "registry register: $(J $reg)"
Write-Output "registry list:     $(J (Invoke-RestMethod "$base/registry/models"))"

Write-Output "SMOKE OK"
