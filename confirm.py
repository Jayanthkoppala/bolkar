import json, requests
KEY=[l.split('=',1)[1].strip() for l in open('.env') if l.startswith('ASSEMBLYAI_API_KEY')][0]
URL="https://dictation.assemblyai.com/transcribe"
for i in range(3):
    r=requests.post(URL,headers={"Authorization":KEY},
        files={"audio":("inject.wav",open("inject.wav","rb"),"audio/wav")},timeout=90)
    j=r.json()
    print(f"run{i+1}: rewrite={j.get('llm_response')!r}  session={j.get('session_id')}")
