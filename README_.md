Private note:

```
# opencode instance, remember to check mount
cd ~/Repos/Workbook
docker compose up opencode

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
