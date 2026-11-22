@echo off
setlocal enabledelayedexpansion
REM ==========================================================
REM Local Windows Deploy Script for kind-k8s-lab (ID: 68130239)
REM Usage: Double-click or run scripts\deploy.bat
REM ==========================================================

set "KCTX=kind-k8s-lab"
set "NS=iam-239"
set "LB_CONTAINER=k8s-lb-iam239"
for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"

echo ==========================================================
echo  [1/6] Checking Kubernetes cluster (%KCTX%) ...
echo ==========================================================
kubectl --context %KCTX% get nodes -o wide
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Cannot connect to cluster context %KCTX%.
    exit /b 1
)

echo ==========================================================
echo  [2/6] Checking NGINX Ingress Controller (v1.15.1) ...
echo ==========================================================
kubectl --context %KCTX% get namespace ingress-nginx >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing NGINX Ingress Controller ^(Bare-metal v1.15.1^)...
    kubectl --context %KCTX% apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/baremetal/deploy.yaml
    if %ERRORLEVEL% NEQ 0 goto :err
    kubectl --context %KCTX% wait --namespace ingress-nginx --for=condition=complete job/ingress-nginx-admission-create --timeout=120s
    kubectl --context %KCTX% wait --namespace ingress-nginx --for=condition=complete job/ingress-nginx-admission-patch --timeout=120s
) else (
    echo NGINX Ingress Controller namespace already exists.
)

kubectl --context %KCTX% wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=180s
if %ERRORLEVEL% NEQ 0 goto :err

kubectl --context %KCTX% patch svc ingress-nginx-controller -n ingress-nginx -p "spec: {ports: [{port: 80, nodePort: 31080}]}"
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% get svc ingress-nginx-controller -n ingress-nginx

echo ==========================================================
echo  [3/6] Creating Namespace and Persistent Storage ...
echo ==========================================================
kubectl --context %KCTX% apply -f "%PROJECT_DIR%\k8s\00-namespace.yaml" -f "%PROJECT_DIR%\k8s\01-storage.yaml"
if %ERRORLEVEL% NEQ 0 goto :err

echo ==========================================================
echo  [4/6] Packaging Application Code into ConfigMaps ...
echo ==========================================================
kubectl --context %KCTX% create configmap portal-239-code --from-file="%PROJECT_DIR%\apps\portal-239" -n %NS% --dry-run=client -o yaml | kubectl --context %KCTX% apply -f -
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% create configmap app-research-code --from-file="%PROJECT_DIR%\apps\app-research\server.py" -n %NS% --dry-run=client -o yaml | kubectl --context %KCTX% apply -f -
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% create configmap api-239-code --from-file="%PROJECT_DIR%\apps\api-239\server.py" -n %NS% --dry-run=client -o yaml | kubectl --context %KCTX% apply -f -
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% create configmap admin-239-code --from-file="%PROJECT_DIR%\apps\admin-239" -n %NS% --dry-run=client -o yaml | kubectl --context %KCTX% apply -f -
if %ERRORLEVEL% NEQ 0 goto :err

echo ==========================================================
echo  [5/6] Deploying Deployments, Services and Ingress ...
echo ==========================================================
kubectl --context %KCTX% apply -f "%PROJECT_DIR%\k8s\02-portal-239.yaml" -f "%PROJECT_DIR%\k8s\03-app-research.yaml" -f "%PROJECT_DIR%\k8s\04-api-239.yaml" -f "%PROJECT_DIR%\k8s\05-admin-239.yaml" -f "%PROJECT_DIR%\k8s\06-ingress.yaml"
if %ERRORLEVEL% NEQ 0 goto :err

kubectl --context %KCTX% rollout restart deployment/portal-239 deployment/app-research deployment/api-239 deployment/admin-239 -n %NS%
if %ERRORLEVEL% NEQ 0 goto :err

echo ==========================================================
echo  [6/6] Waiting for Pods and starting Nginx LB (%LB_CONTAINER%) ...
echo ==========================================================
kubectl --context %KCTX% rollout status deployment/portal-239 -n %NS% --timeout=180s
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% rollout status deployment/app-research -n %NS% --timeout=180s
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% rollout status deployment/api-239 -n %NS% --timeout=180s
if %ERRORLEVEL% NEQ 0 goto :err
kubectl --context %KCTX% rollout status deployment/admin-239 -n %NS% --timeout=180s
if %ERRORLEVEL% NEQ 0 goto :err

docker rm -f %LB_CONTAINER% >nul 2>&1
docker run -d --name %LB_CONTAINER% --restart unless-stopped --network kind -p 80:80 -v "%PROJECT_DIR%\configs\k8s-lb-kind.conf:/etc/nginx/conf.d/iam-239-ingress.conf:ro" nginx:1.25-alpine sh -c "rm -f /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"
if %ERRORLEVEL% NEQ 0 goto :err
docker exec %LB_CONTAINER% nginx -t
if %ERRORLEVEL% NEQ 0 goto :err

echo.
echo ==========================================================
echo  Deployment Complete! Resources in namespace '%NS%':
echo ==========================================================
kubectl --context %KCTX% get pv,pvc,pods,svc,ingress -n %NS% -o wide
exit /b 0

:err
echo [ERROR] Deployment failed with exit code %ERRORLEVEL%.
exit /b 1
