"""
Single-worker job queue for long generation runs.

Cloudflare closes any proxied request whose origin has not responded within
roughly 100 seconds and returns a 524 to the browser. Generation takes three to
ten minutes, so the work cannot happen inside the request that asks for it.
The client posts a document, receives a job id immediately, and polls.

One worker, deliberately. A single run already saturates Ollama's five parallel
slots on one GPU, so two concurrent runs do not both finish in the time one
would take -- they interleave, each takes roughly twice as long, and the extra
KV cache risks exhausting 8 GB. Serialising means whoever arrives first runs at
full speed, and whoever arrives second is told where they are in the queue
rather than watching an unexplained slowdown.

State lives in this process. That matches the deployment (one Flask process on
one machine with one GPU); a second worker process would need shared storage
and a real broker, and would not make anything faster.
"""
import logging
import queue
import threading
import time
import uuid

logger = logging.getLogger(__name__)

# How long a finished job stays readable before it is discarded. The client
# polls every couple of seconds, so this is generous; it exists to stop a
# long-lived server accumulating every result it has ever produced.
RESULT_TTL_SECONDS = 3600


class Job:
    """One queued or running generation."""

    __slots__ = ('id', 'status', 'filename', 'phase', 'phase_num', 'total_phases',
                 'result', 'http_status', 'error', 'queued_at', 'started_at',
                 'finished_at')

    TOTAL_PHASES = 5

    def __init__(self, job_id, filename):
        self.id = job_id
        self.filename = filename
        self.status = 'queued'          # queued | running | done | failed
        self.phase = 'Waiting to start'
        self.phase_num = 0
        self.total_phases = self.TOTAL_PHASES
        self.result = None              # payload dict once done
        self.http_status = None         # status the payload would have had
        self.error = None
        self.queued_at = time.time()
        self.started_at = None
        self.finished_at = None

    def elapsed(self):
        if self.started_at is None:
            return 0.0
        return (self.finished_at or time.time()) - self.started_at

    def to_dict(self, position=None):
        payload = {
            'job_id': self.id,
            'status': self.status,
            'filename': self.filename,
            'phase': self.phase,
            'phase_num': self.phase_num,
            'total_phases': self.total_phases,
            'elapsed_seconds': round(self.elapsed(), 1),
        }
        if position is not None:
            payload['queue_position'] = position
        if self.status == 'done':
            payload['result'] = self.result
        elif self.status == 'failed':
            payload['error'] = self.error
            if self.result:
                payload['result'] = self.result
        return payload


class JobQueue:
    """
    FIFO queue with exactly one worker thread.

    Submitted callables receive the Job as their only argument and return
    (payload_dict, http_status). Raising is also fine: the job is marked failed
    and the exception text is reported.
    """

    def __init__(self, app=None):
        self._app = app
        self._jobs = {}
        self._order = []                # submission order, for queue position
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._worker = None

    def init_app(self, app):
        """Bind the Flask app and start the worker. Safe to call once."""
        self._app = app
        if self._worker is None:
            self._worker = threading.Thread(
                target=self._run, name='generation-worker', daemon=True)
            self._worker.start()
            logger.info("Generation worker started (concurrency 1)")

    def submit(self, fn, filename):
        """Queue a callable. Returns the Job."""
        job = Job(uuid.uuid4().hex, filename)
        with self._lock:
            self._prune_locked()
            self._jobs[job.id] = job
            self._order.append(job.id)
        self._queue.put((job, fn))
        logger.info(f"Job {job.id[:8]} queued ({filename}), "
                    f"{self.position_of(job.id) or 0} ahead")
        return job

    def get(self, job_id):
        with self._lock:
            return self._jobs.get(job_id)

    def position_of(self, job_id):
        """
        How many jobs must finish before this one starts, or None once it has.

        Zero means it is next and the worker is about to pick it up.
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status != 'queued':
                return None
            ahead = 0
            for other_id in self._order:
                if other_id == job_id:
                    break
                other = self._jobs.get(other_id)
                if other and other.status in ('queued', 'running'):
                    ahead += 1
            return ahead

    def _prune_locked(self):
        """Drop finished jobs past their TTL. Caller holds the lock."""
        cutoff = time.time() - RESULT_TTL_SECONDS
        stale = [jid for jid, j in self._jobs.items()
                 if j.finished_at and j.finished_at < cutoff]
        for jid in stale:
            del self._jobs[jid]
            if jid in self._order:
                self._order.remove(jid)
        if stale:
            logger.debug(f"Pruned {len(stale)} finished job(s)")

    def _run(self):
        while True:
            job, fn = self._queue.get()
            job.status = 'running'
            job.started_at = time.time()
            job.phase = 'Starting'
            logger.info(f"Job {job.id[:8]} started ({job.filename})")
            try:
                # The callable reaches Flask config and extensions, so give it
                # an application context -- there is no request context here.
                if self._app is not None:
                    with self._app.app_context():
                        payload, status = fn(job)
                else:
                    payload, status = fn(job)
                job.result = payload
                job.http_status = status
                job.status = 'done' if status < 400 else 'failed'
                if job.status == 'failed':
                    job.error = (payload or {}).get('error', 'Generation failed')
            except Exception as exc:                      # noqa: BLE001
                logger.exception(f"Job {job.id[:8]} raised")
                job.status = 'failed'
                job.error = str(exc)
                job.http_status = 500
            finally:
                job.finished_at = time.time()
                job.phase = ('Complete' if job.status == 'done' else 'Failed')
                job.phase_num = job.total_phases if job.status == 'done' else job.phase_num
                logger.info(f"Job {job.id[:8]} {job.status} in {job.elapsed():.1f}s")
                self._queue.task_done()


# One queue for the app.
job_queue = JobQueue()
