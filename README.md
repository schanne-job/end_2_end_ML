# End to End ML Pipeline with MLflow and a prepackaged server via Seldon Core

This README depicts a CLI setup guide for Windows. Things might look different in other platform, but order of setup would be the same. 

### Reproducable experimentation 

First and foremost step is setting up a reproducable ML experimentation system. For that we need, 

1. An ML experiment tracking system - <font color='green'>MLflow</font>
2. A database to store the experimentation tracking system data - <font color='green'>MySQL DB</font>
3. A local object store to keep the artifacts of each experiment -  <font color='green'>MinIO</font>

![Training Flow Chart](images/mlflow_train.png "seldon training")

Here we are setting everything using dockers, so all three above can be actualized as containers.<br/>
In the `mflow` folder, we have a `Dockerfile` which loads neccessary Python modules for mlflow's tracking feature. The MySQL database is stored in `db` and in `minio\buckets` all artifacts of trainings are stored.

- Install Docker for Desktop
- Start from clean state
    - `cmd> docker compose down`
    - `cmd> docker system prune --force --volumes`
    - `cmd> for /F %i in ('docker images -a -q') do docker rmi -f %i`
- `cmd> copy env.txt .env`
- `cmd> docker compose -f docker-start.yml up`

This command should give, 

1. Mlflow dashboard at `localhost:5000` 
2. MinIO dashboard at `localhost:9000`
3. MySQL server at `localhost:3306`

The training script `train.py` is available in `train` folder to simualate the training in MLflow. 

Open Anaconda Prompt with Python 3.8.X
```bash
py38> cd train
py38> pip install -r requirements.txt
py38> python train.py
```

You can see the experiments in `localhost:5000`, metrics and the artifacts in `localhost:9000`. <br/>
The trained model can be copied (or downloaded) into the final model serving container based on seldon-core-microservice:

```bash
cmd> copy .\minio\buckets\mlflow\0\<hash>\artifacts\rf-regressor\model.pkl .\ml-app

cmd> cd .\ml-app
cmd> python download.py
```

Finally start this model serving with docker compose:

```bash
cmd> docker run -p 9002:9000 -it seldon-app
```

Test this app from command line with curl:

```bash
cmd> curl -X POST -H "Content-Type: application/json" -d "{\"data\": { \"ndarray\": [[1,2,3,4,5,6,7,8,9,10,11]]}}" http://127.0.0.1:6000/predict
```

An alternative model is the identity prediction with `MyModel`, replace in `ml-app\Dockerfile`:

```bash
ENV MODEL_NAME Model -> ENV MODEL_NAME MyModel
```

---

