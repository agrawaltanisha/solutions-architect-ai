
import os, json, re, operator, time
from datetime import datetime
from typing import TypedDict, List, Annotated
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
from langgraph.graph import StateGraph, END
import nest_asyncio
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
GROQ_MODEL_PRIMARY  = "llama-3.3-70b-versatile"
GROQ_MODEL_FALLBACK = "llama-3.1-8b-instant"

def call_groq(system_prompt, user_message, temperature=0.5, model=GROQ_MODEL_PRIMARY):
    for attempt, m in enumerate([model, GROQ_MODEL_FALLBACK]):
        try:
            resp = groq_client.chat.completions.create(
                model=m, temperature=temperature, max_tokens=2048,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                time.sleep(5)
                continue
            raise

class MCPMermaidServer:
    COMPONENTS = {
        "user":            ("U",   "circle",   "User"),
        "mobile client":   ("MC",  "rect",     "Mobile Client"),
        "cdn":             ("CDN", "rect",     "CDN"),
        "load balancer":   ("LB",  "stadium",  "Load Balancer"),
        "api gateway":     ("AG",  "rect",     "API Gateway"),
        "auth service":    ("AU",  "rounded",  "Auth Service"),
        "web server":      ("WS",  "rect",     "Web Server"),
        "app server":      ("AS",  "rect",     "App Server"),
        "microservice":    ("MS",  "rounded",  "Microservice"),
        "cache":           ("CH",  "stadium",  "Cache / Redis"),
        "database":        ("DB",  "cylinder", "Primary DB"),
        "replica":         ("RDB", "cylinder", "DB Replica"),
        "message queue":   ("MQ",  "stadium",  "Message Queue"),
        "object storage":  ("OS",  "cylinder", "Object Storage"),
        "notification":    ("NS",  "rounded",  "Notification Svc"),
        "search":          ("SE",  "rounded",  "Search Engine"),
        "payment service": ("PS",  "rounded",  "Payment Service"),
        "analytics":       ("AN",  "rounded",  "Analytics"),
        "monitoring":      ("MO",  "rect",     "Monitoring"),
        "rate limiter":    ("RL",  "rounded",  "Rate Limiter"),
    }
    EDGES = [
        ("U","MC","opens app"),("U","CDN","static assets"),("MC","CDN","static assets"),
        ("CDN","LB","dynamic traffic"),("U","LB","HTTPS"),("MC","LB","HTTPS"),
        ("LB","AG","route"),("LB","WS","route"),("AG","AU","authenticate"),
        ("AG","RL","rate limit"),("AG","WS","forward"),("AG","MS","forward"),
        ("WS","AS","internal RPC"),("AS","CH","cache r/w"),("AS","DB","read/write"),
        ("DB","RDB","replication"),("AS","MQ","publish event"),("MQ","NS","trigger"),
        ("MQ","AN","stream"),("AS","SE","search query"),("AS","PS","payment"),
        ("AS","OS","upload/fetch"),("MS","DB","query"),("MS","CH","cache"),
        ("MO","DB","metrics"),("MO","AS","health check"),
    ]

    def generate_architecture_diagram(self, description, components):
        try:
            mermaid = self._build(description, components)
            errors, warnings = self._validate(mermaid)
            return {
                "mermaid_code": mermaid,
                "validation_status": "PASS" if not errors else "FAIL",
                "warnings": warnings,
                "renderable": len(errors) == 0
            }
        except Exception as exc:
            return {"mermaid_code": "", "validation_status": "ERROR",
                    "validation_errors": [str(exc)], "warnings": [], "renderable": False}

    def _build(self, description, components):
        desc_lower = (description + " " + " ".join(components)).lower()
        matched, seen_ids = [], set()
        for key, (nid, shape, label) in self.COMPONENTS.items():
            if key in desc_lower and nid not in seen_ids:
                matched.append((nid, shape, label))
                seen_ids.add(nid)
        for nid, shape, label in [("U","circle","User"),("LB","stadium","Load Balancer"),
                                   ("AS","rect","App Server"),("DB","cylinder","Primary DB")]:
            if nid not in seen_ids:
                matched.append((nid, shape, label))
                seen_ids.add(nid)
        shape_syntax = {
            "circle":   ("((", "))"),
            "stadium":  ("([", "])"),
            "cylinder": ("[(", ")]"),
            "rounded":  ("(",  ")"),
            "rect":     ("[",  "]"),
        }
        lines = ["graph TD"]
        for nid, shape, label in matched:
            o, c = shape_syntax.get(shape, ("[", "]"))
            lines.append("    " + nid + o + label + c)
        lines.append("")
        added = set()
        for src, dst, lbl in self.EDGES:
            if src in seen_ids and dst in seen_ids and (src, dst) not in added:
                lines.append("    " + src + " -->|" + lbl + "| " + dst)
                added.add((src, dst))
        prev = None
        for nid, _, _ in matched:
            if prev and (prev, nid) not in added and (nid, prev) not in added:
                lines.append("    " + prev + " --> " + nid)
            prev = nid
        lines += [
            "",
            "    classDef db      fill:#7c3aed,stroke:#a78bfa,color:#fff",
            "    classDef cache   fill:#0369a1,stroke:#38bdf8,color:#fff",
            "    classDef lb      fill:#15803d,stroke:#4ade80,color:#fff",
            "    classDef queue   fill:#b45309,stroke:#fbbf24,color:#fff",
            "    classDef default fill:#1e293b,stroke:#475569,color:#e2e8f0",
        ]
        db_ids    = [n for n, s, _ in matched if s == "cylinder"]
        cache_ids = [n for n, _, l in matched if "cache" in l.lower()]
        lb_ids    = [n for n, _, l in matched if "load" in l.lower()]
        mq_ids    = [n for n, _, l in matched if "queue" in l.lower()]
        if db_ids:    lines.append("    class " + ",".join(db_ids) + " db")
        if cache_ids: lines.append("    class " + ",".join(cache_ids) + " cache")
        if lb_ids:    lines.append("    class " + ",".join(lb_ids) + " lb")
        if mq_ids:    lines.append("    class " + ",".join(mq_ids) + " queue")
        return "\n".join(lines)

    def _validate(self, code):
        errors, warnings = [], []
        lines = [l.strip() for l in code.strip().splitlines() if l.strip()]
        if not lines:
            errors.append("Empty diagram")
            return errors, warnings
        if not any(lines[0].startswith(v) for v in ("graph", "flowchart", "sequenceDiagram")):
            errors.append("Invalid header: " + lines[0])
        if not [l for l in lines if "-->" in l]:
            warnings.append("No edges found")
        return errors, warnings

mcp_server = MCPMermaidServer()

class DesignDocumentState(TypedDict):
    user_prompt: str
    executive_summary: str
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    system_components: List[str]
    architecture_description: str
    mermaid_diagram: str
    diagram_validation_status: str
    diagram_warnings: List[str]
    risks_identified: List[str]
    spof_detected: bool
    critic_feedback: str
    critic_final_signoff: str
    revision_count: int
    max_revisions: int
    iteration_log: Annotated[List[str], operator.add]

ANALYST_SYS = (
    "You are a Principal Solutions Architect. Transform the prompt into specs. "
    "Output ONLY valid JSON, no markdown fences: "
    '{"executive_summary":"...","functional_requirements":["FR-01: ..."],'
    '"non_functional_requirements":["NFR-01 Availability: 99.99%"],'
    '"system_components":["load balancer","api gateway","cache","database","message queue"]} '
    "Rules: min 8 FRs, min 6 NFRs, system_components in lowercase."
)

DIAGRAMMER_SYS = (
    "You are a Cloud Architect. Design the optimal infrastructure. "
    "Output ONLY valid JSON, no markdown fences: "
    '{"architecture_description":"...","component_list":["user","load balancer","api gateway","cache","database"]} '
    "Use lowercase component names. If revising, address all critic SPOFs."
)

CRITIC_SYS = (
    "You are a Senior SRE. Find every weakness in the architecture. "
    "Output ONLY valid JSON, no markdown fences: "
    '{"risks":["RISK-01 [SPOF] ..."],"spof_detected":true,"critic_feedback":"...","final_signoff":"REVISION REQUIRED: ..."} '
    "Set spof_detected true only if unmitigated SPOF exists. Provide at least 4 risks."
)

def parse_json(raw):
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"{[\s\S]+}", raw)
        return json.loads(m.group()) if m else {}

