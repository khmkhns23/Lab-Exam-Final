#!/usr/bin/env bash
# ==========================================================
# Automated Deploy Script for Student ID: 68130239 (iam-239)
# Run on Control Plane: bash scripts/deploy.sh
# ==========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NS="iam-239"

echo "=========================================================="
echo " [1/5] Checking NGINX Ingress Controller..."
echo "=========================================================="
if ! kubectl get namespace ingress-nginx >/dev/null 2>&1; then
  echo "Installing NGINX Ingress Controller (Bare-metal v1.15.1)..."
  kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/baremetal/deploy.yaml
  echo "Waiting for admission webhook jobs..."
  kubectl wait --namespace ingress-nginx \
    --for=condition=complete job/ingress-nginx-admission-create \
    --timeout=120s
  kubectl wait --namespace ingress-nginx \
    --for=condition=complete job/ingress-nginx-admission-patch \
    --timeout=120s
else
  echo "NGINX Ingress Controller namespace already exists."
fi

echo "Waiting for ingress-nginx-controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

# กำหนด NodePort ของ Ingress Controller เป็น 31080 เพื่อไม่ให้ชนกับ Lab เดิม (30080)
CURRENT_NODEPORT=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[0].nodePort}')
if [ "$CURRENT_NODEPORT" != "31080" ]; then
  kubectl patch svc ingress-nginx-controller -n ingress-nginx \
    -p 'spec: {ports: [{port: 80, nodePort: 31080}]}'
fi
echo "NGINX Ingress HTTP NodePort: $(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.ports[0].nodePort}')"

echo "=========================================================="
echo " [2/5] Creating Namespace & Persistent Storage..."
echo "=========================================================="
kubectl apply -f "$PROJECT_DIR/k8s/00-namespace.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/01-storage.yaml"

echo "=========================================================="
echo " [3/5] Packaging Application Code into ConfigMaps..."
echo "=========================================================="
kubectl create configmap portal-239-code \
  --from-file="$PROJECT_DIR/apps/portal-239/" \
  -n "$NS" --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap app-research-code \
  --from-file="$PROJECT_DIR/apps/app-research/server.py" \
  -n "$NS" --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap api-239-code \
  --from-file="$PROJECT_DIR/apps/api-239/server.py" \
  -n "$NS" --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap admin-239-code \
  --from-file="$PROJECT_DIR/apps/admin-239/" \
  -n "$NS" --dry-run=client -o yaml | kubectl apply -f -

echo "=========================================================="
echo " [4/5] Deploying Deployments, Services & Ingress..."
echo "=========================================================="
kubectl apply -f "$PROJECT_DIR/k8s/02-portal-239.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/03-app-research.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/04-api-239.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/05-admin-239.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/06-ingress.yaml"

echo "=========================================================="
echo " [5/5] Restarting & Waiting for Pods to become Ready..."
echo "=========================================================="
kubectl rollout restart deployment/portal-239 deployment/app-research deployment/api-239 deployment/admin-239 -n "$NS"
kubectl rollout status deployment/portal-239 -n "$NS" --timeout=180s
kubectl rollout status deployment/app-research -n "$NS" --timeout=180s
kubectl rollout status deployment/api-239 -n "$NS" --timeout=180s
kubectl rollout status deployment/admin-239 -n "$NS" --timeout=180s

echo ""
echo "Deployment Complete! Current resources in namespace '$NS':"
kubectl get pv,pvc,pods,svc,ingress -n "$NS" -o wide
