"""Reuse the Goud/Relevate desktop app's installed llama.cpp runtime and GGUF."""
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


class GoudRuntime:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path.home() / "Library/Application Support/com.relevate.desktop/llama.cpp"
        self.process = None
        self.log = None

    @staticmethod
    def model_at(port):
        try:
            with urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=2) as response:
                models = json.load(response).get("data", [])
            return next((m["id"] for m in models if "gemma" in m["id"].lower()), None)
        except (URLError, OSError, ValueError, KeyError):
            return None

    def connect(self):
        # These are the desktop app's existing orchestrator, primary and executor ports.
        for port in (18766, 18765, 18767, 18769):
            model = self.model_at(port)
            if model:
                return f"http://127.0.0.1:{port}", model
        manifest = json.loads((self.root / "install.json").read_text())
        executable = Path(manifest["executable_path"])
        model = self.root / "models/gemma-4-E2B-it-Q4_K_M.gguf"
        if not executable.is_file() or not model.is_file():
            raise ValueError("The desktop app's installed runtime or Gemma E2B model is missing.")
        log_path = Path(__file__).resolve().parent / "runtime.log"
        self.log = log_path.open("a")
        environment = dict(os.environ)
        environment["DYLD_LIBRARY_PATH"] = str(executable.parent) + os.pathsep + environment.get("DYLD_LIBRARY_PATH", "")
        self.process = subprocess.Popen([
            str(executable), "-m", str(model), "--host", "127.0.0.1", "--port", "18769",
            "--ctx-size", "4096", "--parallel", "1", "--cache-type-k", "f16",
            "--cache-type-v", "f16", "-ngl", "999",
        ], cwd=executable.parent, env=environment, stdout=self.log, stderr=self.log)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.close()
                raise ValueError(f"The desktop llama.cpp runtime exited. See {log_path}.")
            served_model = self.model_at(18769)
            if served_model:
                return "http://127.0.0.1:18769", served_model
            time.sleep(0.5)
        self.close()
        raise ValueError(f"Gemma did not become ready. See {log_path}.")

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        if self.log:
            self.log.close()
