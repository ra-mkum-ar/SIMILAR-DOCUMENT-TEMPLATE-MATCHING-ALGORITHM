from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Tuple
import uuid
from datetime import datetime, timezone
import PyPDF2
from docx import Document
import io
import json
import difflib
import re
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer

# ------------------ ENV + CONFIG ------------------

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# Embedding model (local)
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Weights for final similarity score
WEIGHTS = {
    "text": 0.60,
    "structure": 0.25,
    "layout": 0.15,
}

# ------------------ FASTAPI APP ------------------

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ------------------ MODELS ------------------

class Template(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    file_path: str
    file_type: str
    content: str
    structure_data: Dict[str, Any]
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_size: int
    embedding: List[float] = Field(default_factory=list)


class TemplateResponse(BaseModel):
    id: str
    name: str
    file_type: str
    upload_date: str
    file_size: int


class MatchResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_doc_name: str
    matched_templates: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimilarityScore(BaseModel):
    template_id: str
    template_name: str
    overall_score: float
    text_similarity: float
    structure_similarity: float
    layout_similarity: float
    analysis: str
    is_duplicate: bool = False
    confidence: float = 0.0          # general similarity confidence
    forgery_risk: float = 0.0        # 0–1: probability-of-forgery
    forgery_label: str = "LOW"       # LOW / MEDIUM / HIGH
    fraud_confidence: float = 0.0    # alias of forgery_risk for UI
    classification: str = "UNCLASSIFIED"  # DUPLICATE / FORGERY_LIKELY / TEMPLATE_REUSE / MODIFIED_COPY / UNRELATED / PARTIAL_MATCH
    field_differences: List[Dict[str, Any]] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

# ------------------ UTILS: BASIC SIMILARITY ------------------

def lexical_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a[:8000], b[:8000]).ratio()


