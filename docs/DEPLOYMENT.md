# Deployment

The Flask development server is not suitable for anything beyond a laptop. It
prints a warning on every start for good reason:

```
WARNING: This is a development server. Do not use it in a production deployment.
```

Two distinct problems, not one:

1. **Security.** `debug=True` serves the Werkzeug interactive debugger. Anyone
   who can reach the port and trigger a traceback gets a console that executes
   code in the process. Combined with binding to `0.0.0.0`, that is remote code
   execution on any network you do not fully trust.
2. **Concurrency.** The dev server is single-threaded by default and not built
   for concurrent load. This pipeline holds a request open for around three
   minutes while five worker threads run, which is the profile it handles worst.

`run.py` now defaults `debug` to off and binds to `127.0.0.1`. Everything below
is about serving it properly.

---

## Ubuntu / Linux: gunicorn

```bash
pip install -r requirements.txt

gunicorn \
  --chdir src \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --threads 4 \
  --timeout 600 \
  --graceful-timeout 30 \
  --access-logfile - \
  "backend.app:app"
```

### Why these values

**`--timeout 600`** is the one you cannot leave at the default. Gunicorn's
default is 30 seconds, and it kills any worker that does not respond in time. A
full pipeline run takes two to four minutes, so with the default *every*
generation request is killed mid-flight and the client sees a truncated
response. Set it above your slowest expected run.

**`--workers 2`, not `2 * cores + 1`.** The usual heuristic sizes workers
against CPU, which is wrong here: every request drives the same local Ollama
instance, so the constraint is GPU capacity, not CPU. Each Flask worker also
spawns `MAX_PARALLEL_WORKERS` threads of its own, so 2 gunicorn workers at 5
pipeline workers each is already 10 concurrent model calls. Oversizing thrashes
the GPU and makes everything slower.

**`--threads 4`** because the workload is I/O-bound — threads spend their time
waiting on Ollama, not computing.

Scale concurrency with `OLLAMA_NUM_PARALLEL` on the Ollama side. Adding Flask
workers without raising it just queues requests deeper.

---

## Windows: waitress

Gunicorn needs `fork` and does not run on Windows. Use waitress:

```powershell
pip install -r requirements.txt

waitress-serve --listen=0.0.0.0:5000 --threads=8 --channel-timeout=600 backend.app:app
```

Run it from the `src` directory, or set `PYTHONPATH` to `src`.

---

## Required environment

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | **Yes** | Signs session cookies. Without it the app falls back to a well-known constant and logs a warning; anyone who knows that constant can forge a session. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Yes, for login | OAuth credentials. Never commit them; `.env` is gitignored. |
| `DATABASE_URL` | No | Defaults to SQLite in `instance/`. |
| `OLLAMA_BASE_URL` | No | Defaults to `http://localhost:11434`. |
| `OLLAMA_MODEL` | No | Generation model. |
| `REVIEWER_MODEL` | No | Judge model. Prefer a different model from `OLLAMA_MODEL` — see `docs/PARALLEL_SETUP.md`. |
| `OLLAMA_TIMEOUT` | No | Per-call budget in seconds, default 180. Raise for larger models. |
| `FLASK_DEBUG` | No | **Leave unset in production.** Enables the interactive debugger. |
| `FLASK_HOST` / `FLASK_PORT` | No | Only used by `run.py`'s dev server. |

Verify before exposing the service:

```bash
python -c "import os; assert os.environ.get('SECRET_KEY'), 'SECRET_KEY not set'"
```

---

## Reverse proxy

Behind nginx, raise the proxy timeouts to match gunicorn's. The defaults are
60 seconds and will cut off a generation request that is working correctly:

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
}
```

`X-Forwarded-Proto` matters for OAuth: without it Flask builds `http://` callback
URLs behind an HTTPS proxy and Google rejects the redirect.

---

## Long requests

A three-minute HTTP request is fragile no matter how the timeouts are tuned —
any proxy, load balancer or laptop lid in between can end it. If this moves
beyond a small number of trusted users, the right shape is a job queue: accept
the upload, return a job id immediately, and let the client poll.

The checkpoint artifacts under `data/runs/<run_id>/` already persist each phase
as it completes, so most of that groundwork exists.
