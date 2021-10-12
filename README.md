# End to End ML Pipeline with MLflow and Seldon Core

This README depicts a CLI setup guide in Macbook. Things might look different in other platform, but order of setup would be the same. 

### Setup MLFlow for reproducable experimentation 

- Install `virtualengwrapper` and create new env `mkvirtualenv end_2_end_ml` 
- `workon end_2_end_ml`
- Install `mlflow` and `scikit-learn` 
    - `pip install mlflow scikit-learn`
- Run a couple of experiments with `train.py`
    - `python wine_data/train.py 0.5 0.2`
    - `python wine_data/train.py`
- Check the dashboard in MLFlow UI using `mlflow ui` command

OR 

Just install `MLFLow` and `conda` and run `mlflow run wine_data -P alpha=0.42`

Now we've the models trained, (ignore the performance as of now), these models can be served using MLFlow itself. For this project, I use Seldon.
### Install Seldon Core 

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
- Install Seldon Core, Seldon Analytics with Prometheus and Grafana 
- Install Seldon Core and Ambassodor
    - `kubectl create namespace ambassador || echo "namespace ambassador exists"` 
    - `helm repo add datawire https://www.getambassador.io`
    - `helm install ambassador datawire/ambassador --set image.repository=docker.io/datawire/ambassador --set crds.keep=false --namespace ambassador`
    - `kubectl create namespace seldon-system`
    - `helm install seldon-core seldon-core-operator --repo https://storage.googleapis.com/seldon-charts --set istio.enabled=true --set usageMetrics.enabled=true --namespace seldon-system`
    - `helm install seldon-core-analytics seldon-core-analytics --namespace seldon-system --repo https://storage.googleapis.com/seldon-charts --set grafana.adminPassword=password --set grafana.adminUser=admin`
    - `kubectl get deploy -n seldon-system`
        
        This should give the following response. 

        ```
        NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
        seldon-controller-manager   1/1     1            1           93s
        ```
- You may check the Ambassodor pods as well using `kubectl get po -n ambassador` 


### Training and Experimentation 

![Training Flow Chart](/images/training.png "seldon training")


Since I'm setting up everything offline, MLflow experiment details are stored in a MySQL DB. I use MinIO for simulating the Object Store that stores the artifacts. MLflow will 
store the artifacts in the MinIO. 

In the `experiments` folder, we have a `Dockerfile` which will setup a container that has

1. Training script 
2. Training data 

There are provisions to add test scripts, if required. Another aspect is, the training data is added as a file. In a real setup, it won't be the case. The training data could be streaming
data, or stored in a DB or anything. 

`docker-compose --env-file ./.env up`

To clean slate
    - `docker-compose down`
    - `docker system prune --force --volumes`

3. Deploy the trained models in the pods 

- `kubectl create -f ./serving/model-a-b.yaml` (Imperative, creates a whole new object (previously non-existing / deleted))
- `kubectl apply -f ./serving/model-a-b.yaml` (Declarative, makes incremental changes to an existing object)

4. Delete the deployment and pods

- `kubectl delete -f ./serving/model-a-b.yaml`


Reference 

[1] [Alejandro Saucedo's Medium article](https://towardsdatascience.com/a-simple-mlops-pipeline-on-your-local-machine-db9326addf31)

[2] [Adrian Gonzalez's PPT](https://docs.google.com/presentation/d/1QXiOZkd_XNw6PbUalhYDajljKYQjgKczzNncTyLk9uA/)

[3] [Adrian Gonzalez's Talk](https://www.youtube.com/watch?v=M_q0-8JH0Zw)

[4] [A Simple MLOps Pipeline on Your Local Machine](https://towardsdatascience.com/a-simple-mlops-pipeline-on-your-local-machine-db9326addf31)

[5] [MLflow On-Premise Deployment - GitHub](https://github.com/sachua/mlflow-docker-compose)

