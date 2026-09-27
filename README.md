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
