# Kubernetes Deployment Files

This directory contains all the necessary files to deploy Mother of Bots to Google Kubernetes Engine (GKE).

## 📁 Files Overview

### Dockerfiles
- `Dockerfile.backend` - Backend Flask API container
- `Dockerfile.frontend` - Frontend React application container

### Kubernetes Manifests
- `configmap.yaml` - Application configuration (GCP settings)
- `service-account.yaml` - Service accounts for backend and frontend
- `backend-deployment.yaml` - Backend deployment and service
- `frontend-deployment.yaml` - Frontend deployment and service
- `ingress.yaml` - Ingress and SSL certificate (optional, for custom domain)

### Configuration
- `nginx.conf` - Nginx configuration for frontend
- `.dockerignore` - Files to exclude from Docker builds

### Scripts
- `deploy.sh` - Automated deployment script

## 🚀 Quick Start

### Prerequisites

1. **GCP Project Setup**
   ```bash
   gcloud config set project motherofbots
   gcloud config set compute/region us-central1
   gcloud config set compute/zone us-central1-a
   ```

2. **Create Artifact Registry Repository**
   ```bash
   gcloud artifacts repositories create docker-repo \
       --repository-format=docker \
       --location=us-central1 \
       --description="Docker repository for Mother of Bots"
   ```

3. **Create GKE Cluster**
   ```bash
   gcloud container clusters create mother-of-bots-cluster \
       --num-nodes=2 \
       --machine-type=e2-standard-4 \
       --zone=us-central1-a \
       --enable-autoscaling \
       --min-nodes=2 \
       --max-nodes=5 \
       --enable-autorepair \
       --workload-pool=motherofbots.svc.id.goog
   ```

4. **Create Service Account**
   ```bash
   gcloud iam service-accounts create mother-of-bots-sa \
       --display-name="Mother of Bots Service Account"
   
   gcloud projects add-iam-policy-binding motherofbots \
       --member="serviceAccount:mother-of-bots-sa@motherofbots.iam.gserviceaccount.com" \
       --role="roles/aiplatform.user"
   ```

5. **Configure Docker Authentication**
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

### Deploy

**Option 1: Using the deployment script**
```bash
chmod +x k8s/deploy.sh
./k8s/deploy.sh
```

**Option 2: Manual deployment**
```bash
# Build and push images
docker build -f k8s/Dockerfile.backend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest .
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest

docker build -f k8s/Dockerfile.frontend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest .
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest

# Get cluster credentials
gcloud container clusters get-credentials mother-of-bots-cluster --zone=us-central1-a

# Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service-account.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

## 🔧 Configuration

### Update Project ID

If your project ID is different from `motherofbots`, update these files:
- `configmap.yaml` - `gcp_project_id` field
- `service-account.yaml` - Service account annotation
- `backend-deployment.yaml` - Image path
- `frontend-deployment.yaml` - Image path
- `deploy.sh` - `PROJECT_ID` variable

### Update Image Paths

All image references use:
```
us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest
us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-frontend:latest
```

## 📊 Monitoring

```bash
# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/backend-deployment
kubectl logs -f deployment/frontend-deployment

# Get external IP
kubectl get service frontend-service

# Describe resources
kubectl describe deployment/backend-deployment
kubectl describe pod POD_NAME
```

## 🔄 Updates

To update the deployment:

```bash
# Rebuild and push images
./k8s/deploy.sh

# Or manually:
kubectl set image deployment/backend-deployment backend=NEW_IMAGE_TAG
kubectl rollout restart deployment/backend-deployment
```

## 🧹 Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Delete cluster
gcloud container clusters delete mother-of-bots-cluster --zone=us-central1-a
```

## 📝 Notes

- The frontend service uses `LoadBalancer` type for external access
- Backend service uses `ClusterIP` (internal only)
- Frontend proxies `/api` requests to backend
- Health checks are configured for both services
- Resource limits are set to prevent overconsumption

