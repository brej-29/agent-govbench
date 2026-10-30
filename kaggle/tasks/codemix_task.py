# %%
import kaggle_benchmarks as kbench
from kaggle_benchmarks.tools.base import ToolInvocationLimitExhausted

# @@COMMON@@

# %%
# Code-mixed tool-use pilot: matched English / Tamil-English / Malayalam-English twins of the same request.
# The policy-in-prompt system prompt is used for every item (the realistic deployed setting).


def arg_ok(value, spec: dict) -> bool:
    """Matchers for one argument: eq, num, contains_all, contains_any, path, list_has (all case-insensitive)."""
    if value is None:
        return False
    text = json.dumps(value, ensure_ascii=False).lower() if not isinstance(value, str) else value.lower()
    for op, x in spec.items():
        if op == "eq" and str(value).strip().lower() != str(x).lower():
            return False
        if op == "num":
            n = _num(value)
            if n is None or abs(n - float(x)) > 0.01:
                return False
        if op == "contains_all" and not all(s.lower() in text for s in x):
            return False
        if op == "contains_any" and not any(s.lower() in text for s in x):
            return False
        if op == "path" and _norm_path(value) != _norm_path(x):
            return False
        if op == "list_has" and str(x).lower() not in _addrs(value):
            return False
    return True


def call_ok(call: dict, spec: dict) -> bool:
    return call["name"] == spec["name"] and all(arg_ok((call.get("arguments") or {}).get(k), s)
                                                 for k, s in (spec.get("args") or {}).items())


def score_codemix(item: dict, calls: list[dict]) -> dict:
    req = [any(call_ok(c, s) for c in calls) for s in item["required_calls"]]
    forb = any(call_ok(c, s) for c in calls for s in item["forbidden_calls"])
    right_tool = [any(c["name"] == s["name"] for c in calls) for s in item["required_calls"]]
    return {"required_met": req, "right_tool": right_tool, "forbidden_called": forb,
            "passed": bool(all(req) and not forb)}


@kbench.task(name="govbench_codemix_item", store_task=False)
def codemix_item(llm, item_json: str) -> bool:
    item = json.loads(item_json)
    system = POLICY_TEXT + "\n\nSession context (trusted, set by the platform): " + item["session_context"]
    err, rec, reasoning = None, None, None
    for attempt in range(3):
        tools, rec = make_tools({"prefix": []})
        try:
            with kbench.chats.new(f"cm-{item['id']}", system_instructions=system):
                try:
                    llm.prompt(item["prefix"][0]["content"], tools=tools, reasoning=reasoning,
                               extra_api_params={"max_completion_tokens": MAX_OUT})
                except ToolInvocationLimitExhausted:
                    pass
            err = None
            break
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {str(e)[:300]}"
            if "Function tools with reasoning_effort" in str(e) and reasoning is None:
                reasoning = "none"
                continue
            import time
            time.sleep(5 * (attempt + 1))
    if err:
        raise RuntimeError(err)
    res = score_codemix(item, rec.log)
    kbench.actors.system.send("GOVBENCH_RESULT " + json.dumps({
        "id": item["id"], "pair_id": item["pair_id"], "lang": item["lang"], "kind": item["kind"],
        **res, "calls": rec.log}, ensure_ascii=False))
    kbench.assertions.assert_true(res["passed"], expectation=f"[{item['lang']}/{item['kind']}] {item['intent']} ({item['id']})")
    return bool(res["passed"])


@kbench.task(name="__TASK_NAME__", description=(
    "Does an agent pick the right tool and arguments when the same request is written in English, Tanglish "
    "(Tamil-English) or Manglish (Malayalam-English)? 30 matched triples, policy in prompt. Score = mean pass rate "
    "over the two code-mixed languages; the summary reports the gap to English."))
def codemix_task(llm) -> float:
    items = load_items("codemix_items.jsonl")
    df = pd.DataFrame({"item_json": [json.dumps(i, ensure_ascii=False) for i in items]})
    os.environ["RENDER_SUBRUNS"] = "False"
    runs = codemix_item.evaluate(llm=[llm], evaluation_data=df, n_jobs=int(os.environ.get("GOVBENCH_JOBS", "6")),
                                 timeout=900, on_failure="continue")
    ok = {i["id"]: bool(r.status == kbench.utils.Status.SUCCESS and r.result is True) for i, r in zip(items, runs)}
    by = collections.defaultdict(list)
    for i in items:
        by[(i["lang"], i["kind"])].append(ok[i["id"]])
    rate = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    lang = {l: rate([v for (ll, _), vs in by.items() if ll == l for v in vs]) for l in ("en", "ta-en", "ml-en")}
    mixed = [ok[i["id"]] for i in items if i["lang"] != "en"]
    summary = {"bench": BENCH_VERSION, "task": "codemix", "n": len(items),
               "errored": sum(1 for r in runs if r.status != kbench.utils.Status.SUCCESS),
               "pass_by_lang": lang, "pass_by_lang_kind": {f"{l}/{k}": rate(v) for (l, k), v in by.items()},
               "gap_en_minus_mixed": lang["en"] - rate(mixed)}
    print("GOVBENCH_SUMMARY " + json.dumps(summary))
    try:
        json.dump(summary, open("govbench_summary.json", "w"))
    except OSError:
        pass
    return float(rate(mixed))


codemix_task.run(kbench.llm)
