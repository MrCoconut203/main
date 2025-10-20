# Hướng dẫn đưa project lên GitHub và host (frontend + backend)

Tài liệu này hướng dẫn từng bước để đưa repository `ai-detection` lên GitHub, host frontend bằng GitHub Pages và triển khai backend (FastAPI + YOLO) bằng Docker. Mình cũng thêm lựa chọn dùng GitHub Container Registry (GHCR) và deploy lên VPS/Render/Railway.

Yêu cầu trước khi bắt đầu:
- Một tài khoản GitHub.
- `git` và (tùy chọn) `gh` CLI cài trên máy dev.
- (Nếu deploy trên server) SSH access tới server hoặc tài khoản trên Render/Railway.

---

## 1) Init repo cục bộ & đẩy lên GitHub

1. Kiểm tra/gắn kết git trong thư mục `d:\project` (nếu chưa init):

```powershell
Set-Location D:\project
git init
git add .
git commit -m "Initial commit"
```

2. Tạo repo mới trên GitHub (2 cách):

- Dùng `gh` CLI (nếu đã cài và đăng nhập):

```powershell
gh repo create <your-username>/<repo-name> --public --source=. --remote=origin
git push -u origin main
```

- Hoặc tạo thủ công trên github.com và rồi add remote:

```powershell
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

3. (Tuỳ chọn) Tạo branch cho deployment: `git checkout -b deploy` và push.

---

## 2) Host frontend bằng GitHub Pages

Repo có thư mục `frontend/` tĩnh (index.html). Bạn có thể serve nó bằng GitHub Pages:

1. Tạo branch `gh-pages` (nơi chứa static build):

```powershell
# ở trong repo root
git checkout --orphan gh-pages
git --work-tree=frontend add --all
git --git-dir=.git commit -m "Deploy frontend to GitHub Pages"
git push origin gh-pages --force
```

2. Hoặc tự động deploy bằng GitHub Actions: bạn có thể thêm action để copy `frontend` vào branch `gh-pages` mỗi khi `main` push. (Mình không thêm action ở đây nhưng có thể nếu bạn muốn.)

3. Bật GitHub Pages trong Settings -> Pages: chọn branch `gh-pages` và folder `/`.

Trang sẽ có URL: `https://<your-username>.github.io/<repo-name>/`.

---

## 3) Build Docker image và push lên GitHub Container Registry (GHCR)

1. Tạo PAT (Personal Access Token) có quyền `write:packages` hoặc dùng `GITHUB_TOKEN` trong Actions.

2. Local build & push (tạm thời):

```powershell
# build image
docker build -t ghcr.io/<your-username>/<repo-name>:latest -f ai-detection/Dockerfile ai-detection/
# login
echo <YOUR_GITHUB_PAT> | docker login ghcr.io -u <your-username> --password-stdin
# push
docker push ghcr.io/<your-username>/<repo-name>:latest
```

3. Mình cung cấp GitHub Actions mẫu phía dưới để tự động build & push khi có tag hoặc push vào `main`.

---

## 4) Triển khai backend (lựa chọn)

Lựa chọn A — Deploy lên VPS bằng Docker Compose (nhanh & đơn giản):

1. Trên server (Ubuntu), cài Docker & docker compose (xem README chính để chi tiết).
2. Clone repo vào server: `git clone https://github.com/<user>/<repo>.git` và `cd repo/ai-detection`.
3. Copy model tới `../models/yolov8s.pt` (root repository `models/`), hoặc mount nơi lưu model.
4. Chạy:

```bash
# build và chạy
sudo docker compose up --build -d
```

5. Kiểm tra `curl http://<server-ip>:8000/health`.

Lựa chọn B — Dùng Render / Railway (PaaS) để deploy container:

1. Push image lên GHCR (bước 3).
2. Trong Render/Railway, tạo service từ Docker image: sử dụng image `ghcr.io/<user>/<repo>:latest` và set env vars (MODEL_PATH, CORS_ORIGINS).

Lựa chọn C — GitHub Actions + SSH deploy (tự động deploy khi push):

1. Tạo secret `DEPLOY_SSH_KEY` trên repo chứa private key dùng để SSH vào server.
2. Thêm workflow để build image, rsync code hoặc chạy ssh to run `docker compose pull && docker compose up -d`.

---

## 5) GitHub Actions sample (build & push to GHCR)

Tạo file `.github/workflows/docker-publish.yml`:

```yaml
name: Build and Push Docker image

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Log in to GHCR
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: ./ai-detection
        file: ./ai-detection/Dockerfile
        push: true
        tags: ghcr.io/${{ github.repository_owner }}/${{ github.event.repository.name }}:latest
```

## 6) Đặt biến môi trường và secrets
- Trên GitHub repo -> Settings -> Secrets, thêm secrets nếu dùng GHCR login bằng PAT, hoặc `DEPLOY_SSH_KEY` cho SSH deploy.

---

Kết luận
- Bạn có thể host frontend miễn phí bằng GitHub Pages.
- Backend cần Docker; bạn có thể host trên VPS (Docker Compose) hoặc PaaS (Render, Railway). GitHub Actions có thể tự động build/publish image.

Muốn mình làm tiếp điều gì?
- Mình có thể tạo workflow file `.github/workflows/docker-publish.yml` trong repo (mình đang sẵn sàng thêm). 
- Mình có thể tạo script deploy SSH mẫu hoặc file `README_deploy.md` chi tiết hơn cho VPS.
