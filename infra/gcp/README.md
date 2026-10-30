# Google Cloud deployment

This stack provisions the production foundation for HackEval:

- Cloud Run for the API and restricted runner
- Cloud SQL PostgreSQL with private networking and point-in-time backups
- Memorystore Redis
- Private, versioned Cloud Storage for uploads
- Secret Manager-backed JWT and runner credentials
- Serverless VPC Access and least-privilege service accounts

Build and push the two images first:

```powershell
gcloud builds submit backend --tag REGION-docker.pkg.dev/PROJECT/hackeval/backend
gcloud builds submit runner --tag REGION-docker.pkg.dev/PROJECT/hackeval/runner
gcloud builds submit frontend --tag REGION-docker.pkg.dev/PROJECT/hackeval/frontend
```

Then provision. Pass secrets through an untracked `terraform.tfvars` file or a
CI secret store; never put them in the repository:

```powershell
terraform init
terraform apply `
  -var="project_id=PROJECT" `
  -var="backend_image=REGION-docker.pkg.dev/PROJECT/hackeval/backend" `
  -var="runner_image=REGION-docker.pkg.dev/PROJECT/hackeval/runner" `
  -var="frontend_image=REGION-docker.pkg.dev/PROJECT/hackeval/frontend" `
  -var="upload_bucket=PROJECT-hackeval-uploads" `
  -var="db_password=USE_A_SECRET_MANAGER_OR_TFVARS" `
  -var="jwt_secret=LONG_RANDOM_VALUE" `
  -var="runner_token=RANDOM_RUNNER_TOKEN"
```

Do not commit `terraform.tfvars`, database passwords, or secret values. After
Terraform creates the migration job, run it before accepting traffic:

```powershell
gcloud run jobs execute hackeval-migration --region REGION --wait
```

Verify the database with:

```powershell
gcloud sql operations list --instance hackeval-postgres --project PROJECT
```
