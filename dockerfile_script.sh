# Set GCP Environment Variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export REPO_NAME="agentic-workflow-repo"
export IMAGE_TAG="v1.0.0"

# 1. Build & Push Cloud Run Router Service Image
docker build --target router-service -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/router-service:${IMAGE_TAG} .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/router-service:${IMAGE_TAG}

# 2. Build & Push Cloud Run Worker Job Image
docker build --target worker-job -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/worker-job:${IMAGE_TAG} .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/worker-job:${IMAGE_TAG}

# 3. Deploy Control Plane Cloud Run Service
gcloud run deploy enterprise-agent-router \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/router-service:${IMAGE_TAG} \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --timeout=3600s \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}"

# 4. Create Ephemeral Worker Cloud Run Job
gcloud run jobs create worker-agent-job \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/worker-job:${IMAGE_TAG} \
  --region=${REGION} \
  --max-retries=2 \
  --task-timeout=900s \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},REGION=${REGION}"