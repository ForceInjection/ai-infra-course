# 模块 4 配套代码 — K8s GPU 工作负载调度

## 文件说明

| 文件                 | 内容                                            | 对应 PPT               |
| -------------------- | ----------------------------------------------- | ---------------------- |
| `01_nginx_demo.yaml` | ConfigMap + Deployment (含资源限制) + NodePort Service | 第 16 页 [动手]        |
| `02_gpu_pod.yaml`    | GPU Pod — nvidia-smi 测试                       | 第 45 页 [动手 1]      |
| `03_gpu_deploy.yaml` | GPU Deployment — 生产级工作负载                 | 第 45-46 页 [动手 1+2] |

## 环境要求

- Kubernetes 集群 (minikube / k3s / kind 均可)
- NVIDIA Device Plugin 已安装 (GPU 实验需要)
- kubectl

## 运行方法

```bash
# 实验 1: K8s 基础 — ConfigMap + Deployment + Service
kubectl apply -f 01_nginx_demo.yaml
kubectl get configmap,deploy,pods,svc       # 查看创建的所有资源
curl localhost:30080                          # 访问 Nginx (NodePort)
kubectl scale deployment nginx-demo --replicas=5  # 扩容
kubectl get pods -o wide                      # 观察 Pod 分布
# 可选: 修改 ConfigMap, kubectl rollout restart deployment nginx-demo, 观察生效

# 实验 2: GPU Pod (需要 GPU 节点)
kubectl apply -f 02_gpu_pod.yaml
kubectl logs gpu-test                         # 查看 nvidia-smi 输出

# 实验 3: GPU Deployment + 资源争抢
kubectl apply -f 03_gpu_deploy.yaml
kubectl scale deployment gpu-inference --replicas=3  # 超过 GPU 数观察 Pending
kubectl describe pod <pending-pod> | grep -A5 Events  # 查看调度失败原因
# 观察: Events 中显示 "insufficient nvidia.com/gpu"

# 清理
kubectl delete -f 01_nginx_demo.yaml
kubectl delete -f 02_gpu_pod.yaml
kubectl delete -f 03_gpu_deploy.yaml
```
