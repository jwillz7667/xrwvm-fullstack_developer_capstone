# OpenRoad — IBM Full Stack Dealership Capstone

Implementation by Justin Williams, with AI coding assistance, based on the IBM Skills Network starter. OpenRoad is an educational dealership review portal with fictional company details and the supplied IBM sample dataset.

## Features

- Browse dealerships, filter by state, inspect dealer details and newest-first customer reviews.
- Register, log in, and log out using Django sessions. Authenticated customers can write reviews and optionally attach vehicle/purchase information.
- Django admin manages vehicle makes and models.
- Express/MongoDB stores dealers and reviews; idempotent seed imports preserve submitted reviews across restarts.
- A Flask/NLTK VADER service analyzes review sentiment using the bundled lexicon.
- React/Vite interface, accessible labels, loading/error feedback, responsive layouts, About and Contact pages.

## Architecture and safeguards

Browser → same-origin Django API → private Express/MongoDB and sentiment services. Django owns authentication and the relational vehicle catalog. Reviews use server-derived user identity. All mutation endpoints require POST and CSRF tokens; the private review service additionally requires a shared service key. Input sizes and purchase details are validated. Password validation and shared database authentication throttling are enabled. Backend calls have bounded timeouts. Containers run application processes as unprivileged users.

SQLite and named Docker volumes are used for this single-instance course deployment. Use PostgreSQL and a shared rate limiter before operating multiple production web instances. The Compose services bind only to localhost. Cloud deployment requires HTTPS, secure cookies, exact allowed hosts, secrets from the deployment environment, and persistent database volumes. No cloud deployment is claimed until its live checks succeed.

## Run locally

Requirements: Docker Engine with Compose and Python 3.

```sh
python3 scripts/init_local.py
docker compose --env-file .local-env up -d --build
```

Open http://127.0.0.1:8016 . The initializer creates private local secrets; they are ignored by Git. Register through the interface. To create an admin account interactively:

```sh
docker compose --env-file .local-env exec web python manage.py createsuperuser
```

Stop services without removing database volumes:

```sh
docker compose --env-file .local-env down
```

## Endpoints

Django: `/djangoapp/session`, `/login`, `/logout`, `/register`, `/get_dealers`, `/get_dealers/Kansas`, `/dealer/<id>`, `/reviews/dealer/<id>`, `/get_cars`, `/add_review` (all after `/djangoapp`).

Dealer service: `/fetchDealers`, `/fetchDealers/<state>`, `/fetchDealer/<id>`, `/fetchReviews/dealer/<id>`, `/insert_review`.

Sentiment service: `/analyze/<text>`. For example, `Fantastic services` returns a positive sentiment. Every service has `/healthz`.

## Verification

GitHub Actions lints Python and JavaScript, builds the React production bundle, verifies migrations, and runs Django authentication/authorization, CSRF, throttling, purchase validation, MongoDB persistence/validation, and sentiment tests. MongoDB tests create and drop only their own randomly named test database. To reproduce, follow `.github/workflows/validate.yml` with a local MongoDB instance on port 27019.

## Provenance

Starter and fixture data: https://github.com/ibm-developer-skills-network/xrwvm-fullstack_developer_capstone . Preserve the included Apache license. Company/team names and contacts are demonstration data. Source screenshots and grading evidence must be captured from real runs; local screenshots are not cloud-deployment evidence.

## Course cloud deployment

The Skills Network lab scripts deploy the sentiment analyzer on Code Engine and
Django, the Express API, and MongoDB on Kubernetes. Run
`bash scripts/deploy_sentiment.sh` in the enrolled Code Engine lab. In the
Kubernetes lab, set `SENTIMENT_URL` to the verified HTTPS endpoint and `APP_HOST`
to the exact hostname shown by Launch Application for port 8000, then run
`bash scripts/deploy_kubernetes.sh`.

The Kubernetes manifest uses persistent volumes for both databases, private
services and network policies for MongoDB and Express, generated Kubernetes
Secrets, immutable application image digests, resource limits, health probes,
and secure cookies behind the lab HTTPS proxy. Do not enable
`TRUST_HTTPS_PROXY` on a directly exposed server. The deployment scripts preserve
existing resources and save actual runtime evidence under ignored `evidence/`.
The free lab is temporary; this is a course deployment, not a production SLA.

If the lab image mirror cannot build the maintained runtime, the same Linux/amd64 images may be built outside the lab and transferred as a checksum-verified Docker archive. The deployment script only reuses a prebuilt image when its OCI revision label exactly matches the checked-out source commit; it then pushes the images to the lab ICR registry before Kubernetes deployment.
