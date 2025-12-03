# 🚀 GKE Deployment Commands

Complete command list for deploying Mother of Bots to Google Kubernetes Engine.

## Prerequisites

- Project ID: `motherofbots`
- Region: `us-central1`
- Zone: `us-central1-a`
- Service Account: `mob-653@motherofbots.iam.gserviceaccount.com`

---

## Step 1: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create docker-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Mother of Bots"
```

---

## Step 2: Configure Docker Authentication

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

---

## Step 3: Build and Push Backend Image

```bash
# From project root directory
docker build -f k8s/Dockerfile.backend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest .

docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest
```

---

## Step 4: Build and Push Frontend Image

```bash
# From project root directory
docker build -f k8s/Dockerfile.frontend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest .

docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest
```

---

## Step 5: Create GKE Cluster

```bash
gcloud container clusters create mother-of-bots-cluster \
    --project=motherofbots \
    --zone=us-central1-a \
    --num-nodes=2 \
    --machine-type=e2-standard-4 \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=5 \
    --enable-autorepair \
    --enable-autoupgrade \
    --workload-pool=motherofbots.svc.id.goog \
    --addons=HorizontalPodAutoscaling,HttpLoadBalancing
```

---

## Step 6: Get Cluster Credentials

```bash
gcloud container clusters get-credentials mother-of-bots-cluster --zone=us-central1-a
```

---

## Step 7: Verify Cluster Connection

```bash
kubectl get nodes
```

---

## Step 8: Deploy to Kubernetes

```bash
# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml

# Apply Service Accounts
kubectl apply -f k8s/service-account.yaml

# Apply Backend Deployment
kubectl apply -f k8s/backend-deployment.yaml

# Apply Frontend Deployment
kubectl apply -f k8s/frontend-deployment.yaml
```

---

## Step 9: Verify Deployment

```bash
# Check deployments
kubectl get deployments

# Check pods
kubectl get pods

# Check services
kubectl get services

# View backend logs
kubectl logs -f deployment/backend-deployment

# View frontend logs
kubectl logs -f deployment/frontend-deployment
```

---

## Step 10: Get External IP

```bash
# Get LoadBalancer external IP
kubectl get service frontend-service

# Or watch until IP is assigned
kubectl get service frontend-service -w
```

---

## 🔄 Update Deployment Commands

### Rebuild and Redeploy

```bash
# 1. Rebuild and push backend
docker build -f k8s/Dockerfile.backend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest .
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest

# 2. Rebuild and push frontend
docker build -f k8s/Dockerfile.frontend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest .
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest

# 3. Restart deployments
kubectl rollout restart deployment/backend-deployment
kubectl rollout restart deployment/frontend-deployment

# 4. Check rollout status
kubectl rollout status deployment/backend-deployment
kubectl rollout status deployment/frontend-deployment
```

---

## 📊 Monitoring Commands

```bash
# Get all resources
kubectl get all

# Describe deployment
kubectl describe deployment/backend-deployment
kubectl describe deployment/frontend-deployment

# Describe pod
kubectl describe pod POD_NAME

# Get events
kubectl get events --sort-by='.lastTimestamp'

# Check pod status
kubectl get pods -o wide

# View pod logs
kubectl logs POD_NAME
kubectl logs -f POD_NAME  # Follow logs
```

---

## 🔧 Troubleshooting Commands

```bash
# Execute command in pod
kubectl exec -it deployment/backend-deployment -- /bin/bash

# Port forward for local testing
kubectl port-forward service/backend-service 5000:5000
kubectl port-forward service/frontend-service 3000:80

# Check pod logs with errors
kubectl logs deployment/backend-deployment --previous

# Scale deployment
kubectl scale deployment/backend-deployment --replicas=3

# Rollback deployment
kubectl rollout undo deployment/backend-deployment
kubectl rollout undo deployment/frontend-deployment

# Check resource usage
kubectl top pods
kubectl top nodes
```

---

## 🧹 Cleanup Commands

```bash
# Delete all deployments and services
kubectl delete -f k8s/backend-deployment.yaml
kubectl delete -f k8s/frontend-deployment.yaml
kubectl delete -f k8s/service-account.yaml
kubectl delete -f k8s/configmap.yaml

# Delete cluster
gcloud container clusters delete mother-of-bots-cluster --zone=us-central1-a

# Delete Docker images
gcloud artifacts docker images delete us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest
gcloud artifacts docker images delete us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest
```

---

## 📝 Quick Reference

### Essential Commands (Copy-Paste Ready)

```bash
# 1. Create repository
gcloud artifacts repositories create docker-repo --repository-format=docker --location=us-central1 --description="Docker repository for Mother of Bots"

# 2. Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# 3. Build and push backend
docker build -f k8s/Dockerfile.backend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest .
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest

# 4. Build and push frontend
docker build -f k8s/Dockerfile.frontend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest .
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest

# 5. Create cluster
gcloud container clusters create mother-of-bots-cluster --project=motherofbots --zone=us-central1-a --num-nodes=2 --machine-type=e2-standard-4 --enable-autoscaling --min-nodes=2 --max-nodes=5 --enable-autorepair --enable-autoupgrade --workload-pool=motherofbots.svc.id.goog --addons=HorizontalPodAutoscaling,HttpLoadBalancing

# 6. Get credentials
gcloud container clusters get-credentials mother-of-bots-cluster --zone=us-central1-a

# 7. Deploy
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service-account.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 8. Check status
kubectl get services
kubectl get pods
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Backend pods are running: `kubectl get pods | grep backend`
- [ ] Frontend pods are running: `kubectl get pods | grep frontend`
- [ ] Services are created: `kubectl get services`
- [ ] External IP is assigned: `kubectl get service frontend-service`
- [ ] Backend health check passes: `kubectl logs deployment/backend-deployment | grep health`
- [ ] Application is accessible via external IP

---

## 🔗 Access Your Application

Once deployed, get the external IP:

```bash
EXTERNAL_IP=$(kubectl get service frontend-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Application available at: http://$EXTERNAL_IP"
```

Open `http://EXTERNAL_IP` in your browser to access the application.

