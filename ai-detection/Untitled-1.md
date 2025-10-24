प्रोजेक्ट: YOLOv8 + FastAPI के साथ ऑब्जेक्ट डिटेक्शन

यह एप्लिकेशन एक API प्रदान करता है जो YOLOv8 मॉडल का उपयोग करके छवियों में ऑब्जेक्ट डिटेक्शन करता है। फ्रंटेंड एक साधारण SPA (HTML/JS) है और बैकएंड FastAPI सेवा है जो app/ में स्थित है।

यह दस्तावेज़ एप्लिकेशन चलाने के दो तरीके बताता है — Docker द्वारा (डिप्लॉयमेंट के लिए अनुशंसित) और Python वर्चुअल वातावरण (virtualenv) द्वारा विकास के लिए।

मुख्य संरचना

app/ — FastAPI स्रोत कोड (एंट्रीपॉइंट: app/main.py)।

models/ — मॉडल yolov8s.pt रखता है (वास्तविक inference के लिए आवश्यक)।

frontend/ — SPA स्टैटिक फाइलें।

deploy/ — nginx / reverse proxy कॉन्फ़िगरेशन, docker-compose इत्यादि।

requirements.txt, constraints.txt — Python dependencies (ध्यान दें: constraints.txt में numpy<2 प्रतिबंध है)।

तरीका 1 — Docker के द्वारा डिप्लॉयमेंट (Production / Render / Cloud)

फ़ायदे: पर्यावरण समान रहता है, डिप्लॉयमेंट और स्केल करना आसान। स्टेजिंग / प्रोडक्शन वातावरण के लिए अनुशंसित।

इमेज बिल्ड करें (PowerShell):

# उस फोल्डर से चलाएं जहाँ Dockerfile है (ai-detection)
docker build -t your-registry/ai-detection:latest .


स्थानीय कंटेनर चलाएँ टेस्ट करने के लिए:

# कंटेनर के लिए PORT सेट करें (image के भीतर uvicorn इस PORT को पढ़ता है)
$env:PORT = '8000'
docker run --rm -e PORT=8000 -p 8000:8000 your-registry/ai-detection:latest


docker-compose का उपयोग करें (यदि repo में docker-compose.yml हो):

docker compose up --build


इमेज को registry (Docker Hub / GHCR आदि) में push करें:

docker tag your-registry/ai-detection:latest yourhub/ai-detection:1.0.0
docker push yourhub/ai-detection:1.0.0


महत्वपूर्ण नोट्स:

कई PaaS (जैसे Render) PORT नामक environment variable देती हैं — एप्लिकेशन को उस $PORT पर bind होना चाहिए। start.sh स्क्रिप्ट repo में इस बात को पढ़ती है। सुनिश्चित करें आपका प्लेटफ़ॉर्म वह variable सेट करता है।

Torch एक बड़ा पैकेज है; इमेज बिल्ड करते वक्त wheel डाउनलोड धीमा हो सकता है या असफल हो सकता है अगर नेटवर्क अस्थिर हो। यदि build या install torch में समस्या आए:

wheel को पहले डाउनलोड करके build context में शामिल करें, या

एक base image उपयोग करें जिसमें torch wheel पहले से हो, या

CI / सर्वर वातावरण में build करें जहाँ नेटवर्क स्थिर है।

अगर NumPy ABI mismatch की समस्या हो (उदाहरण “A module compiled using NumPy 1.x cannot be run in NumPy 2.x”), सुनिश्चित करें कि constraints.txt में numpy<2 है और फिर इमेज को पुनः बिल्ड करें।

तरीका 2 — स्थानीय विकास virtualenv द्वारा (development / debug)

फ़ायदे: हल्का होता है, कोड बदलना आसान, IDE से debug आसान। नुकसान: यदि आप वास्तविक inference चलाना चाहते हैं, तब भारी पैकेज (torch) इंस्टॉल करना पड़ सकता है।

virtualenv बनाएं और एक्टिवेट करें (PowerShell):

cd path\to\ai-detection
python -m venv .venv
# एक्टिवेट (PowerShell)
.\.venv\Scripts\Activate.ps1
# यदि PowerShell स्क्रिप्ट execution blocked हो:
# एडमिन अधिकारों के साथ PowerShell खोलें और चलाएँ:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned


dependencies इंस्टॉल करें:

pip install --upgrade pip
pip install -r requirements.txt -c constraints.txt


PORT सेट करें और सर्वर चलाएँ (उदाहरण के लिए PORT=8000):

$env:PORT = '8000'
uvicorn app.main:app --host 0.0.0.0 --port $env:PORT --reload


ब्राउज़र खोलें और परीक्षण करें: http://localhost:8000/

विकास के लिए नोट्स:

यदि आप torch इंस्टॉल नहीं करना चाहते क्योंकि बहुत भारी है, आप inference को mock कर सकते हैं या केवल unit tests चला सकते हैं; या inference के लिए Docker का उपयोग करें।

सुनिश्चित करें कि मॉडल फ़ाइल models/yolov8s.pt मौजूद हो models/ फोल्डर में यदि आप वास्तविक inference करना चाहते हैं।

Endpoints & हेल्थ चेक

GET /health — हेल्‍थ चेक एन्डपॉइंट।

POST /predict/ — inference एन्डपॉइंट (file upload form-data). फ्रंट-एंड में भी उसके अनुरूप टेस्ट करें।

त्वरित Troubleshooting

यदि /predict/ पर 500 एरर आ रही हो और NumPy ABI mismatch हो: कोशिश करें pip install 'numpy<2' और इमेज को पुनः build करें।

अगर POST करने पर 405 एरर हो रही हो: reverse-proxy / static route कॉन्फ़िगरेशन देखें; repo में static route /static के लिए सेटअप है और सुनिश्चित करें API route overshadow नहीं हो रही है।

502/504 error अगर reverse proxy से आ रही हो: यह हो सकता है कि worker crash हुआ हो या timeout हो रहा हो; repo में uvicorn worker-count एक है और proxy timeout बढ़ाया गया है deploy/default.conf में।