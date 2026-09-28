"""In-process HTTP provider for synthetic adapter and subprocess server tests."""

from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Event, Lock, Thread


def completion(answers=None, *, model="reported-model"):
    """A valid Chat Completions envelope; callers can mutate failure fields."""
    return {
        "id": "synthetic-completion",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        {"answers": {"q": 0.5} if answers is None else answers}
                    ),
                    "reasoning_content": "synthetic reasoning",
                    "refusal": None,
                },
            }
        ],
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
            "reasoning_tokens": 3,
        },
    }


@dataclass
class Reply:
    body: object
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    delay: float = 0
    stall: bool = False


class FakeProvider:
    """Serve one scripted Reply (or JSON object) per request on loopback only.

    requests contains synthetic request bodies, paths and headers for assertions.
    received signals the first request; close releases stalled or delayed replies.
    """

    def __init__(self, script):
        self.script = deque(script)
        self.requests = []
        self.received = Event()
        self.release = Event()
        self.lock = Lock()
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(
                    self.rfile.read(int(self.headers["Content-Length"]))
                )
                with fake.lock:
                    fake.requests.append(
                        {
                            "path": self.path,
                            "headers": {
                                key.lower(): value
                                for key, value in self.headers.items()
                            },
                            "body": body,
                        }
                    )
                    step = (
                        fake.script.popleft()
                        if fake.script
                        else Reply({"error": "script exhausted"}, 500)
                    )
                fake.received.set()
                reply = step if isinstance(step, Reply) else Reply(step)
                if reply.stall:
                    fake.release.wait()
                elif reply.delay:
                    fake.release.wait(reply.delay)
                data = (
                    reply.body
                    if isinstance(reply.body, bytes)
                    else json.dumps(reply.body).encode()
                )
                try:
                    self.send_response(reply.status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    for key, value in reply.headers.items():
                        self.send_header(key, value)
                    self.end_headers()
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = False
        self.base_url = f"http://127.0.0.1:{self.server.server_port}/v1"
        self.thread = Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}
        )

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
