```
docker build -t seldon-app .
docker run -p 9002:9000 -it seldon-app
```

python tests.py

curl -X POST -H "Content-Type: application/json" -d "{\"data\": { \"ndarray\": [[1,2,3,4,5,6,7]]}}" http://127.0.0.1:9002/predict