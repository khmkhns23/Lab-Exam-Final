#!/usr/bin/env bash
# ==========================================================
# Verification Script for Student ID: 68130239 (iam-239)
# Run on Control Plane: bash scripts/verify.sh
# ==========================================================

NS="iam-239"
LB_IP="${LB_IP:-192.168.1.20}"

echo "=========================================================="
echo " 0. KUBERNETES NODES"
echo "=========================================================="
kubectl get nodes -o wide

echo -e "\n=========================================================="
echo " 1. KUBERNETES RESOURCES (GET)"
echo "=========================================================="
kubectl get all,ingress,pv,pvc,cm -n "$NS" -o wide

echo -e "\n=========================================================="
echo " 2. INGRESS DETAILS (DESCRIBE)"
echo "=========================================================="
kubectl describe ingress iam-239-ingress -n "$NS"

echo -e "\n=========================================================="
echo " 3. ENDPOINTS CHECK"
echo "=========================================================="
kubectl get endpoints -n "$NS"

echo -e "\n=========================================================="
echo " 4. HTTP ROUTING TEST (via External LB $LB_IP)"
echo "=========================================================="
echo "--- Test www.iam-239.com/ (portal-239) ---"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: www.iam-239.com" "http://${LB_IP}/"

echo "--- Test www.iam-239.com/research (app-research) ---"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: www.iam-239.com" "http://${LB_IP}/research"

echo "--- Test www.iam-239.com/api-239/Hello_68130239 (api-239) ---"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: www.iam-239.com" "http://${LB_IP}/api-239/Hello_68130239"

echo "--- Test admin.iam-239.com/ (admin-239) ---"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: admin.iam-239.com" "http://${LB_IP}/"

echo "--- Test admin.iam-239.com/portal ---"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: admin.iam-239.com" "http://${LB_IP}/portal"

echo "--- Test admin.iam-239.com/research ---"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" -H "Host: admin.iam-239.com" "http://${LB_IP}/research"
