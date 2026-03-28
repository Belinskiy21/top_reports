# Deploy To Dokku On A DigitalOcean Droplet

This repo is set up for Dokku using the root `Dockerfile` and `Procfile`.

Dokku references:

- Dockerfile deployment: https://dokku.com/docs/deployment/builders/dockerfiles/
- App deployment: https://dokku.com/docs/deployment/application-deployment/

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

On the Dokku host:

```bash
dokku apps:create fastapi-app
dokku postgres:create fastapi-app-db
dokku postgres:link fastapi-app-db fastapi-app
```

Linking the Postgres service sets `DATABASE_URL` for the app.

## 4. Add the Dokku git remote

On your local machine:

```bash
git remote add dokku dokku@your-droplet-hostname:fastapi-app
```

## 5. Deploy

On your local machine:

```bash
git push dokku main
```

If your default branch is not `main`, push that branch instead.

## 6. Initialize the schema

Run the seed script once on the Dokku host:

```bash
dokku run fastapi-app python db/seed.py
```

This creates the `users` table in the linked PostgreSQL database.

## 7. Verify

```bash
dokku logs fastapi-app
curl https://your-domain/health
curl https://your-domain/users
```

## Notes

- The app respects the `PORT` environment variable, which Dokku requires.
- `docker/entrypoint.sh` only starts the web process. Seeding is an explicit Dokku command.
