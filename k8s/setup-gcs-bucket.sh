#!/bin/bash
# Setup GCS bucket for storing generated chatbot projects

PROJECT_ID="motherofbots"
BUCKET_NAME="motherofbots-generated-projects"
LOCATION="us-central1"
SERVICE_ACCOUNT="mob-653@motherofbots.iam.gserviceaccount.com"

echo "Creating GCS bucket: $BUCKET_NAME"

# Create bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l $LOCATION gs://$BUCKET_NAME

# Set bucket versioning (optional, for backup)
gsutil versioning set on gs://$BUCKET_NAME

# Grant service account Storage Object Admin role
echo "Granting permissions to service account..."
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT:roles/storage.objectAdmin gs://$BUCKET_NAME

# Set lifecycle policy (optional - delete files older than 90 days)
cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
gsutil lifecycle set /tmp/lifecycle.json gs://$BUCKET_NAME
rm /tmp/lifecycle.json

echo "GCS bucket setup complete!"
echo "Bucket: gs://$BUCKET_NAME"
echo "Projects will be stored at: gs://$BUCKET_NAME/projects/{project_name}/"

