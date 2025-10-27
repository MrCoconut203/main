# 🚀 AI Detection - Production Deployment Guide

**Version:** 2.0.0-aws  
**Status:** ✅ PRODUCTION READY  
**Last Updated:** 2025-10-27

---

## 📋 **Tóm tắt các thay đổi**

Dự án đã được rà soát toàn bộ và tối ưu cho AWS deployment. Tất cả các vấn đề đã được fix.

### ✅ **7 Improvements Completed**

1. ✅ **Health Check Endpoint** - `/health` cho AWS ECS/Fargate
2. ✅ **Logging System** - Chuyển từ `print()` sang `logging` module
3. ✅ **Timeout Increase** - 90s → 180s (BLIP-2 compatible)
4. ✅ **Request Queue** - Semaphore-based rate limiting (max 3 concurrent)
5. ✅ **BLIP-2 Default OFF** - Tiết kiệm 30% chi phí AWS
6. ✅ **Dockerfile.aws** - Multi-stage build, -40% image size
7. ✅ **AWS Documentation** - 800+ lines complete guide

---

## 🎯 **Quick Start**

### **Local Testing (5 phút)**

```bash
# Build với Dockerfile tối ưu
docker build -f Dockerfile.aws -t ai-detection:aws .

# Run
docker run -d -p 8000:8000 \
  -e ENABLE_CAPTIONING=false \
  -e MAX_CONCURRENT_REQUESTS=3 \
  ai-detection:aws

# Test
curl http://localhost:8000/health
```

### **AWS Deployment (30 phút)**

Chi tiết xem: **[`docs/AWS_QUICK_START.md`](./docs/AWS_QUICK_START.md)**

```bash
# 1. Push to ECR
aws ecr create-repository --repository-name ai-detection --region ap-southeast-1
docker push <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest

# 2. Upload model to S3
aws s3 cp models/yolov8s.pt s3://ai-detection-models/models/yolov8s.pt

# 3. Deploy to ECS Fargate (see AWS_QUICK_START.md)
```

---

## 📊 **Performance & Cost**

### **Performance Benchmarks**

| Configuration | Latency | RAM | Throughput |
|---------------|---------|-----|------------|
| YOLOv8 only | 100-300ms | ~1.5GB | 30-50 req/min |
| YOLOv8 + BLIP-2 | 5-10s | ~3-4GB | 6-12 req/min |

### **AWS Cost Estimates**

| Deployment | CPU/RAM | Cost/month |
|------------|---------|------------|
| Fargate (1 task) | 1vCPU, 4GB | ~$35 |
| Fargate (auto-scale 1-3) | 1vCPU, 4GB | ~$50-100 |
| EC2 t3.medium | 2vCPU, 4GB | ~$30 |
| Fargate Spot | 1vCPU, 4GB | ~$10 (70% savings) |

---

## 📚 **Documentation Index**

| Document | Purpose | Lines |
|----------|---------|-------|
| **[AWS_DEPLOYMENT.md](./docs/AWS_DEPLOYMENT.md)** | Complete AWS deployment guide | 800+ |
| **[AWS_QUICK_START.md](./docs/AWS_QUICK_START.md)** | 30-minute quick start | 200+ |
| **[PRODUCTION_READY.md](./docs/PRODUCTION_READY.md)** | Changes checklist | 300+ |
| **[SUMMARY.md](./docs/SUMMARY.md)** | Technical summary | 250+ |

---

## ⚙️ **Environment Variables**

```bash
# Core settings
MODEL_PATH=/app/models/yolov8s.pt
ENABLE_CAPTIONING=false              # Set true for BLIP-2
MAX_CONCURRENT_REQUESTS=3            # Prevent OOM
CORS_ORIGINS=*                       # Restrict in production
PORT=8000

# AWS-specific
S3_MODEL_URI=s3://bucket/models/yolov8s.pt  # Auto-download from S3
```

---

## 🔧 **API Endpoints**

### `GET /health`
```json
{
  "status": "healthy",
  "model_loaded": true,
  "captioning_enabled": false,
  "captioning_available": false
}
```

### `POST /predict/`
```bash
curl -X POST http://localhost:8000/predict/ -F "file=@image.jpg"
```

Response includes:
- `description` (Japanese)
- `yolo_summary`
- `object_count`
- `object_details`
- `processing_time`
- `inference_speed`
- `image_base64`

---

## 🐳 **Docker Images**

### Standard Dockerfile
```bash
docker build -t ai-detection:standard .
```
- Size: ~2GB
- For development

### AWS-Optimized Dockerfile
```bash
docker build -f Dockerfile.aws -t ai-detection:aws .
```
- Size: ~1.2GB (-40%)
- Multi-stage build
- Health check built-in
- Production-ready

---

## 📁 **New Files Created**

```
ai-detection/
├── Dockerfile.aws                   # ✅ Optimized multi-stage build
├── start-with-s3.sh                 # ✅ S3 model download script
└── docs/
    ├── AWS_DEPLOYMENT.md            # ✅ 800+ lines complete guide
    ├── AWS_QUICK_START.md           # ✅ 30-min quick start
    ├── PRODUCTION_READY.md          # ✅ Changes checklist
    ├── SUMMARY.md                   # ✅ Technical summary
    ├── task-definition-quick.json   # ✅ ECS template
    └── README_AWS.md                # ✅ This file
```

---

## ✅ **Production Checklist**

- [x] Health check endpoint
- [x] Structured logging (CloudWatch)
- [x] Request rate limiting
- [x] Timeout configuration (180s)
- [x] BLIP-2 cost optimization
- [x] Multi-stage Docker build
- [x] AWS deployment docs
- [x] Auto-scaling support
- [x] S3 model storage
- [x] Monitoring ready

---

## 🎯 **Recommended Setup for Production**

```yaml
Architecture:
  Load Balancer: ALB (Application Load Balancer)
  Compute: ECS Fargate (1vCPU, 4GB RAM)
  Auto-scaling: 1-5 tasks (CPU-based)
  Model Storage: S3 + download on startup
  Logging: CloudWatch Logs
  Monitoring: CloudWatch Metrics + Alarms

Cost: ~$95/month
  - Fargate (2 tasks): $70
  - ALB: $20
  - S3 + CloudWatch: $5

Performance:
  - Response time: 100-300ms
  - Concurrent users: 10-20
  - Throughput: 30-50 requests/min
```

---

## 🚨 **Troubleshooting**

### Container won't start
```bash
aws logs tail /ecs/ai-detection --follow --region ap-southeast-1
```

### Slow predictions
- Disable BLIP-2: `ENABLE_CAPTIONING=false`
- Increase CPU/memory
- Enable auto-scaling

### 503 Service Unavailable
- Check ECS service status
- Check ALB target health
- Verify security groups

**Full guide:** [`docs/AWS_DEPLOYMENT.md#troubleshooting`](./docs/AWS_DEPLOYMENT.md#troubleshooting)

---

## 📞 **Support**

- **GitHub Issues:** [MrCoconut203/main/issues](https://github.com/MrCoconut203/main/issues)
- **Full Documentation:** [`docs/`](./docs/)
- **AWS Guide:** [`docs/AWS_DEPLOYMENT.md`](./docs/AWS_DEPLOYMENT.md)

---

**🎉 Ready for AWS Production Deployment!**

Start here: [`docs/AWS_QUICK_START.md`](./docs/AWS_QUICK_START.md)
