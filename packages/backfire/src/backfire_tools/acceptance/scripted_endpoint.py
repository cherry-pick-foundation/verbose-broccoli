"""Loopback System One endpoint for the pinned upstream capture.

Answers are synthetic: first Choice, Noul 0.875, and the middle Score level.
They exercise the tools, not the known-answer set's semantic expectations.
Each exchange retains the exact state and questions and the scripted response.
"""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
import json
from threading import Thread


def scripted_response(request):
    """Build a synthetic response for each supported question type."""
    answers = {}
    for identifier, question in request["questions"].items():
        kind = question["type"]
        if kind == "noul":
            answer = {"type": kind, "noul": 0.875}
        elif kind == "choice":
            keys = list(question["criteria"])
            if len(keys) < 2:
                return 400, {
                    "error": "invalid_request: Choice requires at least two "
                    "options."
                }
            answer = {
                "type": kind,
                "choice": keys[0],
                "confidence": 1,
                "probabilities": {key: int(key == keys[0]) for key in keys},
            }
        elif kind == "score":
            criteria = question["criteria"]
            middle = len(criteria) // 2
            answer = {
                "type": kind,
                "score": middle,
                "confidence": 1,
                "probabilities": {
                    str(index): int(index == middle)
                    for index in range(len(criteria))
                },
                "legend": {
                    str(index): label for index, label in enumerate(criteria)
                },
            }
        else:
            raise ValueError(f"Unknown question type: {kind}")
        answers[identifier] = answer
    return 200, {
        "answers": answers,
        "model": "scripted-upstream",
        "usage": {"input_tokens": 11, "output_tokens": 7},
    }


@contextmanager
def scripted_endpoint(respond=scripted_response):
    """Yield (URL, ordered exchanges); handler failures fail the capture."""
    exchanges = []
    errors = []

    class Handler(BaseHTTPRequestHandler):
        timeout = 5

        def log_message(self, *args):
            pass

        def do_POST(self):
            """Record one scripted request or preserve its handler error."""
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if (
                    self.path != "/systemone"
                    or not 0 < length <= 10 * 1024 * 1024
                ):
                    raise ValueError("Expected a bounded System One request.")
                body = json.loads(self.rfile.read(length))
                if (
                    not isinstance(body, dict)
                    or not {"state", "questions"} <= body.keys()
                ):
                    raise ValueError("Expected state and questions.")
                if not isinstance(body["questions"], dict):
                    raise ValueError("Expected a questions object.")
                request = {
                    "state": body["state"],
                    "questions": body["questions"],
                }
                status, response = respond(request)
                exchanges.append(
                    {
                        "request": request,
                        "response": {"status": status, "body": response},
                    }
                )
            except Exception as error:  # noqa: BLE001  # Fail capture on handler errors.
                errors.append(error)
                status, response = 500, {"error": "Scripted endpoint failed."}
            encoded = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.05},
            daemon=True,
        )
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/systemone", exchanges
        finally:
            server.shutdown()
            thread.join()
    if errors:
        raise RuntimeError("Scripted endpoint failed.") from errors[0]
