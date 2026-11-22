#!/usr/bin/env bash
# ==========================================================
# Node Prerequisite Script for Kubernetes v1.31 (Ubuntu 24.04)
# รันบน k8s-control, k8s-worker1, k8s-worker2: sudo bash scripts/node-prereq.sh
# ==========================================================

set -e

echo "[1/5] Disabling Swap..."
swapoff -a
sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

echo "[2/5] Configuring Kernel Modules & Sysctl..."
cat << 'EOF' > /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
modprobe overlay
modprobe br_netfilter

cat << 'EOF' > /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system

echo "[3/5] Installing & Configuring containerd (SystemdCgroup = true)..."
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gpg containerd

mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml
systemctl restart containerd
systemctl enable containerd

echo "[4/5] Adding Kubernetes v1.31 APT Repository..."
mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | gpg --dearmor --yes -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' > /etc/apt/sources.list.d/kubernetes.list

echo "[5/5] Installing kubelet, kubeadm, kubectl..."
apt-get update
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

echo "=========================================================="
echo " Node setup complete!"
echo "=========================================================="
