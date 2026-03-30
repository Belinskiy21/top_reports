# Deploy To Dokku On A DigitalOcean Droplet

This repo is set up for Dokku using the root [Dockerfile](/Users/olehpro/work/tasks/quartr/top_reports/Dockerfile) and [Procfile](/Users/olehpro/work/tasks/quartr/top_reports/Procfile).

Dokku references:

- Dockerfile deployment: https://dokku.com/docs/deployment/builders/dockerfiles/
- App deployment: https://dokku.com/docs/deployment/application-deployment/
- Environment variables: https://dokku.com/docs/configuration/environment-variables/

## 1. Install Dokku on the Droplet

The easiest route is the DigitalOcean Dokku marketplace image:

- https://docs.digitalocean.com/products/marketplace/catalog/dokku/

## 2. Install the PostgreSQL plugin

On the Dokku host:

```bash
sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git postgres
```

Check that it is installed:

```bash
dokku plugin:installed postgres
```

## 3. Create the app and database service

Replace `top-reports` below if you want a different Dokku app name.

On the Dokku host:

```bash
dokku apps:create top-reports
dokku postgres:create top-reports-db
dokku postgres:link top-reports-db top-reports
```

Linking the Postgres service sets `DATABASE_URL` for the app.

## 4. Configure environment variables

At minimum, set the app secret and SEC user agent:

```bash
dokku config:set top-reports \
  JWT_SECRET=change-me \
  SEC_USER_AGENT=quartr
```

Optional settings:

```bash
dokku config:set top-reports \
  STORAGE_BACKEND=local \
  LOCAL_STORAGE_DIR=storage/files \
  REPORT_PREFETCH_ENABLED=false \
  REPORT_PREFETCH_INTERVAL_SECONDS=86400 \
  REPORT_PREFETCH_USER_EMAIL=seeded-user@quartr.dev
```

Notes:

- `REPORT_PREFETCH_ENABLED=true` enables the background prefetch loop on app boot.
- `REPORT_PREFETCH_USER_EMAIL` only decides which app user is recorded as the creator of prefetched report rows. User emails are not sent to the SEC API.

## 5. Decide how report PDFs will be stored

For production, S3-style object storage is the safer default because report files should survive deploys and container rebuilds.

If you use S3:

```bash
dokku config:set top-reports \
  STORAGE_BACKEND=s3 \
  S3_BUCKET_NAME=your-bucket \
  S3_PUBLIC_BASE_URL=https://your-bucket.s3.amazonaws.com \
  AWS_REGION=eu-north-1
```

If you keep `STORAGE_BACKEND=local`, make sure you also persist `/app/storage/files` on the Dokku host. Otherwise generated PDFs can disappear on redeploy.

## 6. Add the Dokku git remote

On your local machine:

```bash
git remote add dokku dokku@your-droplet-hostname:top-reports
```

## 7. Deploy

On your local machine:

```bash
git push dokku main
```

If your default branch is not `main`, push that branch instead.

## 8. Initialize the schema

Run the seed script once on the Dokku host:

```bash
dokku run top-reports python -m db.seed
```

This creates the database tables, seeds the supported companies, and creates the demo user.

## 9. Verify

```bash
dokku logs top-reports
curl https://your-domain/
```

Optional auth check:

```bash
curl -X POST https://your-domain/api/v1/sign-in \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seeded-user@quartr.dev",
    "password": "seeded-password"
  }'
```

## Notes

- Dokku provides `PORT`, and the app respects it.
- [docker/entrypoint.sh](/Users/olehpro/work/tasks/quartr/top_reports/docker/entrypoint.sh) starts only the web process.
- Seeding is an explicit Dokku command and is not part of the container entrypoint.
- The root endpoint is `GET /`, not `/health`.
