စီမံကိန်း – YOLOv8 + FastAPI နဲ့ အရာဝတ္ထုဖော်ထုတ်ခြင်း

ဒီအက်ပလီကေးရှင်းဟာ ပုံများထဲမှာ YOLOv8 မော်ဒယ်ကို အသုံးပြုပြီး အရာဝတ္ထုဖော်ထုတ်နိုင်တဲ့ API တစ်ခု ပေးစွမ်းတယ်။ Frontend က HTML/JS ဖြင့်ပြုလုပ်ထားတဲ့ SPA ဆန်းရှင်းမှုဖြစ်ပြီး backend သည် FastAPI စနစ်ဖြင့် app/ ထဲမှာရှိတယ်။

ဒီစာတမ်းထဲမှာ ဒီအက်ပလီကေးရှင်းကို ဘယ်လိုအတိုင်း ထည့်သုံးရမလဲဆိုတာကို Docker နဲ့ (deploy လုပ်ဖို့အတွက် အကြံပြု) နှင့် Python virtualenv ဖြင့် (ဖွံ့ဖြိုးရေးအတွက် / ဖျော်ဖြေရေးအတွက်) ဆိုပြီး နှစ်ဖက်လမ်းကြောင်း ဖော်ပြထားတယ်။

အဓိက ဖွဲ့စည်းပုံ

app/ — FastAPI ရဲ့ source code (entry point: app/main.py)

models/ — မော်ဒယ် yolov8s.pt ကို ထည့်သွင်းထားပြီး inference အသုံးပြုရန်လိုအပ်တယ်။

frontend/ — SPA static ဖိုင်တွေ

deploy/ — nginx / reverse proxy configuration, docker-compose စသည်တို့

requirements.txt, constraints.txt — Python dependencies တွေ (မှတ်ချက်: constraints.txt ထဲမှာ numpy<2 ဆိုတဲ့ ကန့်သတ်ချက် ရှိတယ်)

နည်းလမ်း ၁ — Docker ဖြင့် တင်သွင်းခြင်း (Production / Render / Cloud)

အားသာချက်များ: ပတ်ဝန်းကျင်တူညီမှုရှိ၊ deployment လုပ်ရတာလွယ်ကူ၊ scale ပေးရလ mudah. staging/production အတွက် recommend လုပ်ပါတယ်။

၁) Image ကို build လုပ်ခြင်း (PowerShell မှ):

# Dockerfile ရှိတဲ့ folder (ai-detection) မှ run လုပ်ပါ
docker build -t your-registry/ai-detection:latest .


၂) စမ်းသပ်ဖို့လ local container run မည်:

# PORT ကို set လုပ်ပါ (image ထဲမှာ uvicorn မှတ်သားထားတဲ့ PORT ကိုဖတ်မည်)
$env:PORT = '8000'
docker run --rm -e PORT=8000 -p 8000:8000 your-registry/ai-detection:latest


၃) docker-compose သုံးမည် (repo ထဲမှာ docker-compose.yml ရှိလျှင်):

docker compose up --build


၄) Image ကို registry (Docker Hub / GHCR စသည်) ထဲသို့ push လုပ်ခြင်း:

docker tag your-registry/ai-detection:latest yourhub/ai-detection:1.0.0
docker push yourhub/ai-detection:1.0.0


အရေးကြီး မှတ်ချက်များ:

PaaS များ (ဥပမာ Render ကဲ့သို့သော) က PORT ဆိုတဲ့ environment variable ပေးတတ်သည် — အက်ပလီကေးရှင်းသည် ထို $PORT အပေါ် bind ဖြစ်မှရမည်။ Repo ထဲရှိ start.sh script မှ variable ကိုဖတ်ပါတယ်။ သင့် platform မှာ variable သတ်မှတ်ထားမှ အလုပ်လုပ်မည်။