def agent_requirement_analyst(state):
    prompt = state["user_prompt"]
    raw  = call_groq(ANALYST_SYS, "Design prompt: " + prompt, 0.3)
    data = parse_json(raw)
    log  = "[" + datetime.now().strftime("%H:%M:%S") + "] Agent 1 done"
    return {
        "executive_summary":          data.get("executive_summary", ""),
        "functional_requirements":    data.get("functional_requirements", []),
        "non_functional_requirements":data.get("non_functional_requirements", []),
        "system_components":          data.get("system_components", []),
        "iteration_log":              [log],
    }

def agent_diagrammer(state):
    rev = state.get("revision_count", 0)
    frs  = "\n".join(state.get("functional_requirements", []))
    nfrs = "\n".join(state.get("non_functional_requirements", []))
    msg  = "Prompt: " + state["user_prompt"] + "\nFRs:\n" + frs + "\nNFRs:\n" + nfrs
    if rev > 0 and state.get("critic_feedback"):
        msg += "\nCRITIC FEEDBACK:\n" + state["critic_feedback"]
    raw  = call_groq(DIAGRAMMER_SYS, msg, 0.4)
    data = parse_json(raw)
    components = data.get("component_list", state.get("system_components", []))
    arch_desc  = data.get("architecture_description", state["user_prompt"])
    mcp = mcp_server.generate_architecture_diagram(
        arch_desc + " " + " ".join(components), components
    )
    log = "[" + datetime.now().strftime("%H:%M:%S") + "] Agent 2 revision #" + str(rev) + " done"
    return {
        "architecture_description":  arch_desc,
        "mermaid_diagram":           mcp["mermaid_code"],
        "diagram_validation_status": mcp["validation_status"],
        "diagram_warnings":          mcp.get("warnings", []),
        "system_components":         components,
        "revision_count":            rev + 1,
        "iteration_log":             [log],
    }

