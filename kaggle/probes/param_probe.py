# %%
import json

import kaggle_benchmarks as kbench


def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b


@kbench.task(name="govbench_probe_params")
def probe(llm) -> bool:
    """Which output-cap parameter names does the Model Proxy accept, and do tools work with reasoning='none'?"""
    out = {}
    for label, kw, extra in [
        ("max_tokens", {}, {"max_tokens": 64}),
        ("max_completion_tokens", {}, {"max_completion_tokens": 64}),
        ("max_output_tokens", {}, {"max_output_tokens": 64}),
        ("tools_reason_none_cap", {"tools": [add], "reasoning": "none"}, {"max_completion_tokens": 512}),
        ("tools_cap_default_reasoning", {"tools": [add]}, {"max_completion_tokens": 512}),
    ]:
        try:
            with kbench.chats.new("p-" + label):
                r = llm.prompt("What is 2+3? Use the tool if you have one.", extra_api_params=extra, **kw)
            out[label] = "ok:" + str(r)[:40]
        except Exception as e:  # noqa: BLE001
            out[label] = "ERR:" + (type(e).__name__ + str(e))[:160]
    kbench.actors.system.send("GOVBENCH_RESULT " + json.dumps(out))
    kbench.assertions.assert_true(True, expectation="probe finished")
    return True


probe.run(kbench.llm)
