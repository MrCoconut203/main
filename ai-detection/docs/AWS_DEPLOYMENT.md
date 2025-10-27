# 🚀 AWS Deployment Guide - YOLOv8 AI Detection

完全なAWSデプロイメントガイド (Hướng dẫn triển khai AWS chi tiết)

---

## 📋 **Mục lục**

1. [Tổng quan kiến trúc AWS](#tổng-quan-kiến-trúc-aws)
2. [Chuẩn bị trước khi triển khai](#chuẩn-bị-trước-khi-triển-khai)
3. [Phương án 1: AWS ECS Fargate (Khuyến nghị)](#phương-án-1-aws-ecs-fargate)
4. [Phương án 2: AWS EC2](#phương-án-2-aws-ec2)
5. [Phương án 3: AWS App Runner](#phương-án-3-aws-app-runner)
6. [Cấu hình nâng cao](#cấu-hình-nâng-cao)
7. [Monitoring & Logging](#monitoring--logging)
8. [Tối ưu chi phí](#tối-ưu-chi-phí)
9. [Troubleshooting](#troubleshooting)

---

## 🏗️ **Tổng quan kiến trúc AWS**

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Route53 │ (Optional: Custom domain)
                    └────┬────┘
                         │
                    ┌────▼────────┐
                    │     ALB     │ (Application Load Balancer)
                    │  (HTTPS)    │
                    └─┬─────────┬─┘
                      │         │
           ┌──────────▼─┐   ┌──▼──────────┐
           │  ECS Task  │   │  ECS Task   │ (Auto-scaling)
           │ (Fargate)  │   │ (Fargate)   │
           └──────┬─────┘   └──────┬──────┘
                  │                │
                  └────────┬───────┘
                           │
              ┌────────────▼─────────────┐
              │         EFS/S3           │ (Model storage)
              │    yolov8s.pt (~22MB)    │
              └──────────────────────────┘
```

**Các thành phần:**
- **ALB**: Load balancer cho HTTPS, health checks
- **ECS Fargate**: Chạy container không cần quản lý server
- **S3**: Lưu trữ model files, backup
- **CloudWatch**: Logging và monitoring
- **Auto Scaling**: Tự động scale theo CPU/memory

---

## 🔧 **Chuẩn bị trước khi triển khai**

### 1. **Yêu cầu hệ thống**

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
|------------|-------------------|-------------|
| vCPU | 1 vCPU | 2 vCPU |
| RAM | 2GB | 4GB (nếu bật BLIP-2: 6GB) |
| Storage | 2GB | 5GB |
| Network | 1 Mbps | 10 Mbps |

### 2. **Cài đặt AWS CLI**

```bash
# Windows (PowerShell)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Cấu hình AWS CLI:**

```bash
aws configure
# AWS Access Key ID: [Nhập key của bạn]
# AWS Secret Access Key: [Nhập secret key]
# Default region name: ap-southeast-1  # Singapore (gần VN nhất)
# Default output format: json
```

### 3. **Build và push Docker image lên ECR**

```bash
# 1. Tạo ECR repository
aws ecr create-repository --repository-name ai-detection --region ap-southeast-1

# 2. Get login token
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

# 3. Build image với Dockerfile.aws
cd d:\project\ai-detection
docker build -f Dockerfile.aws -t ai-detection:latest .

# 4. Tag image
docker tag ai-detection:latest <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest

# 5. Push lên ECR
docker push <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest
```

> **Lưu ý:** Thay `<ACCOUNT_ID>` bằng AWS Account ID của bạn (12 số)

### 4. **Upload model lên S3**

```bash
# 1. Tạo S3 bucket
aws s3 mb s3://ai-detection-models --region ap-southeast-1

# 2. Upload YOLOv8 model
aws s3 cp d:\project\ai-detection\models\yolov8s.pt s3://ai-detection-models/models/yolov8s.pt

# 3. Verify
aws s3 ls s3://ai-detection-models/models/
```

---

## 🐳 **Phương án 1: AWS ECS Fargate** (Khuyến nghị)

### **Ưu điểm:**
- ✅ Không cần quản lý server
- ✅ Auto-scaling tự động
- ✅ Tích hợp ALB, CloudWatch
- ✅ Pay-as-you-go

### **Bước 1: Tạo ECS Cluster**

```bash
aws ecs create-cluster --cluster-name ai-detection-cluster --region ap-southeast-1
```

### **Bước 2: Tạo Task Definition**

Tạo file `task-definition.json`:

```json
{
  "family": "ai-detection-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "ai-detection",
      "image": "<ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MODEL_PATH",
          "value": "/app/models/yolov8s.pt"
        },
        {
          "name": "ENABLE_CAPTIONING",
          "value": "false"
        },
        {
          "name": "MAX_CONCURRENT_REQUESTS",
          "value": "3"
        },
        {
          "name": "CORS_ORIGINS",
          "value": "*"
        },
        {
          "name": "S3_MODEL_URI",
          "value": "s3://ai-detection-models/models/yolov8s.pt"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-detection",
          "awslogs-region": "ap-southeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**Register task definition:**

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json --region ap-southeast-1
```

### **Bước 3: Tạo Application Load Balancer**

```bash
# 1. Tạo ALB
aws elbv2 create-load-balancer \
  --name ai-detection-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --region ap-southeast-1

# 2. Tạo Target Group
aws elbv2 create-target-group \
  --name ai-detection-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --region ap-southeast-1

# 3. Tạo Listener
aws elbv2 create-listener \
  --load-balancer-arn <ALB_ARN> \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=<TARGET_GROUP_ARN> \
  --region ap-southeast-1
```

### **Bước 4: Tạo ECS Service với Auto Scaling**

```bash
aws ecs create-service \
  --cluster ai-detection-cluster \
  --service-name ai-detection-service \
  --task-definition ai-detection-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=<TARGET_GROUP_ARN>,containerName=ai-detection,containerPort=8000 \
  --region ap-southeast-1
```

### **Bước 5: Cấu hình Auto Scaling**

```bash
# 1. Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ai-detection-cluster/ai-detection-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10 \
  --region ap-southeast-1

# 2. Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/ai-detection-cluster/ai-detection-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json \
  --region ap-southeast-1
```

**scaling-policy.json:**

```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

### **Bước 6: Kiểm tra deployment**

```bash
# 1. Get ALB DNS
aws elbv2 describe-load-balancers --names ai-detection-alb --query 'LoadBalancers[0].DNSName' --output text

# 2. Test health check
curl http://<ALB_DNS>/health

# 3. Test prediction
curl -X POST http://<ALB_DNS>/predict/ \
  -F "file=@test_image.jpg"
```

---

## 💻 **Phương án 2: AWS EC2**

### **Ưu điểm:**
- ✅ Full control
- ✅ Có thể dùng GPU (g4dn.xlarge)
- ✅ Phù hợp với BLIP-2

### **Bước 1: Launch EC2 Instance**

```bash
# 1. Create key pair
aws ec2 create-key-pair --key-name ai-detection-key --query 'KeyMaterial' --output text > ai-detection-key.pem
chmod 400 ai-detection-key.pem

# 2. Launch instance (Ubuntu 22.04, t3.medium)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name ai-detection-key \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ai-detection}]' \
  --region ap-southeast-1
```

### **Bước 2: SSH và cài đặt Docker**

```bash
# SSH vào EC2
ssh -i ai-detection-key.pem ubuntu@<EC2_PUBLIC_IP>

# Cài đặt Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Logout và login lại để apply docker group
exit
ssh -i ai-detection-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### **Bước 3: Pull và chạy container**

```bash
# 1. Login ECR
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

# 2. Pull image
docker pull <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest

# 3. Run container
docker run -d \
  --name ai-detection \
  -p 80:8000 \
  -e MODEL_PATH=/app/models/yolov8s.pt \
  -e ENABLE_CAPTIONING=false \
  -e MAX_CONCURRENT_REQUESTS=3 \
  -e S3_MODEL_URI=s3://ai-detection-models/models/yolov8s.pt \
  --restart unless-stopped \
  <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest

# 4. Kiểm tra logs
docker logs -f ai-detection
```

### **Bước 4: Cấu hình HTTPS với Let's Encrypt** (Optional)

```bash
# Cài đặt Nginx + Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Cấu hình Nginx reverse proxy
sudo nano /etc/nginx/sites-available/ai-detection

# Nội dung:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 180s;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/ai-detection /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## 🚀 **Phương án 3: AWS App Runner** (Đơn giản nhất)

### **Ưu điểm:**
- ✅ Cực kỳ đơn giản
- ✅ Auto-scaling tự động
- ✅ HTTPS built-in

### **Bước 1: Tạo App Runner service**

```bash
aws apprunner create-service \
  --service-name ai-detection \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/ai-detection:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "ENABLE_CAPTIONING": "false",
          "MAX_CONCURRENT_REQUESTS": "3"
        }
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1024",
    "Memory": "4096"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 30,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 3
  }' \
  --region ap-southeast-1
```

### **Bước 2: Kiểm tra URL**

```bash
aws apprunner describe-service \
  --service-arn <SERVICE_ARN> \
  --query 'Service.ServiceUrl' \
  --output text
```

---

## ⚙️ **Cấu hình nâng cao**

### **1. Bật BLIP-2 Image Captioning**

```bash
# Trong task definition hoặc docker run, thêm:
-e ENABLE_CAPTIONING=true

# ⚠️ Lưu ý: Cần tăng RAM lên 6GB
```

### **2. Custom CORS Origins**

```bash
-e CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

### **3. Tăng concurrent requests**

```bash
-e MAX_CONCURRENT_REQUESTS=5

# ⚠️ Tăng RAM tương ứng (mỗi request ~500MB)
```

### **4. Sử dụng CloudFront CDN**

```bash
# 1. Tạo CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name <ALB_DNS> \
  --default-cache-behavior '{
    "TargetOriginId": "ai-detection-alb",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
      "Quantity": 7
    },
    "ForwardedValues": {
      "QueryString": true,
      "Headers": {
        "Items": ["*"],
        "Quantity": 1
      }
    }
  }'
```

---

## 📊 **Monitoring & Logging**

### **1. CloudWatch Logs**

```bash
# Xem logs real-time
aws logs tail /ecs/ai-detection --follow --region ap-southeast-1

# Filter errors
aws logs filter-log-events \
  --log-group-name /ecs/ai-detection \
  --filter-pattern "ERROR" \
  --region ap-southeast-1
```

### **2. CloudWatch Metrics**

```python
# Tạo custom metrics trong code (thêm vào main.py)
import boto3
cloudwatch = boto3.client('cloudwatch', region_name='ap-southeast-1')

def log_prediction_metric(processing_time):
    cloudwatch.put_metric_data(
        Namespace='AIDetection',
        MetricData=[
            {
                'MetricName': 'PredictionTime',
                'Value': processing_time,
                'Unit': 'Seconds'
            }
        ]
    )
```

### **3. Tạo CloudWatch Dashboard**

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ai-detection-dashboard \
  --dashboard-body file://dashboard.json
```

---

## 💰 **Tối ưu chi phí**

### **Bảng so sánh chi phí** (ap-southeast-1 region)

| Phương án | CPU/RAM | Chi phí/tháng | Khuyến nghị |
|-----------|---------|---------------|-------------|
| **Fargate (1 task)** | 1vCPU, 4GB | ~$35 | Sản xuất |
| **Fargate (auto-scale 1-3)** | 1vCPU, 4GB | ~$50-100 | High traffic |
| **EC2 t3.medium** | 2vCPU, 4GB | ~$30 | Ổn định |
| **App Runner** | 1vCPU, 4GB | ~$40 | Đơn giản |
| **EC2 Spot** | 2vCPU, 4GB | ~$10 | Dev/Test |

### **Chiến lược tiết kiệm:**

1. **Tắt BLIP-2**: Giảm RAM từ 6GB → 4GB (~30% cost)
2. **Dùng Fargate Spot**: Giảm 70% chi phí Fargate
3. **Schedule scaling**: Scale down vào ban đêm
4. **S3 Intelligent-Tiering**: Tự động chuyển model sang storage rẻ hơn

```bash
# Enable Fargate Spot
aws ecs update-service \
  --cluster ai-detection-cluster \
  --service ai-detection-service \
  --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1 \
  --region ap-southeast-1
```

---

## 🔧 **Troubleshooting**

### **1. Container không start**

```bash
# Check logs
aws logs tail /ecs/ai-detection --follow

# Common issues:
# - Model không download được → Check IAM role có quyền S3
# - OOM → Tăng memory trong task definition
# - Health check fail → Check /health endpoint
```

### **2. Slow response time**

```bash
# 1. Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=ai-detection-service \
  --start-time 2025-10-27T00:00:00Z \
  --end-time 2025-10-27T23:59:59Z \
  --period 3600 \
  --statistics Average

# Solutions:
# - Tăng CPU/memory
# - Tăng MAX_CONCURRENT_REQUESTS
# - Enable auto-scaling
```

### **3. 503 Service Unavailable**

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster ai-detection-cluster \
  --services ai-detection-service

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN>

# Solutions:
# - Check health check path: /health
# - Increase health check timeout
# - Check security groups allow ALB → ECS traffic
```

---

## 📚 **Tài liệu tham khảo**

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)

---

## 🎯 **Khuyến nghị cuối cùng**

**Cho môi trường Production:**
1. ✅ Dùng **ECS Fargate** với ALB
2. ✅ Bật **Auto Scaling** (1-5 tasks)
3. ✅ **Tắt BLIP-2** mặc định (tiết kiệm 30% chi phí)
4. ✅ Lưu model trên **S3** + CloudFront
5. ✅ Enable **CloudWatch Logs** + **Alarms**
6. ✅ Dùng **CloudFront CDN** cho frontend
7. ✅ Setup **HTTPS** với ACM certificate

**Chi phí ước tính:**
- Fargate (2 tasks): ~$70/tháng
- ALB: ~$20/tháng
- S3 + CloudWatch: ~$5/tháng
- **Tổng: ~$95/tháng**

---

**Liên hệ hỗ trợ:** [GitHub Issues](https://github.com/MrCoconut203/main/issues)
