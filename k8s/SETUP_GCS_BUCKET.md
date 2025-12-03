# Setup GCS Bucket for Generated Projects

This guide will help you create a Google Cloud Storage bucket to store generated chatbot projects.

## Prerequisites

- GCP Project: `motherofbots`
- Service Account: `mob-653@motherofbots.iam.gserviceaccount.com`
- Region: `us-central1`

## Step 1: Create GCS Bucket

```powershell
# Create the bucket
gsutil mb -p motherofbots -c STANDARD -l us-central1 gs://motherofbots-generated-projects

# Enable versioning (optional, for backup)
gsutil versioning set on gs://motherofbots-generated-projects
```

## Step 2: Grant Permissions to Service Account

```powershell
# Grant Storage Object Admin role to service account
gsutil iam ch serviceAccount:mob-653@motherofbots.iam.gserviceaccount.com:roles/storage.objectAdmin gs://motherofbots-generated-projects
```

## Step 3: Verify Bucket Creation

```powershell
# List buckets
gsutil ls

# Check bucket details
gsutil ls -L gs://motherofbots-generated-projects
```

## Step 4: Update ConfigMap (Already Done)

The ConfigMap has been updated with:
```yaml
gcs_bucket_name: "motherofbots-generated-projects"
```

## Step 5: Apply Updated ConfigMap

```powershell
kubectl apply -f k8s/configmap.yaml
```

## Step 6: Rebuild and Redeploy Backend

```powershell
# Rebuild backend image with google-cloud-storage
docker build -f k8s/Dockerfile.backend -t us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest .

# Push image
docker push us-central1-docker.pkg.dev/motherofbots/docker-repo/mother-of-bots-backend:latest

# Restart backend
kubectl rollout restart deployment/backend-deployment
```

## Project Storage Structure

Generated projects will be stored in GCS with the following structure:

```
gs://motherofbots-generated-projects/
  └── projects/
      └── generated_project_{uuid}/
          ├── backend/
          │   ├── app.py
          │   └── requirements.txt
          ├── frontend/
          │   ├── App.jsx
          │   ├── index.html
          │   ├── package.json
          │   └── config.js
          └── README.md
```

## Accessing Generated Projects

You can access the generated projects using:

1. **gsutil command:**
   ```powershell
   gsutil ls gs://motherofbots-generated-projects/projects/
   ```

2. **GCP Console:**
   - Go to Cloud Storage > Buckets
   - Navigate to `motherofbots-generated-projects`
   - Browse the `projects/` folder

3. **Download a project:**
   ```powershell
   gsutil -m cp -r gs://motherofbots-generated-projects/projects/generated_project_abc123 ./downloaded_project
   ```

## Lifecycle Management (Optional)

To automatically delete old projects (older than 90 days), you can set a lifecycle policy:

```powershell
# Create lifecycle policy file
@"
{
  'lifecycle': {
    'rule': [
      {
        'action': {'type': 'Delete'},
        'condition': {'age': 90}
      }
    ]
  }
}
"@ | Out-File -FilePath lifecycle.json -Encoding utf8

# Apply lifecycle policy
gsutil lifecycle set lifecycle.json gs://motherofbots-generated-projects
```

## Troubleshooting

### Permission Denied
If you get permission errors, ensure the service account has the correct role:
```powershell
gsutil iam get gs://motherofbots-generated-projects
```

### Bucket Not Found
Verify the bucket exists:
```powershell
gsutil ls gs://motherofbots-generated-projects
```

### Upload Fails
Check backend logs:
```powershell
kubectl logs deployment/backend-deployment | Select-String -Pattern "GCS|upload"
```

