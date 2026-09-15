"""Model-independent task contracts; decision support, never action authorization."""
import math

VERSION = "DAKSH-OP-001/v1"
STAGES = [
    ("Understand context", "Identify scope, entity, objective, evidence, constraints and acceptance criteria. Separate facts, assumptions and unknowns."),
    ("Isolate the problem", "State the core obstacle and distinguish symptoms. Ask only for missing facts that change the decision."),
    ("Evaluate risk", "Compare alternatives, reversibility, worst-case loss and user tolerance. Expected loss is probability times loss; unknowns remain unknown."),
    ("Question requirements", "Identify each requirement, its purpose and evidence. Do not discard legal obligations, authorization boundaries or security controls."),
    ("Propose deletion", "Remove redundant work from the plan. Actual deletion of user data requires explicit authorization and a recoverable backup."),
    ("Simplify and optimize", "Choose the smallest reliable workflow and use deterministic calculations where available."),
    ("Accelerate", "Use small iterations and reusable outputs without skipping checks or approvals."),
    ("Map and execute", "Define concrete deliverables, dependencies, tool scope, checkpoints and stop conditions. Execute only with available authorized tools."),
    ("Verify", "Check evidence, calculations and actual output. Distinguish planned, attempted, verified and blocked; never invent tool success."),
    ("Automate and learn", "Automate only a tested workflow with bounded permissions, retries, deduplication, audit and a stop switch. Save explicit memory only on user request."),
]
ROUTES = {
    "general": "Local chat and scoped memory/RAG; clarify missing evidence.",
    "research": "Scoped documents first; current public sources only through a separately configured web tool. No live web capability is implied.",
    "finance": "Deterministic Finance for calculations; local business templates for drafts. Confirm period, currency, entity and jurisdiction.",
    "coding": "Task plan and reviewed repository changes; coding/browser tools require separately configured bounded access.",
    "communications": "Existing allowlisted connectors and approval queue; Gmail drafts only, Calendar read-only. No send permission is implied.",
}
PROMPT = (
    "Follow DAKSH-OP-001 proportionately: understand context and isolate the core problem; separate facts, assumptions and unknowns; "
    "evaluate alternatives, worst-case risk and reversibility without inventing probabilities; question requirements, propose removing redundancy, "
    "simplify, then accelerate; define deliverables and checks before automation. Use local evidence and deterministic calculations when possible. "
    "A plan is not execution or authorization. Only verified tool results establish completed actions. Never claim unavailable capabilities. "
    "Give concise decision summaries, not private reasoning traces. Keep a simple answer simple. "
)

def contract(data, scope):
    goal = str(data.get("goal", "")).strip()
    if not goal or len(goal) > 8000:
        raise ValueError("Provide a goal of 1–8000 characters.")
    domain = data.get("domain", "general")
    if domain not in ROUTES:
        raise ValueError("Choose a supported domain.")
    context = str(data.get("context", ""))
    if len(context) > 12000:
        raise ValueError("Context is limited to 12000 characters.")
    risk = {"expected_loss": None, "assessment": "Unknown: supply probability, loss and tolerance; do not infer them."}
    supplied = [data.get(k) for k in ("probability", "loss", "tolerance")]
    if any(x is not None and x != "" for x in supplied):
        if any(x is None or x == "" for x in supplied):
            raise ValueError("Risk calculation needs probability, loss and tolerance together.")
        probability, loss, tolerance = map(float, supplied)
        if not all(math.isfinite(x) for x in (probability, loss, tolerance)) or not 0 <= probability <= 1 or min(loss, tolerance) < 0:
            raise ValueError("Probability must be 0–1; loss and tolerance must be finite non-negative amounts in the same currency.")
        risk = {"expected_loss": probability * loss, "worst_case_loss": loss, "tolerance": tolerance,
                "assessment": "Worst-case exceeds tolerance; revise or escalate." if loss > tolerance else "Worst-case is within supplied tolerance; this does not grant approval."}
    result = {"protocol": VERSION, "scope": scope, "goal": goal, "domain": domain,
              "context": context, "route": ROUTES[domain], "risk": risk,
              "status": "planned", "stages": [{"name": a, "check": b} for a,b in STAGES],
              "acceptance": "Define the observable output and evidence needed before execution.",
              "authorization": "No new permissions. External messages, submissions, destructive actions and expanded access require applicable explicit approval.",
              "handoff": {"facts": [], "assumptions": [], "sources": [], "decisions": [], "artifacts": [], "checks": [], "pending": [], "next_action": "Complete context and acceptance criteria."}}
    result["markdown"] = "# DAKSH task contract\n\n" + "\n\n".join(f"**{k}:** {result[k]}" for k in ("protocol","scope","goal","domain","context","route","status","acceptance","authorization")) + "\n\n## Risk\n\n" + str(risk) + "\n\n## Process\n\n" + "\n".join(f"{i}. **{a}** — {b}" for i,(a,b) in enumerate(STAGES,1)) + "\n\n## Handoff\n\nFacts / Assumptions / Sources / Decisions / Artifacts / Checks performed / Checks not performed / Pending approvals / Next action. Fill these with verified results before handing off.\n"
    return result
