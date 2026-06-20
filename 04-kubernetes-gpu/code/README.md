# 模块 4 配套代码 — K8s GPU 工作负载调度

## 文件说明

| 文件                 | 内容                            | 对应 PPT               |
| -------------------- | ------------------------------- | ---------------------- |
| `01_nginx_demo.yaml` | Nginx Deployment + Service      | 第 16 页 [动手]        |
| `02_gpu_pod.yaml`    | GPU Pod — nvidia-smi 测试       | 第 45 页 [动手 1]      |
| `03_gpu_deploy.yaml` | GPU Deployment — 生产级工作负载 | 第 45-46 页 [动手 1+2] |

## 环境要求

- Kubernetes 集群 (minikube / k3s / kind 均可)
- NVIDIA Device Plugin 已安装 (GPU 实验需要)
- kubectl

## 运行方法

```bash
# 实验 1: K8s 基础 — 部署 Nginx
kubectl apply -f 01_nginx_demo.yaml
kubectl get pods,svc
kubectl scale deployment nginx-demo --replicas=5
kubectl port-forward deployment/nginx-demo 8080:80

# 实验 2: GPU Pod
kubectl apply -f 02_gpu_pod.yaml
kubectl logs gpu-test

# 实验 3: GPU Deployment + 争抢
kubectl apply -f 03_gpu_deploy.yaml
kubectl scale deployment gpu-inference --replicas=3  # 超过 GPU 数观察 Pending
kubectl describe pod <pending-pod> | grep -A5 Events

# 清理
kubectl delete -f 01_nginx_demo.yaml
kubectl delete -f 02_gpu_pod.yaml
kubectl delete -f 03_gpu_deploy.yaml
```