Torch သည် အများကြီးသော package ဖြစ်သည်။ Image build လုပ်စဉ် wheel များ download လုပ်ခြင်းသည် network မတည်ငြိမ်လျှင် နှေးကွေးခြင်းဖြစ်နိုင် သို့မဟုတ် မအောင်မြင်နိုင်သည်။ build / install torch တွင် ပြဿနာများရှိပါက —

wheel များကို ကြိုတင် download လုပ်ပြီး build context ထဲ ထည့်ပါ၊ သို့မဟုတ်

torch wheel ပါသော base image ကို အသုံးပြုပါ၊ သို့မဟုတ်

CI / server စနစ် သို့မဟုတ် network တည်ငြိမ်သော စနစ်တွင် build လုပ်ပါ။

NumPy ABI mismatch အမှားတွေ့လျှင် (ဥပမာ: “A module compiled using NumPy 1.x cannot be run in NumPy 2.x”), constraints.txt ထဲမှာ numpy<2 ဖြစ်စေပြီး image ကို ပြန် build လုပ်ပါ။

နည်းလမ်း ၂ — local development virtualenv ဖြင့် (development / debug)

အားသာချက်များ: ပိုရိုးရှင်းသည်၊ code ပြင်ဖို့လွယ်သည်၊ IDE ဖြင့် debugging လုပ်ရသောသူများအတွက် သင့်လျော်သည်။ အားနည်းချက်: inference ပြီးမြောက်စေရန် torch ကဲ့သို့ package များ install လုပ်ရရန်လိုအပ်နိုင်သည်။

၁) virtualenv ပြုလုပ်ပြီး အက်မသုံးခြင်း (PowerShell):

cd path\to\ai-detection
python -m venv .venv
# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1
# PowerShell script တွင် execution block ဖြစ်ပါက - 
# Admin ခွင့်ဖြင့် PowerShell ကိုဖွင့်ပြီး run လုပ်ပါ:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned


၂) dependencies များ install လုပ်ခြင်း:

pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt


၃) PORT ကို သတ်ပြီး server ကို run လုပ်ခြင်း (ဥပမာ PORT=8000):

$env:PORT = '8000'
uvicorn app.main:app --host 0.0.0.0 --port $env:PORT --reload


၄) browser ဖြင့် စမ်းသပ်ရန်: http://localhost:8000/ ကိုဖွင့်ကြည့်ပါ။

local development မှတ်ချက်များ:

torch ကဲ့သို့ packages မူလတန်းအလေးချိန်များကို မinstall လုပ်ချင်ပါက inference ကို mock လုပ်နိုင်သည်၊ သို့မဟုတ် unit tests များသာ run လုပ်ရမည်။ သို့မဟုတ် אנו Docker ကို အသုံးပြုနိုင်သည် inference ဖြစ်စေလိုပါက။

inference run မည်ဆိုပါက models/yolov8s.pt ဖိုင်သည် models/ folder ထဲမှာ ရှိနေသင့်သည်။

Endpoints & Health Check

GET /health — health check endpoint

POST /predict/ — inference endpoint (file upload form-data)။ frontend ကလည်း ဒါနှင့်လိုက်ဖက်သင့်သည်။

ပြတ်ပြတ်သားသား Troubleshooting

/predict/ မှာ 500 error ဖြစ်လာက NumPy ABI mismatch ဖြစ်နိုင်သည် — စမ်းပြပါ ­pip install 'numpy<2' ပြန် install ပြီး image ကို rebuild လုပ်ပါ။

POST ပြုလုပ်စဉ် 405 error ဖြစ်ပါက reverse-proxy / static route configuration ကို စစ်ဆေးပါ။ Repo ထဲမှာ static route /static သတ်မှတ်ထားပြီး API route မဖုံးမိရန်သေချာစေပါ။

Proxy မှာ 502/504 error ကြုံရပါက worker crash ဖြစ်နေသည် သို့မဟုတ် timeout ဖြစ်နေခြင်း ဖြစ်နိုင်သည်။ Repo တွင် deploy/default.conf ထဲမှာ uvicorn worker-count ကို 1 သတ်ထားပြီး proxy timeout ကို မြှင့်ပေးထားသည်။