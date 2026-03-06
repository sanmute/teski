# Backend smoke test for production (teski-zj2gsg.fly.dev)
# Usage: .\smoke_test_prod.ps1 [-BaseUrl "https://teski-zj2gsg.fly.dev"]
# Captures all responses and status codes for STABILITY_REPORT.md

param(
    [string]$BaseUrl = "https://teski-zj2gsg.fly.dev"
)

$ErrorActionPreference = "Continue"
$Timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$TestEmail = "smoke-$Timestamp@teski-smoke.test"
$TestPassword = "SmokeTest123!"

function Invoke-SmokeRequest {
    param([string]$Method, [string]$Url, [hashtable]$Headers = @{}, [string]$Body = $null)
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            UseBasicParsing = $true
            Headers = $Headers
        }
        if ($Body) { $params.Body = $Body; $params.ContentType = "application/json" }
        $resp = Invoke-WebRequest @params
        return @{ Code = $resp.StatusCode; Body = $resp.Content }
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { "ERR" }
        $body = $_.Exception.Message
        return @{ Code = $code; Body = $body }
    }
}

Write-Host "=== Teski Backend Smoke Test ==="
Write-Host "Base URL: $BaseUrl"
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')"
Write-Host ""

# 1. Health check
Write-Host "--- 1. GET /health ---"
$health = Invoke-SmokeRequest -Method GET -Url "$BaseUrl/health"
Write-Host "Status: $($health.Code)"
Write-Host "Response: $($health.Body)"
Write-Host ""

# 2. CORS debug
Write-Host "--- 2. GET /api/debug/cors ---"
$cors = Invoke-SmokeRequest -Method GET -Url "$BaseUrl/api/debug/cors"
Write-Host "Status: $($cors.Code)"
Write-Host "Response: $($cors.Body)"
Write-Host ""

# 3. Exercise list
Write-Host "--- 3. GET /api/ex/list ---"
$exList = Invoke-SmokeRequest -Method GET -Url "$BaseUrl/api/ex/list"
Write-Host "Status: $($exList.Code)"
Write-Host "Response: $($exList.Body)"
$firstExId = $null
if ($exList.Body -match '"id"\s*:\s*"([^"]+)"') { $firstExId = $Matches[1] }
Write-Host "First exercise ID: $firstExId"
Write-Host ""

# 4. Exercise get
if ($firstExId) {
    Write-Host "--- 4. GET /api/ex/get?id=$firstExId ---"
    $exGet = Invoke-SmokeRequest -Method GET -Url "$BaseUrl/api/ex/get?id=$firstExId"
    Write-Host "Status: $($exGet.Code)"
    Write-Host "Response: $($exGet.Body)"
} else {
    Write-Host "--- 4. GET /api/ex/get (skipped - no exercises) ---"
    $exGet = @{ Code = "SKIP"; Body = "No exercises in list" }
}
Write-Host ""

# 5. Auth - Signup
Write-Host "--- 5. POST /auth/signup ---"
$signupBody = @{ email = $TestEmail; password = $TestPassword; display_name = "Smoke Test" } | ConvertTo-Json
$signup = Invoke-SmokeRequest -Method POST -Url "$BaseUrl/auth/signup" -Body $signupBody
Write-Host "Status: $($signup.Code)"
Write-Host "Response: $($signup.Body)"
$token = $null; $userId = $null
if ($signup.Body -match '"access_token"\s*:\s*"([^"]+)"') { $token = $Matches[1] }
if ($signup.Body -match '"user_id"\s*:\s*"([^"]+)"') { $userId = $Matches[1] }
Write-Host "Token: $($token.Substring(0, [Math]::Min(20, $token.Length)))..."
Write-Host "User ID: $userId"
Write-Host ""

# 6. Onboarding status
Write-Host "--- 6. GET /api/onboarding/status ---"
if ($token) {
    $onboardStatus = Invoke-SmokeRequest -Method GET -Url "$BaseUrl/api/onboarding/status" `
        -Headers @{ Authorization = "Bearer $token" }
} else {
    $onboardStatus = @{ Code = "SKIP"; Body = "No token from signup" }
}
Write-Host "Status: $($onboardStatus.Code)"
Write-Host "Response: $($onboardStatus.Body)"
Write-Host ""

# 7. Onboarding submit
Write-Host "--- 7. POST /api/onboarding/submit ---"
if ($token) {
    $onboardPayload = '{"motivation_style":"mentor","difficulty_preference":"balanced","daily_minutes_target":15,"skipped":false}'
    $onboardSubmit = Invoke-SmokeRequest -Method POST -Url "$BaseUrl/api/onboarding/submit" `
        -Headers @{ Authorization = "Bearer $token" } -Body $onboardPayload
} else {
    $onboardSubmit = @{ Code = "SKIP"; Body = "No token" }
}
Write-Host "Status: $($onboardSubmit.Code)"
Write-Host "Response: $($onboardSubmit.Body)"
Write-Host ""

# 8. Exercise submit
Write-Host "--- 8. POST /api/ex/answer ---"
if ($userId -and $firstExId) {
    $exAnswerBody = @{ user_id = $userId; exercise_id = $firstExId; answer = "0" } | ConvertTo-Json
    $exAnswer = Invoke-SmokeRequest -Method POST -Url "$BaseUrl/api/ex/answer" `
        -Headers @{ Authorization = "Bearer $token" } -Body $exAnswerBody
} else {
    $exAnswer = @{ Code = "SKIP"; Body = "Missing user_id or exercise_id" }
}
Write-Host "Status: $($exAnswer.Code)"
Write-Host "Response: $($exAnswer.Body)"
Write-Host ""

# 9. Explanations - text (frontend uses /explanations/generate, API uses /api/explanations/generate)
Write-Host "--- 9. POST /explanations/generate (text) ---"
$explainBody = '{"text":"What is 2+2?","mode":"big_picture"}'
$explain = Invoke-SmokeRequest -Method POST -Url "$BaseUrl/explanations/generate" -Body $explainBody
Write-Host "Status: $($explain.Code)"
Write-Host "Response: $($explain.Body)"
Write-Host ""

# 10. Explanations - exercise
if ($firstExId) {
    Write-Host "--- 10. POST /explanations/generate (exercise_id) ---"
    $explainExBody = @{ exercise_id = $firstExId; user_answer = "0" } | ConvertTo-Json
    $explainEx = Invoke-SmokeRequest -Method POST -Url "$BaseUrl/explanations/generate" -Body $explainExBody
    Write-Host "Status: $($explainEx.Code)"
    Write-Host "Response: $($explainEx.Body)"
} else {
    Write-Host "--- 10. POST /api/explanations/generate (exercise) - skipped ---"
    $explainEx = @{ Code = "SKIP" }
}
Write-Host ""

# Summary
Write-Host "=== Summary ==="
Write-Host "Health: $($health.Code) | CORS: $($cors.Code) | ExList: $($exList.Code) | ExGet: $($exGet.Code)"
Write-Host "Signup: $($signup.Code) | OnboardStatus: $($onboardStatus.Code) | OnboardSubmit: $($onboardSubmit.Code)"
Write-Host "ExAnswer: $($exAnswer.Code) | Explain: $($explain.Code) | ExplainEx: $($explainEx.Code)"
Write-Host ""
Write-Host "Completed: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')"
