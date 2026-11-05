"""Kiểm hai endpoint CAD thật lần lượt, đồng thời đo health, auth và backend PID."""
import concurrent.futures
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "http://127.0.0.1:8000"
OUT = HERE / ("runtime46_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
OUT.mkdir()


def now():
    return datetime.now(timezone.utc).isoformat()


def backend_sample():
    cmd = ("$p=Get-Process -Id 20288 -ErrorAction Stop; "
           "@{pid=$p.Id;cpu=$p.CPU;rss=$p.WorkingSet64} | ConvertTo-Json -Compress")
    return json.loads(subprocess.check_output(["powershell.exe", "-NoProfile", "-Command", cmd],
                                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=10))


def probe(path):
    start = time.perf_counter()
    try:
        res = requests.get(BASE + path, timeout=5)
        return {"http": res.status_code, "seconds": round(time.perf_counter() - start, 3)}
    except requests.RequestException as exc:
        return {"error": type(exc).__name__, "seconds": round(time.perf_counter() - start, 3)}


def upload(name, endpoint):
    path = ROOT / "data/drawings/build" / name
    with path.open("rb") as stream:
        res = requests.post(BASE + endpoint, files={"file": (name, stream)},
                            timeout=(5, 900))
    summary = {"http": res.status_code, "response_bytes": len(res.content)}
    if res.ok:
        data = res.json()
        if endpoint.endswith("/view"):
            summary["plans"] = [{"name": p["plan"]["name"], "walls": len(p["walls"]),
                                 "openings": len(p["openings"])} for p in data["plans"]]
        else:
            summary["items"] = {k: len(v) for k, v in data.items() if isinstance(v, (list, dict))}
        summary["file"] = data["file"]
    else:
        summary["detail"] = res.text[:350]
    return summary


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    report = {"start": now(), "pid": 20288, "route": BASE, "jobs": []}
    print(OUT.name, flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for filename, endpoint in (("tan_binh_kien_truc.dxf", "/api/takeoff/view"),
                                   ("tan_binh_ket_cau.dxf", "/api/takeoff/structural")):
            job = {"start": now(), "file": filename, "endpoint": endpoint,
                   "bytes": (ROOT / "data/drawings/build" / filename).stat().st_size,
                   "initial_process": backend_sample(), "probes": []}
            report["jobs"].append(job)
            save("result.json", report)
            start = time.perf_counter()
            task = pool.submit(upload, filename, endpoint)
            try:
                while not task.done():
                    concurrent.futures.wait([task], timeout=2 if not job["probes"] else 15)
                    if task.done():
                        break
                    hp = pool.submit(probe, "/api/health")
                    auth = pool.submit(probe, "/api/auth/me")
                    sample = {"utc": now(), "process": backend_sample(),
                              "health": hp.result(), "auth_me": auth.result(),
                              "job_still_pending": not task.done()}
                    job["probes"].append(sample)
                    save("result.json", report)
                job["response"] = task.result()
            except Exception as exc:
                job["error"] = type(exc).__name__ + ": " + str(exc)[:250]
            job.update(end=now(), seconds=round(time.perf_counter() - start, 3),
                       final_process=backend_sample())
            save("result.json", report)
            print(filename, job.get("response", job.get("error")), flush=True)
            if "error" in job:
                break
    report["end"] = now()
    save("result.json", report)


if __name__ == "__main__":
    main()
