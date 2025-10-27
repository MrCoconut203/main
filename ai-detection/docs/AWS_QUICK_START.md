# ⚡ AWS Quick Start - 30 phút Deploy lên Production

Hướng dẫn nhanh triển khai lên AWS ECS Fargate (khuyến nghị cho production)

---

## 🚀 **Chuẩn bị (5 phút)**

### 1. Install AWS CLI

```powershell
# Windows PowerShell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

### 2. Configure AWS

```bash
aws configure
# Region: ap-southeast-1 (Singapore - gần VN nhất)
```

---

## 📦 **Deploy lên AWS (25 phút)**

### **Bước 1: Push Docker image lên ECR** (10 phút)

```powershell
# 1. Tạo repository
aws ecr create-repository --repository-name ai-detection --region ap-southeast-1

# 2. Get account ID
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# 3. Login Docker
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com"

# 4. Build image
cd d:\project\ai-detection
docker build -f Dockerfile.aws -t ai-detection:latest .

# 5. Tag & Push
docker tag ai-detection:latest "$ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest"
docker push "$ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest"
```

### **Bước 2: Upload model lên S3** (2 phút)

```powershell
# Tạo bucket và upload
aws s3 mb s3://ai-detection-models-$ACCOUNT_ID --region ap-southeast-1
aws s3 cp models\yolov8s.pt s3://ai-detection-models-$ACCOUNT_ID/models/yolov8s.pt
```

### **Bước 3: Deploy lên ECS Fargate** (5 phút)

```powershell
# 1. Tạo cluster
aws ecs create-cluster --cluster-name ai-detection --region ap-southeast-1

# 2. Register task (copy task-definition-quick.json từ docs/)
aws ecs register-task-definition --cli-input-json file://task-definition-quick.json --region ap-southeast-1

# 3. Create service
aws ecs create-service `
  --cluster ai-detection `
  --service-name ai-detection-svc `
  --task-definition ai-detection-task `
  --desired-count 1 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" `
  --region ap-southeast-1
```

### **Bước 4: Lấy public IP và test** (3 phút)

```powershell
# Get task public IP
$TASK_ARN = (aws ecs list-tasks --cluster ai-detection --region ap-southeast-1 --query 'taskArns[0]' --output text)
$TASK_DETAILS = (aws ecs describe-tasks --cluster ai-detection --tasks $TASK_ARN --region ap-southeast-1 | ConvertFrom-Json)
$PUBLIC_IP = $TASK_DETAILS.tasks[0].attachments[0].details | Where-Object {$_.name -eq "networkInterfaceId"} | Select-Object -ExpandProperty value

# Test
curl "http://$PUBLIC_IP:8000/health"
```

### **Bước 5: Setup ALB (Optional, cho production)** (5 phút)

```bash
# Xem hướng dẫn chi tiết trong AWS_DEPLOYMENT.md
# ALB cho phép:
# - HTTPS
# - Auto-scaling
# - Health checks
```

---

## ✅ **Hoàn tất!**

API của bạn đã chạy trên AWS Fargate: `http://<PUBLIC_IP>:8000`

**Endpoints:**
- Health check: `GET /health`
- Prediction: `POST /predict/`
- Frontend: `GET /`

---

## 💰 **Chi phí ước tính**

| Cấu hình | Chi phí/tháng |
|----------|---------------|
| 1 Fargate task (1vCPU, 4GB) | ~$35 |
| S3 storage (~22MB) | ~$0.01 |
| Data transfer (100GB) | ~$9 |
| **Tổng** | **~$44/tháng** |

**Tiết kiệm:**
- BLIP-2 mặc định TẮT → tiết kiệm 30%
- Dùng Fargate Spot → giảm thêm 70%

---

## 🔧 **Troubleshooting**

### Container không start
```bash
aws logs tail /ecs/ai-detection --follow --region ap-southeast-1
```

### Chưa có subnet/security group
```bash
# Get default VPC
aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text

# Get subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<VPC_ID>" --query "Subnets[*].SubnetId" --output text

# Create security group
aws ec2 create-security-group --group-name ai-detection-sg --description "AI Detection SG" --vpc-id <VPC_ID>
aws ec2 authorize-security-group-ingress --group-id <SG_ID> --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

---

## 📚 **Next Steps**

1. ✅ Setup custom domain với Route53
2. ✅ Enable HTTPS với ACM certificate
3. ✅ Add CloudFront CDN
4. ✅ Enable auto-scaling
5. ✅ Setup CloudWatch alarms

Xem chi tiết trong: [`AWS_DEPLOYMENT.md`](./AWS_DEPLOYMENT.md)
