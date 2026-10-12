"""Deploy (create or update) the GovBench agent to Agent Runtime with Agent Identity, no gateway.

Run with the agent env:  uv run --project infra/codelab/src/mortgage-agent python agent/deploy.py [--update NAME]
Settings come from agent/local.env and flags; nothing project-specific is hardcoded here.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SHIPPED = ["__init__.py", "policy.py", "rules_g2.py", "guard_llm.py", "guard_ma.py", "convo.py", "world.py"]
REQUIREMENTS = [
    "google-cloud-aiplatform[agent_engines]>=1.149.0,<1.154.0",
    "google-adk[agent-identity]==1.34.0",
    "google-auth>=2.0",
    "httpx",
    "cloudpickle",
    "pydantic",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", default=None, help="existing reasoningEngine resource name")
    ap.add_argument("--display-name", default="govbench-agent")
    ap.add_argument("--min-instances", type=int, default=0)
    ap.add_argument("--max-instances", type=int, default=10)
    ap.add_argument("--cpu", default="1")
    ap.add_argument("--memory", default="2Gi")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()

    project = os.environ["GOVBENCH_PROJECT"]
    region = os.environ.get("GOVBENCH_REGION", "us-central1")
    staging = os.environ.get("GOVBENCH_STAGING", f"gs://{project}-staging")
    env = {k: os.environ[k] for k in ("GOVBENCH_TOOLS_URL", "GOVBENCH_INVOKER_SA", "GOVBENCH_PROJECT")}
    env.update({
        "GOVBENCH_AGENT_MODEL": os.environ.get("GOVBENCH_AGENT_MODEL", "gemini-3.8-flash"),
        "GOVBENCH_GUARD_MODEL": os.environ.get("GOVBENCH_GUARD_MODEL", "gemini-3.8-flash"),
        "GOVBENCH_MA_TEMPLATE": os.environ.get("GOVBENCH_MA_TEMPLATE", "govbench-basic"),
        "GOVBENCH_MA_LOCATION": region,
        "GOOGLE_GENAI_USE_VERTEXAI": "True",
        "GOOGLE_CLOUD_LOCATION": "global",
        "ADK_ENABLE_MCP_GRACEFUL_ERROR_HANDLING": "true",
        "GOOGLE_API_PREVENT_AGENT_TOKEN_SHARING_FOR_GCP_SERVICES": "false",
    })

    stage = tempfile.mkdtemp(prefix="govbench_deploy_")
    shutil.copytree(os.path.join(HERE, "govbench_agent"), os.path.join(stage, "govbench_agent"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    os.makedirs(os.path.join(stage, "agent_govbench"))
    for f in SHIPPED:
        shutil.copy(os.path.join(REPO, "src", "agent_govbench", f), os.path.join(stage, "agent_govbench", f))
    sys.path.insert(0, stage)
    os.environ.update(env)
    cwd = os.getcwd()
    os.chdir(stage)
    try:
        import vertexai
        from vertexai.agent_engines import AdkApp

        from govbench_agent.agent import root_agent

        vertexai.init(project=project, location=region, staging_bucket=staging)
        client = vertexai.Client(project=project, location=region, http_options=dict(api_version="v1beta1"))
        app = AdkApp(agent=root_agent, enable_tracing=False)
        config = dict(
            staging_bucket=staging, requirements=REQUIREMENTS, extra_packages=["govbench_agent", "agent_govbench"],
            env_vars=env, display_name=args.display_name,
            description="GovBench Northwind Ops Assistant (no gateway)",
            min_instances=args.min_instances, max_instances=args.max_instances,
            resource_limits={"cpu": args.cpu, "memory": args.memory}, container_concurrency=args.concurrency,
            identity_type="AGENT_IDENTITY", labels={"project": "agent-govbench"},
        )
        if args.update:
            eng = client.agent_engines.update(name=args.update, agent=app, config=config)
        else:
            eng = client.agent_engines.create(agent=app, config=config)
        r = eng.api_resource
        print("ENGINE", r.name)
        print("IDENTITY", getattr(r.spec, "effective_identity", None))
    finally:
        os.chdir(cwd)
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    main()
