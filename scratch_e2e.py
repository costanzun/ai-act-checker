import asyncio, json, sys, time, os
sys.path.insert(0, "backend"); os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv; load_dotenv(".env.example")
os.environ["HF_HOME"] = os.path.abspath("data/models")
from pathlib import Path
from app.corpus.store import CorpusStore
from app.pipeline import Pipeline
from app.schemas import AssessRequest

async def main():
    p = Pipeline(CorpusStore(Path("data/corpus")))
    desc = "Our HR department in Milan uses a third-party tool that reads incoming CVs, scores candidates against the job description and ranks them. Recruiters review the top 20 and decide whom to interview."
    t0 = time.time()
    req = AssessRequest(description=desc, language="en")
    async for name, payload in p.run(req):
        if name == "stage": print(f"[{time.time()-t0:5.1f}s] stage {payload['stage']}")
        elif name == "facts": print(f"[{time.time()-t0:5.1f}s] facts: role={payload['facts']['role']} sector={payload['facts']['sector']} area={payload['facts']['annex_iii_area']} impact={payload['facts']['decision_impact']} profiling={payload['facts']['art63']['profiling_of_natural_persons']} unknown={len([1 for k,v in payload['facts'].items() if v is None])}")
        elif name == "questions":
            print(f"[{time.time()-t0:5.1f}s] QUESTIONS round {payload['round']}:")
            for q in payload["questions"]: print("   -", q["fact_path"], "|", q["text"]["en"], "| impact", q["impact"], "| opts", [o["value"] for o in q["options"]])
            qs = payload["questions"]; facts = payload["facts"]
        elif name == "token": print(payload["text"], end="", flush=True)
        elif name == "result":
            a = payload["assessment"]; c = a["classification"]
            print(f"\n[{time.time()-t0:5.1f}s] RESULT tier={c['tier']} conf={c['confidence']} role={c['role']} overlays={ {k:v for k,v in c['overlays'].items() if v} }")
            print("  findings:", [(f['rule_id'], f['decisive'], f['citations']) for f in c['findings']])
            print("  applies_from:", [(m['id'], m['date']) for m in c['applies_from']])
            print("  obligations:", len(a['obligations']), "checklist:", len(a['checklist']), "related:", [r['id'] for r in a['related_provisions']])
            print("  summary:", a.get("summary")); print("  uncertainties:", a["uncertainties"]); print("  metrics:", a["metrics"])
        elif name == "done": print(f"[{time.time()-t0:5.1f}s] done {payload}")
        elif name == "error": print("ERROR", payload)
asyncio.run(main())