def encode_embedding(text: str) -> np.ndarray:
    # Truncate very long documents for speed
    return embed_model.encode(text[:8000], convert_to_numpy=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    sim = float(np.dot(a, b) / denom)
    # Map from [-1, 1] → [0, 1]
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


def structure_score(q: Dict[str, Any], t: Dict[str, Any]) -> float:
    score = 0.0

    # Page / paragraph count similarity
    qp = q.get("pages", len(q.get("paragraphs", [])))
    tp = t.get("pages", len(t.get("paragraphs", [])))
    if qp and tp:
        score += min(qp, tp) / max(qp, tp)

    # Heading similarity
    qh = set(map(str.lower, q.get("headings", [])))
    th = set(map(str.lower, t.get("headings", [])))
    if qh and th:
        score += len(qh & th) / max(len(qh | th), 1)

    score = round(score / 2, 3)
    return max(score, 0.05)


def layout_score(q: Dict[str, Any], t: Dict[str, Any]) -> float:
    # Page count similarity
    q_pages = q.get("pages", len(q.get("paragraphs", [])))
    t_pages = t.get("pages", len(t.get("paragraphs", [])))
    page_score = min(q_pages, t_pages) / max(q_pages, t_pages, 1) if (q_pages and t_pages) else 0.0

    # Density by average text length per page / paragraph
    q_items = q.get("page_data", q.get("paragraphs", []))
    t_items = t.get("page_data", t.get("paragraphs", []))

    def avg_len(items):
        if not items:
            return 0
        return sum(x.get("length", 0) for x in items) / max(len(items), 1)

    q_avg = avg_len(q_items)
    t_avg = avg_len(t_items)

    if q_avg and t_avg:
        density_score = min(q_avg, t_avg) / max(q_avg, t_avg)
    else:
        density_score = 0.0

    score = round((page_score + density_score) / 2, 3)
    return max(score, 0.0)


def confidence_score(q_text: str, t_text: str, text_sim: float) -> float:
    q_len = len(q_text)
    t_len = len(t_text)
    if q_len == 0 or t_len == 0:
        length_conf = 0.0
    else:
        length_conf = min(q_len, t_len) / max(q_len, t_len)
    return round(0.5 * length_conf + 0.5 * text_sim, 3)

# ------------------ UTILS: FORGERY / FRAUD LOGIC ------------------

def forgery_risk_score(
    text_sim: float,
    struct_sim: float,
    layout_sim: float,
    is_dup: bool,
) -> Tuple[float, str]:
    """
    Heuristics for forgery risk:
    - High layout + structure, but text changed => suspicious.
    - Perfect duplicates => low risk (reupload).
    """
    if is_dup:
        return 0.1, "LOW"

    risk = 0.1
    label = "LOW"

    # Strong forgery pattern: template cloned, key text changed
    if layout_sim >= 0.9 and struct_sim >= 0.8 and 0.2 <= text_sim <= 0.85:
        risk = 0.9
        label = "HIGH"
    # Medium: mostly same template, partial text changes
    elif layout_sim >= 0.8 and struct_sim >= 0.6 and 0.3 <= text_sim <= 0.9:
        risk = 0.6
        label = "MEDIUM"
    # Low but non-zero: moderate structure/layout with lower text
    elif layout_sim >= 0.6 and struct_sim >= 0.5 and text_sim <= 0.8:
        risk = 0.35
        label = "LOW"

    return round(risk, 3), label


def classify_match(
    text_sim: float,
    struct_sim: float,
    layout_sim: float,
    is_dup: bool,
    forgery_label: str,
) -> str:
    if is_dup:
        return "DUPLICATE"

    if forgery_label == "HIGH":
        return "FORGERY_LIKELY"
    if forgery_label == "MEDIUM":
        return "TEMPLATE_REUSE"

    # Modified copy of same or similar document
    if text_sim >= 0.75 and layout_sim >= 0.7:
        return "MODIFIED_COPY"

    # Completely unrelated
    if text_sim < 0.3 and layout_sim < 0.4:
        return "UNRELATED"

    return "PARTIAL_MATCH"


def generate_red_flags(
    text_sim: float,
    struct_sim: float,
    layout_sim: float,
    is_dup: bool,
    forgery_label: str,
    classification: str,
    field_diffs: List[Dict[str, Any]],
) -> List[str]:
    flags: List[str] = []

    if is_dup:
        flags.append("Exact or near-exact duplicate of the template.")
        return flags

    if forgery_label == "HIGH":
        flags.append("Template/layout nearly identical but content has been changed.")
    elif forgery_label == "MEDIUM":
        flags.append("Template reused with some modified fields.")

    if layout_sim >= 0.9 and text_sim < 0.8:
        flags.append("High layout similarity but lower text similarity – template reuse suspected.")

    # Field-level flags
    high_changed = [f for f in field_diffs if f.get("importance") == "high" and f.get("status") == "changed"]
    missing_critical = [f for f in field_diffs if f.get("importance") == "high" and f.get("status") == "missing"]

    if high_changed:
        names = ", ".join({f.get("field", "") for f in high_changed})
        flags.append(f"High-importance fields changed: {names}.")
    if missing_critical:
        names = ", ".join({f.get("field", "") for f in missing_critical})
        flags.append(f"Critical fields missing in template/query: {names}.")

    if classification == "FORGERY_LIKELY":
        flags.append("Overall behaviour matches forgery pattern (same invoice design, altered details).")

    return flags

# ------------------ EXTRACTION ------------------

def extract_text_from_pdf(file_content: bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    structure = {"pages": len(reader.pages), "page_data": []}

    for i, page in enumerate(reader.pages):
        content = page.extract_text() or ""
        text += content + "\n"
        structure["page_data"].append({
            "page": i + 1,
            "length": len(content),
            "preview": content[:200]
        })

    return text, structure


def extract_text_from_docx(file_content: bytes):
    doc = Document(io.BytesIO(file_content))
    text = ""
    structure = {"paragraphs": [], "headings": []}

    for p in doc.paragraphs:
        text += p.text + "\n"
        structure["paragraphs"].append({"length": len(p.text), "preview": p.text[:200]})
        if p.style.name.startswith("Heading"):
            structure["headings"].append(p.text)

    return text, structure

# ------------------ GROQ AI: SINGLE DOC ANALYSIS ------------------

async def analyze_document_with_ai(content, structure, file_type):
    prompt = f"""
You are an expert document classifier and analyzer.

Return STRICT JSON ONLY. No markdown, no text.

Analyze the following document:

FILE TYPE: {file_type}
STRUCTURE:
{json.dumps(structure)}

TEXT (first 6000 chars):
{content[:6000]}

Return exactly this JSON:
{{
 "content_themes": [],
 "document_type": "",
 "key_sections": [],
 "writing_style": "",
 "structure_pattern": "",
 "summary": ""
}}
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You analyze invoices, medical records, and official documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.15,
            max_tokens=1200,
            timeout=30
        )

        raw = response.choices[0].message.content.strip()

        # Harden JSON extraction
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            raise ValueError("No JSON block returned by Groq")

        data = json.loads(match.group())

        # Enforce structure
        return {
            "content_themes": data.get("content_themes", []),
            "document_type": data.get("document_type", "Unknown"),
            "key_sections": data.get("key_sections", []),
            "writing_style": data.get("writing_style", "Unknown"),
            "structure_pattern": data.get("structure_pattern", "Unknown"),
            "summary": data.get("summary", "No summary generated")
        }

    except Exception as e:
        logging.error(f"[AI ANALYSIS ERROR] {e}")
        return {
            "content_themes": [],
            "document_type": "Unknown",
            "key_sections": [],
            "writing_style": "Unknown",
            "structure_pattern": "Unknown",
            "summary": "AI analysis failed"
        }

# ------------------ GROQ AI: FIELD-LEVEL DIFFERENCES ------------------

async def extract_field_differences(
    query_content: str,
    template_content: str,
    template_name: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Ask Groq to find field-level changes between two invoice-like documents.
    """
    prompt = f"""
You compare a QUERY invoice-like document to a TEMPLATE invoice document named "{template_name}".

Extract and compare key fields such as:
- patient_name / customer_name
- date_of_birth
- invoice_number / bill_number
- invoice_date / service_date
- total_amount / amount_due
- hospital_name / provider_name
- address
- policy_number / id_number

Return STRICT JSON ONLY with this schema:

{{
  "fields": [
    {{
      "field": "patient_name",
      "status": "same" | "changed" | "missing" | "extra",
      "template_value": "string or null",
      "query_value": "string or null",
      "importance": "high" | "medium" | "low"
    }}
  ],
  "red_flags": [
    "short natural-language red flag, e.g. 'Name differs but layout identical'"
  ]
}}

QUERY DOCUMENT (first 4000 chars):
{query_content[:4000]}

TEMPLATE DOCUMENT (first 4000 chars):
{template_content[:4000]}
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a forensic invoice fraud analyst. Respond with strict JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=900,
        )
        raw = response.choices[0].message.content.strip()
        block = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(block.group() if block else raw)

        fields = data.get("fields", [])
        red_flags = data.get("red_flags", [])
        return fields, red_flags

    except Exception:
        # On failure, just return empty; main similarity still works
        return [], []

# ------------------ SIMILARITY (EMBEDDING + LLM + FORENSICS) ------------------

async def calculate_similarity(
    query_content: str,
    query_structure: Dict[str, Any],
    template_content: str,
    template_structure: Dict[str, Any],
    template_name: str,
    template_id: str,
    base_text_similarity: float
):
    base_struct = structure_score(query_structure, template_structure)
    base_layout = layout_score(query_structure, template_structure)

    prompt = f"""
RETURN JSON ONLY. NO MARKDOWN, NO EXTRA TEXT.

You compare a QUERY document with a TEMPLATE document.

Your job:
- Refine similarity scores (but keep them close to numeric baselines).
- Explain similarities and differences.
- Mention if this looks like a forgery: template reused with edited key fields.

Numeric baselines (0-1 scale, use as strong hints):
- base_text_similarity: {base_text_similarity:.3f}
- base_structure_similarity: {base_struct:.3f}
- base_layout_similarity: {base_layout:.3f}

QUERY STRUCTURE:
{json.dumps(query_structure)}

QUERY CONTENT (first 6000 chars):
{query_content[:6000]}

TEMPLATE NAME:
{template_name}

TEMPLATE STRUCTURE:
{json.dumps(template_structure)}

TEMPLATE CONTENT (first 6000 chars):
{template_content[:6000]}

Return JSON exactly:
{{
  "text_similarity": 0.0,
  "structure_similarity": 0.0,
  "layout_similarity": 0.0,
  "analysis": ""
}}
"""

    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a rigorous document similarity and forgery detection engine "
                               "for invoices and official records."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )

        raw = response.choices[0].message.content.strip()
        block = re.search(r"\{.*\}", raw, re.DOTALL)
        scores = json.loads(block.group() if block else raw)

        # Safe defaults
        scores.setdefault("analysis", "No explanation provided.")
        scores.setdefault("text_similarity", base_text_similarity)
        scores.setdefault("structure_similarity", base_struct)
        scores.setdefault("layout_similarity", base_layout)

        # Floors based on numeric similarity
        scores["text_similarity"] = round(max(scores["text_similarity"], base_text_similarity), 3)
        scores["structure_similarity"] = round(max(scores["structure_similarity"], base_struct), 3)
        scores["layout_similarity"] = round(max(scores["layout_similarity"], base_layout), 3)

        # Confidence & duplicate detection
        conf = confidence_score(query_content, template_content, scores["text_similarity"])
        duplicated = (
            scores["text_similarity"] >= 0.92
            and scores["structure_similarity"] >= 0.85
            and scores["layout_similarity"] >= 0.80
        )

        # Forgery risk estimation
        risk, label = forgery_risk_score(
            scores["text_similarity"],
            scores["structure_similarity"],
            scores["layout_similarity"],
            duplicated
        )

        # Classification (fraud vs normal)
        classification = classify_match(
            scores["text_similarity"],
            scores["structure_similarity"],
            scores["layout_similarity"],
            duplicated,
            label,
        )

        # Field-level differences only when documents are somewhat structurally similar
        field_diffs: List[Dict[str, Any]] = []
        extra_flags: List[str] = []
        if scores["layout_similarity"] >= 0.7 or scores["structure_similarity"] >= 0.6:
            field_diffs, extra_flags = await extract_field_differences(
                query_content, template_content, template_name
            )

        # Red flags
        red_flags = generate_red_flags(
            scores["text_similarity"],
            scores["structure_similarity"],
            scores["layout_similarity"],
            duplicated,
            label,
            classification,
            field_diffs,
        )
        red_flags.extend(extra_flags)

        scores["confidence"] = conf
        scores["is_duplicate"] = duplicated
        scores["forgery_risk"] = risk
        scores["forgery_label"] = label
        scores["fraud_confidence"] = risk
        scores["classification"] = classification
        scores["field_differences"] = field_diffs
        scores["red_flags"] = red_flags

        # Weighted overall score
        overall = (
            scores["text_similarity"] * WEIGHTS["text"]
            + scores["structure_similarity"] * WEIGHTS["structure"]
            + scores["layout_similarity"] * WEIGHTS["layout"]
        )
        scores["overall_score"] = round(overall, 3)

        return SimilarityScore(
            template_id=template_id,
            template_name=template_name,
            **scores
        )

    except Exception as e:
        # Numeric-only fallback if Groq fails
        conf = confidence_score(query_content, template_content, base_text_similarity)
        duplicated = (
            base_text_similarity >= 0.92
            and base_struct >= 0.85
            and base_layout >= 0.80
        )
        risk, label = forgery_risk_score(base_text_similarity, base_struct, base_layout, duplicated)
        classification = classify_match(base_text_similarity, base_struct, base_layout, duplicated, label)
        overall = (
            base_text_similarity * WEIGHTS["text"]
            + base_struct * WEIGHTS["structure"]
            + base_layout * WEIGHTS["layout"]
        )

        return SimilarityScore(
            template_id=template_id,
            template_name=template_name,
            overall_score=round(overall, 3),
            text_similarity=round(base_text_similarity, 3),
            structure_similarity=round(base_struct, 3),
            layout_similarity=round(base_layout, 3),
            analysis=f"Groq failed, numeric fallback used: {str(e)}",
            is_duplicate=duplicated,
            confidence=conf,
            forgery_risk=risk,
            forgery_label=label,
            fraud_confidence=risk,
            classification=classification,
            field_differences=[],
            red_flags=[],
        )

# ------------------ ROUTES ------------------

@api_router.get("/")
async def home():
    return {"message": "Groq + Embedding Document Template API (Forgery Mode Enabled)"}


@api_router.post("/templates/upload")
async def upload_template(file: UploadFile = File(...)):

    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only PDF/DOCX allowed")

    content_bytes = await file.read()
    file_type = "pdf" if file.filename.lower().endswith(".pdf") else "docx"

    content, structure = (
        extract_text_from_pdf(content_bytes)
        if file_type == "pdf"
        else extract_text_from_docx(content_bytes)
    )

    # Embedding for this template
    emb_vec = encode_embedding(content)
    emb_list = emb_vec.tolist()

    ai_result = await analyze_document_with_ai(content, structure, file_type)
    structure["ai_analysis"] = ai_result
    logging.info(f"[AI SUMMARY] {file.filename}: {ai_result.get('summary')}")


    file_id = str(uuid.uuid4())
    path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    path.write_bytes(content_bytes)

    template = Template(
        id=file_id,
        name=file.filename,
        file_path=str(path),
        file_type=file_type,
        content=content,
        structure_data=structure,
        file_size=len(content_bytes),
        embedding=emb_list,
    )

    doc = template.model_dump()
    doc["upload_date"] = doc["upload_date"].isoformat()
    await db.templates.insert_one(doc)

    return {"status": "uploaded", "template_id": file_id}


@api_router.get("/templates")
async def list_templates():
    return await db.templates.find({}, {"_id": 0}).to_list(100)



@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    template = await db.templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(404, "Not found")

    Path(template["file_path"]).unlink(missing_ok=True)
    await db.templates.delete_one({"id": template_id})
    return {"deleted": template_id}


@api_router.post("/match/single")
async def match_single(file: UploadFile = File(...)):

    content = await file.read()
    file_type = "pdf" if file.filename.lower().endswith(".pdf") else "docx"
    q_text, q_struct = (
        extract_text_from_pdf(content)
        if file_type == "pdf"
        else extract_text_from_docx(content)
    )

    # Query embedding
    q_vec = encode_embedding(q_text)

    templates = await db.templates.find({}, {"_id": 0}).to_list(100)
    results: List[Dict[str, Any]] = []

    for t in templates:
        # Ensure template has embedding; if not, compute & store it
        t_emb_list = t.get("embedding")
        if not t_emb_list:
            t_vec = encode_embedding(t["content"])
            t_emb_list = t_vec.tolist()
            await db.templates.update_one({"id": t["id"]}, {"$set": {"embedding": t_emb_list}})
        else:
            t_vec = np.array(t_emb_list, dtype=float)

        # Semantic + lexical similarity
        sem_sim = cosine_similarity(q_vec, t_vec)
        lex_sim = lexical_similarity(q_text, t["content"])
        base_text_sim = 0.7 * sem_sim + 0.3 * lex_sim

        sim = await calculate_similarity(
            q_text,
            q_struct,
            t["content"],
            t["structure_data"],
            t["name"],
            t["id"],
            base_text_sim,
        )
        results.append(sim.model_dump())

    results.sort(key=lambda x: x["overall_score"], reverse=True)

    await db.match_results.insert_one({
        "query_doc_name": file.filename,
        "matched_templates": results,
        "created_at": datetime.utcnow().isoformat()
    })

    return {"query": file.filename, "matches": results}


@api_router.post("/match/batch")
async def match_batch(files: List[UploadFile] = File(...)):

    if len(files) > 10:
        raise HTTPException(400, "Max 10 files allowed")

    templates = await db.templates.find({}, {"_id": 0}).to_list(100)

    # Ensure embeddings exist for templates
    for t in templates:
        if not t.get("embedding"):
            t_vec = encode_embedding(t["content"])
            t["embedding"] = t_vec.tolist()
            await db.templates.update_one({"id": t["id"]}, {"$set": {"embedding": t["embedding"]}})

    batch_results = []

    for file in files:
        content = await file.read()
        file_type = "pdf" if file.filename.lower().endswith(".pdf") else "docx"
        q_text, q_struct = (
            extract_text_from_pdf(content)
            if file_type == "pdf"
            else extract_text_from_docx(content)
        )

        q_vec = encode_embedding(q_text)
        scores = []

        for t in templates[:5]:
            t_vec = np.array(t["embedding"], dtype=float)
            sem_sim = cosine_similarity(q_vec, t_vec)
            lex_sim = lexical_similarity(q_text, t["content"])
            base_text_sim = 0.7 * sem_sim + 0.3 * lex_sim

            sim = await calculate_similarity(
                q_text,
                q_struct,
                t["content"],
                t["structure_data"],
                t["name"],
                t["id"],
                base_text_sim,
            )
            scores.append(sim.model_dump())

        scores.sort(key=lambda x: x["overall_score"], reverse=True)

        batch_results.append({
            "file": file.filename,
            "best": scores[0] if scores else None,
            "top3": scores[:3],
        })

    return {"results": batch_results}


@api_router.get("/match/history")
async def history():
    docs = await db.match_results.find({}, {"_id": 0}).to_list(50)
    return sorted(docs, key=lambda x: x["created_at"], reverse=True)

# ------------------ REGISTER ------------------

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def close_mongo():
    client.close()

logging.basicConfig(level=logging.INFO)
