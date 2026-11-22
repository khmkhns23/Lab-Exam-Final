# ==========================================================
# Local Verification Script for kind-k8s-lab (Student ID: 68130239)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\verify-local.ps1
# ==========================================================

$ErrorActionPreference = "Stop"
$KCtx = "kind-k8s-lab"
$Ns = "iam-239"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 0. KUBERNETES NODES (3-Node Cluster)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
kubectl --context $KCtx get nodes -o wide

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " 1. KUBERNETES RESOURCES (Namespace: $Ns)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
kubectl --context $KCtx get all,ingress,pv,pvc,cm,endpoints -n $Ns -o wide

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " 2. INGRESS DETAILS (DESCRIBE)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
kubectl --context $KCtx describe ingress iam-239-ingress -n $Ns

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " 3. EXTERNAL NGINX LB CONTAINER" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
docker ps --filter "name=k8s-lb-iam239" --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " 4. HTTP ROUTING TESTS (via Domain Names)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$tests = @(
    @{ Name = "Portal (www.iam-239.com/)"; Url = "http://www.iam-239.com/"; Pattern = "portal-239" },
    @{ Name = "Portal Avatar (/avatar)"; Url = "http://www.iam-239.com/avatar"; Pattern = "<svg|PNG|JFIF|WEBP|GIF" },
    @{ Name = "Research (/research)"; Url = "http://www.iam-239.com/research"; Pattern = "app-research" },
    @{ Name = "API (/api-239/Hello%2068130239)"; Url = "http://www.iam-239.com/api-239/Hello%2068130239"; Pattern = "Hello 68130239" },
    @{ Name = "Admin Home (admin.iam-239.com/)"; Url = "http://admin.iam-239.com/"; Pattern = "admin-239" },
    @{ Name = "Admin Portal Form (/portal)"; Url = "http://admin.iam-239.com/portal"; Pattern = "enctype=`"multipart/form-data`"" },
    @{ Name = "Admin Research Form (/research)"; Url = "http://admin.iam-239.com/research"; Pattern = "action=`"/research`"" }
)

$allPassed = $true
foreach ($t in $tests) {
    $tmpFile = [System.IO.Path]::GetTempFileName()
    try {
        $status = & curl.exe -s -o $tmpFile -w "%{http_code}" $t.Url
        $body = Get-Content -Path $tmpFile -Raw -Encoding UTF8
        $matched = $body -match $t.Pattern
        if ($status -eq "200" -and $matched) {
            Write-Host "[PASS] $($t.Name) -> HTTP $status" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] $($t.Name) -> HTTP $status (matched=$matched)" -ForegroundColor Red
            $allPassed = $false
        }
    } finally {
        Remove-Item -Path $tmpFile -Force -ErrorAction SilentlyContinue
    }
}

if (-not $allPassed) {
    exit 1
}
Write-Host "`nAll checks passed!" -ForegroundColor Green