Note: For the first time, when you `docker-compose up` there could be errors with MLflow and SQL DB. In that case, stop the terminal and rerun the `up` command. Follow the issue at [here](https://github.com/mlflow/mlflow/issues/1761).

### Deployment in Kubernates

Once we've the trained models which meets the metric criterias, we can deploy it.

Seldon, is an MLOps framework, to package, deploy, monitor and manage thousands of production ML models 

`SeldonDeployment CRD` makes many things easy by doing an abstraction over the entire inference pipeline. Some important features are,

- There are pre-built servers available for subset of ML frameworks. Eg. `Scikit-Learn`.

- A/B Testings, Shadow deployments etc. 

- Integration with explainability, outlier detection frameworks 

- Integration with monitoring, logging, scaling etc. 

- Seldon Core is a cloud native solution built heavily on Kubernates APIs makes it easy for Seldon to run on any cloud provider. On premise providers are also supported. 

![Seldon Core Block Diagram](/images/seldon_core.jpeg "seldon core")

There are some issues going on with latest kubernetes version and Seldon Core. [Follow this thread for the details.](https://github.com/SeldonIO/seldon-core/issues/3618). I used Docker Desktop with used Kubernetes 1.21.5. 

- Install Docker Desktop.
- Enable Kubernetes in the settings. 
- Install Helm `brew install helm` 
- Install `istio`
    ```bash
    curl -L https://istio.io/downloadIstio | sh -
    cd istio-1.11.4
    export PATH=$PWD/bin:$PATH
    istioctl install --set profile=minimal -y
    ```
- Install Seldon Core with Istio, Seldon Analytics with Prometheus and Grafana 
    ```bash 

    kubectl create namespace seldon
    kubectl config set-context $(kubectl config current-context) --namespace=seldon

    kubectl create namespace seldon-system
    
    helm install seldon-core seldon-core-operator --repo https://storage.googleapis.com/seldon-charts --set istio.enabled=true --set istio.gateway="seldon-gateway.istio-system.svc.cluster.local" --set usageMetrics.enabled=true --namespace seldon-system

    kubectl rollout status deploy/seldon-controller-manager -n seldon-system

    helm install seldon-core-analytics seldon-core-analytics --namespace seldon-system --repo https://storage.googleapis.com/seldon-charts --set grafana.adminPassword=password --set grafana.adminUser=admin
    ```
- Setup the `kubernetes-dashboard` if you would like to, from [here.](https://andrewlock.net/running-kubernetes-and-the-dashboard-with-docker-desktop/)
    - `http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/`
- Create deployment 
    ```bash
    kubectl get deploy -n seldon-system
    ```
        
    This should give the following response. 

    ```
    NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
    seldon-controller-manager   1/1     1            1           93s
    ```

- Install Ambassador Ingress (Install just API Gateway inorder to avoid SSL issues in Ambassador Edge Stack)
    ```bash

    helm repo add datawire https://www.getambassador.io
    helm repo update
    helm install ambassador datawire/ambassador \
    --set image.repository=docker.io/datawire/ambassador \
    --set crds.keep=false \
    --set enableAES=false \
    --namespace seldon-system

    kubectl rollout status deployment.apps/ambassador

    ```

- Setup MinIO - Make sure you've allotted 6-8 GB memory at Docker Desktop resource.
    ```bash
    kubectl create ns minio-system 
    
    helm repo add minio https://helm.min.io/
    helm install minio minio/minio --set accessKey=minioadmin \
    --set secretKey=minioadmin --namespace minio-system

    kubectl describe pods --namespace minio-system
    ```

- On another terminal, 
    ```bash

    export POD_NAME=$(kubectl get pods --namespace minio-system -l "release=minio" -o jsonpath="{.items[0].metadata.name}")

    kubectl port-forward $POD_NAME 9000 --namespace minio-system
    ```
- Configure the MinIO client, create bucket and copy the models 

    ```bash
    mc config host add minio-local http://localhost:9000 minioadmin minioadmin

    mc rb --force minio-local/models
    mc mb minio-local/models
    mc cp -r experiments/buckets/mlflow/0/<experiment-id>/artifacts/ minio-local/models/
    
    ```
- Apply the deployment settings 

    ```bash
    kubectl apply -f seldon-rclone-secret.yaml
    kubectl apply -f deploy.yaml
    ```

4. Delete the deployment and pods

    ```bash 
    kubectl delete -f deploy.yaml
    kubectl delete -f secret.yaml
    kubectl delete -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.2.0/aio/deploy/recommended.yaml
    ```

5. Related 

```bash

kubectl get deployments --all-namespaces
kubectl delete --all pods --namespace=seldon-system
kubectl delete --all deployments --namespace=seldon-system
helm uninstall seldon-core --namespace seldon-system

kubectl get service --all-namespaces
kubectl get deploy -l seldon-deployment-id=mlflow -o jsonpath='{.items}'
kubectl logs -n seldon-system -l control-plane=seldon-controller-manager

kubectl get pods --namespace default
kubectl describe po <POD_NAME> --namespace default

kubectl logs mlflow-default-0-rf-regressor-5c99f87f4-hdlwk -c  rf-regressor-model-initializer
kubectl logs mlflow-default-0-rf-regressor-5c99f87f4-hdlwk -c  rf-regressor
```

Reference 

[1] [Alejandro Saucedo's Medium article](https://towardsdatascience.com/a-simple-mlops-pipeline-on-your-local-machine-db9326addf31)

[2] [Adrian Gonzalez's PPT](https://docs.google.com/presentation/d/1QXiOZkd_XNw6PbUalhYDajljKYQjgKczzNncTyLk9uA/)

[3] [Adrian Gonzalez's Talk](https://www.youtube.com/watch?v=M_q0-8JH0Zw)

[4] [A Simple MLOps Pipeline on Your Local Machine](https://towardsdatascience.com/a-simple-mlops-pipeline-on-your-local-machine-db9326addf31)

[5] [MLflow On-Premise Deployment - GitHub](https://github.com/sachua/mlflow-docker-compose)

[6] [SKlearn Prepackaged Server with MinIO](https://docs.seldon.io/projects/seldon-core/en/v1.1.0/examples/minio-sklearn.html)

[7] [Install MinIO in cluster](https://docs.seldon.io/projects/seldon-core/en/latest/examples/minio_setup.html)

[8] [Seldon Core Setup](https://docs.seldon.io/projects/seldon-core/en/latest/examples/seldon_core_setup.html)

[9] [Install MinIO in cluster](https://docs.seldon.io/projects/seldon-core/en/latest/examples/minio_setup.html)

[10] [MLflow v2 protocol elasticnet wine example](https://docs.seldon.io/projects/seldon-core/en/latest/examples/mlflow_v2_protocol_end_to_end.html)

[11] [KFServing works only with Istio](https://deploy.seldon.io/en/v1.4/contents/architecture/gateways/index.html)

[12] [Serve MLFlow Elasticnet Wines Model](https://docs.seldon.io/projects/seldon-core/en/latest/examples/server_examples.html#Serve-MLflow-Elasticnet-Wines-Model)

Issues 

[1] [Issue in "seldon-container-engine" with MLFLOW_SERVER](https://github.com/SeldonIO/seldon-core/issues/1922)

[2] [Deploying custom MLflow model - stuck at "Readiness probe failed"](https://github.com/SeldonIO/seldon-core/issues/3186)