def agent_critic(state):
    components = ", ".join(state.get("system_components", []))
    nfrs       = "\n".join(state.get("non_functional_requirements", []))
    msg = (
        "Prompt: " + state["user_prompt"] +
        "\nArch: " + state.get("architecture_description", "") +
        "\nDiagram:\n" + state.get("mermaid_diagram", "") +
        "\nComponents: " + components +
        "\nNFRs:\n" + nfrs
    )
    raw  = call_groq(CRITIC_SYS, msg, 0.5)
    data = parse_json(raw)
    log  = "[" + datetime.now().strftime("%H:%M:%S") + "] Agent 3 done"
    return {
        "risks_identified":    data.get("risks", []),
        "spof_detected":       bool(data.get("spof_detected", False)),
        "critic_feedback":     data.get("critic_feedback", ""),
        "critic_final_signoff":data.get("final_signoff", ""),
        "iteration_log":       [log],
    }

def route_after_critic(state):
    if state.get("spof_detected") and state.get("revision_count", 0) < state.get("max_revisions", 3):
        return "revise"
    return "finalize"

builder = StateGraph(DesignDocumentState)
builder.add_node("requirement_analyst", agent_requirement_analyst)
builder.add_node("diagrammer",          agent_diagrammer)
builder.add_node("critic",              agent_critic)
builder.set_entry_point("requirement_analyst")
builder.add_edge("requirement_analyst", "diagrammer")
builder.add_edge("diagrammer",          "critic")
builder.add_conditional_edges("critic", route_after_critic, {"revise": "diagrammer", "finalize": END})
pipeline = builder.compile()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/design", methods=["POST"])
def design():
    data   = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    try:
        result = pipeline.invoke({
            "user_prompt": prompt,
            "executive_summary": "", "functional_requirements": [],
            "non_functional_requirements": [], "system_components": [],
            "architecture_description": "", "mermaid_diagram": "",
            "diagram_validation_status": "", "diagram_warnings": [],
            "risks_identified": [], "spof_detected": False,
            "critic_feedback": "", "critic_final_signoff": "",
            "revision_count": 0, "max_revisions": 3, "iteration_log": [],
        })
        return jsonify({
            "executive_summary":           result.get("executive_summary", ""),
            "functional_requirements":     result.get("functional_requirements", []),
            "non_functional_requirements": result.get("non_functional_requirements", []),
            "mermaid_diagram":             result.get("mermaid_diagram", ""),
            "architecture_description":    result.get("architecture_description", ""),
            "risks_identified":            result.get("risks_identified", []),
            "critic_final_signoff":        result.get("critic_final_signoff", ""),
            "revision_count":              result.get("revision_count", 0),
            "spof_detected":               result.get("spof_detected", False),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
