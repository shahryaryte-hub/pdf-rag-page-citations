"""Use a page-cited passage to answer one question about NIST's AI RMF."""
import argparse
import http.client
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


PDF = "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf"
ACTOR = "solidscrape~pdf-to-rag-with-citations"
QUESTION = "Which three concepts does NIST emphasize in responsible AI?"
CAP_USD = 0.02

# Short excerpts of two real Actor rows, with their original page links.
PREVIEW = [
    {
        "text": "The Framework is divided into two parts.",
        "pageNumber": 7,
        "citationUrl": PDF + "#page=7",
    },
    {
        "text": (
            "Core concepts in responsible AI emphasize human centricity, "
            "social responsibility, and sustainability."
        ),
        "pageNumber": 6,
        "citationUrl": PDF + "#page=6",
    },
]


def find_answer(rows):
    """Rank extracted sentences by overlap with this example's question."""
    words = set(re.findall(r"[a-z]+", QUESTION.lower()))
    terms = words - {"which", "three", "does", "nist", "in"}
    best_score = 0
    answer = None
    for row in rows:
        page = row["pageNumber"]
        if page not in (6, 7) or row["citationUrl"] != f"{PDF}#page={page}":
            raise ValueError("Unexpected page or source link in the example output.")
        text = " ".join(row["text"].split())
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            if not sentence.endswith((".", "?", "!")):
                continue
            score = len(terms.intersection(re.findall(r"[a-z]+", sentence.lower())))
            if score > best_score:
                best_score = score
                answer = (sentence, page, row["citationUrl"])
    if best_score < 3:
        raise ValueError("No passage clearly matches the sample question.")
    return answer


class NoRedirects(HTTPRedirectHandler):
    """Keep the Authorization header on the original Apify API request."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(client, token, path, data=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = Request("https://api.apify.com/v2" + path, data=body, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    try:
        with client.open(req, timeout=30) as response:
            raw = response.read(2_000_001)
    except HTTPError as error:
        raise RuntimeError(f"Apify returned HTTP {error.code}. Check your run in Apify Console.") from None
    except (URLError, OSError, http.client.HTTPException):
        raise RuntimeError("Connection interrupted. Check Apify Console for an existing run before retrying.") from None
    if len(raw) > 2_000_000:
        raise ValueError("Response exceeds the size limit for this two-page sample.")
    return json.loads(raw)


def resource_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9]+", value):
        raise ValueError("Unexpected Apify resource ID.")
    return value


def live_rows():
    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        raise ValueError("Set APIFY_TOKEN in your local environment to run the live example.")
    if not re.fullmatch(r"[a-zA-Z0-9._~+/=-]+", token):
        raise ValueError("Check the format of your APIFY_TOKEN environment variable.")
    client = build_opener(NoRedirects())
    payload = {"pdfUrl": PDF, "startPage": 6, "maxPages": 2, "maxSpendUsd": CAP_USD}
    path = f"/acts/{ACTOR}/runs?timeout=180&memory=512&maxTotalChargeUsd={CAP_USD}"
    run = request_json(client, token, path, payload)["data"]
    run_id = resource_id(run["id"])
    print(f"Run: https://console.apify.com/actors/runs/{run_id}", file=sys.stderr, flush=True)
    deadline = time.monotonic() + 210
    while run["status"] in {"READY", "RUNNING", "TIMING-OUT", "ABORTING"}:
        if time.monotonic() >= deadline:
            raise RuntimeError("Local wait expired. Use the run link above to check progress.")
        time.sleep(2)
        run = request_json(client, token, f"/actor-runs/{run_id}")["data"]
    if run["status"] != "SUCCEEDED":
        raise RuntimeError("The example run did not succeed. See the run link above.")
    dataset = resource_id(run["defaultDatasetId"])
    return request_json(client, token, f"/datasets/{dataset}/items?clean=true&limit=100")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Start one Apify run (maximum Actor event charge $0.02).")
    args = parser.parse_args()
    try:
        sentence, page, url = find_answer(live_rows() if args.live else PREVIEW)
    except (RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(QUESTION)
    print(sentence)
    print(f"Source (physical PDF page {page}): {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
