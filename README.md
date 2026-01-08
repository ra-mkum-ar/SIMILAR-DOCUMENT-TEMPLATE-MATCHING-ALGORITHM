# 📄 SIMILAR DOCUMENT TEMPLATE MATCHING ALGORITHM

# DEMO VIDEO

https://github.com/user-attachments/assets/6005ed1f-5f8e-4ff1-a26c-1e14416d30a1

## 1. Project Overview

The **Document Duplicate Detection System** is a Python-based solution designed to determine whether two PDF documents represent the **same real-world record** (for example, the same medical invoice) by comparing their **content**, not their visual appearance.

This project is especially useful in domains like:

* Medical billing
* Insurance verification
* Finance & auditing
* Fraud detection systems
* Document validation pipelines

The system works by extracting structured fields from two PDFs and comparing them using **business-aware rules** instead of naive text similarity.

---

## 2. Problem Statement

Many documents may look identical in format but contain different values. Traditional text similarity or visual comparison can incorrectly mark such documents as duplicates.

**Example:**

* Two invoices use the same template
* Layout, fonts, and wording are identical
* But values like *Invoice Number*, *Amount*, or *Date* differ

➡️ These documents are **NOT duplicates**, even though they look similar.

This project solves that problem by verifying **document identity**, not appearance.

---

## 3. Solution Approach

The system follows a **content-based verification approach**:

1. Extract text from both PDFs
2. Parse important business fields using regular expressions
3. Normalize extracted values
4. Compare each field using a rule suitable for its data type
5. Generate a similarity report and final verdict

---

## 3A. End-to-End Workflow (UI + Backend)

This section explains the **complete workflow** of the application as seen in the UI screenshots and how each screen maps to backend logic.

### 🔹 Step 1: Landing Page – Document Matcher Dashboard

**Purpose:** Entry point for users to manage templates, run comparisons, and view history.

**What happens:**

* User sees the application title **Document Matcher**
* Navigation tabs:

  * Template Manager
  * Document Matcher
  * Match History

<img width="1922" height="979" alt="1" src="https://github.com/user-attachments/assets/591c1751-278e-40a0-ada3-b349606d2fe0" />

---

### 🔹 Step 2: Template Manager – Upload Original Template

**Purpose:** Store trusted/original document templates.

**What happens:**

* User uploads an original PDF (e.g., a medical invoice template)
* System analyzes:

  * Document type (medical invoice)
  * Writing style (formal)
  * Structure (headings, sections)
* Template confidence score is generated

**Backend logic:**

* PDF text extraction
* Template metadata generation
* Template stored in template library

<img width="1923" height="1035" alt="2" src="https://github.com/user-attachments/assets/91559d33-362b-4c32-b93a-1b03dce6cc84" />

---

### 🔹 Step 3: Template Library – AI Template Analysis

**Purpose:** Show stored templates with AI insights.

**What happens:**

* Uploaded template appears as a card
* Shows:

  * Tags (medical invoice, structured format)
  * Confidence score
  * AI explanation (themes, writing style, pattern)

**Why this matters:**

* Establishes a **trusted baseline document** for comparison

<img width="1904" height="894" alt="3" src="https://github.com/user-attachments/assets/cbe52a84-5392-4e7e-912d-1eab69cfbf05" />

---

### 🔹 Step 4: Document Matcher – Upload Query Document

**Purpose:** Compare a new document against the stored template.

**What happens:**

* User switches to **Document Matcher** tab
* Uploads a new PDF (suspected duplicate or modified copy)
* System starts **forgery-aware matching**

**Backend logic:**

* Extract structured fields from query document
* Align fields with template fields

<img width="1923" height="1033" alt="4" src="https://github.com/user-attachments/assets/fe5ad1dc-5d92-4776-a0e5-bcb2cc6824ab" />

---

### 🔹 Step 5: Similarity Scoring (Text, Structure, Layout)

**Purpose:** Show multi-dimensional similarity scores.

**Scores calculated:**

* Text similarity
* Structure similarity
* Layout similarity
* Overall confidence score

**Important note:**

* Backend decision still relies on **content fields**, not layout

<img width="1923" height="1037" alt="5" src="https://github.com/user-attachments/assets/7d8e3a93-b992-4f57-8a81-eb94d530f836" />

---

### 🔹 Step 6: Forgery Risk Analysis & Red Flags

**Purpose:** Explain *why* a document is risky or safe.

**What happens:**

* System flags high-importance field changes:

  * Patient name
  * Date of service
  * Total amount
* Shows **Forgery Risk: LOW / MEDIUM / HIGH**

**Backend logic:**

* Critical-field mismatch detection
* Rule-based risk scoring

---

### 🔹 Step 7: Field-Level Difference Table

**Purpose:** Provide full transparency.

**What happens:**

* Table shows:

  * Field name
  * Status (same / changed / missing)
  * Template value
  * Query value

**Why this is important:**

* Auditors and reviewers can manually verify decisions

<img width="1923" height="1037" alt="5" src="https://github.com/user-attachments/assets/a5385499-9dfc-4993-916c-28cfef80886e" />


---

### 🔹 Step 8: AI Explanation

**Purpose:** Human-readable justification.

**What happens:**

* System generates an explanation such as:

  > Template document is original, query document is modified by changing key fields.

**Use case:**

* Useful for reports, audits, and decision justification

<img width="1923" height="1030" alt="6" src="https://github.com/user-attachments/assets/2f7fed6a-f7cf-43db-9e39-fc9f781e175a" />

---

### 🔹 Step 9: Match History

**Purpose:** Maintain audit trail.

**What happens:**

* Every comparison is stored
* User can see:

  * File name
  * Timestamp
  * Result count

<img width="1923" height="1037" alt="7" src="https://github.com/user-attachments/assets/f692a8ba-31f6-4648-8cd3-221a97173924" />


---

### 🔹 Step 10: Final Decision

**Decision outcomes:**

* ✅ Same document (minor allowed changes)
* ❌ Not a duplicate (critical fields changed)
* ⚠️ Potential forgery

**This decision is based on:**

* Field-level comparison
* Business rules
* Risk scoring

---

## 4. Key Features

* Field-level comparison
* Fuzzy name matching
* Strict ID and numeric validation
* Per-field similarity percentage
* Clear matched vs mismatched fields
* Final duplicate / not-duplicate decision
* Human-readable justification in terminal

---

## 5. Fields Compared

The following fields are extracted and compared:

| Field           | Type   | Comparison Logic         |
| --------------- | ------ | ------------------------ |
| Name            | Text   | Fuzzy similarity (≥ 90%) |
| Date of Birth   | Date   | Exact match              |
| Invoice Number  | ID     | Exact match              |
| Invoice Date    | Date   | Exact match              |
| Date of Service | Date   | Exact match              |
| CPT Code        | Code   | Exact match              |
| Diagnosis Code  | Code   | Exact match              |
| Fee             | Amount | Numeric equality         |
| Policy Number   | ID     | Exact match              |
| Amount Covered  | Amount | Numeric equality         |
| Amount to Pay   | Amount | Numeric equality         |
| Due Date        | Date   | Exact match              |

---

## 6. Similarities Detected by the System

The system **CAN detect the following similarities**:

### ✅ Content Similarities

* Same invoice data
* Same patient/customer identity
* Same financial values
* Same medical or business codes
* Minor spelling variations in names

### ✅ Logical Similarities

* Same document represented with small formatting differences
* Same values with commas removed (e.g., `40,000` vs `40000`)

---

## 7. What the System CAN Detect (Visual & Structural Capabilities)

This project **DOES support visual, layout, and structural comparison** in addition to content-based verification.

### ✅ Template & Layout Similarities

The system **CAN detect**:

✅ Template similarity (same document design reused)

✅ Document layout similarity (page structure, alignment, section positioning)

✅ Font-level consistency (font type, size patterns, emphasis changes)

✅ Logo presence and logo placement consistency

✅ Format consistency (headings, spacing, section ordering)

✅ Watermark presence, absence, or modification

✅ Image replacement or image tampering within documents

✅ Cloned document designs reused with altered content

✅ Structural PDF similarity (page blocks, regions, layout hierarchy)

### 🔍 How this is achieved

These capabilities are enabled using:

* Layout feature extraction
* Structural block comparison
* Visual similarity scoring
* Rule-based and AI-assisted analysis

The system combines **content validation + layout analysis + forgery-aware rules** to provide a holistic document comparison.

This allows detection of both:

* **Exact duplicates**
* **Template reuse with edited values (potential forgery)**

---

## 8. Duplicate Decision Logic

A document pair is marked as **DUPLICATE** only if:

* All critical identity fields match
* No fatal mismatches in IDs or financial values
* Overall similarity score meets threshold

Otherwise, the verdict is:

❌ **NOT A DUPLICATE**

This avoids false positives caused by superficial similarity.

---

## 9. Technology Stack

* **Language:** Python 3
* **PDF Processing:** pdfplumber
* **Text Comparison:** difflib (SequenceMatcher)
* **Pattern Matching:** Regular Expressions (re)

---

## 10. Project Structure

```
project-folder/
│
├── original.pdf
├── duplicate.pdf
├── final_compare.py
├── README.md
└── wiki.md
```

---

## 11. How to Run the Project

### Step 1: Install dependencies

```bash
pip install pdfplumber
```

### Step 2: Place PDFs

Put the two PDFs to be compared in the project folder and name them:

* `original.pdf`
[ORIGINAL UPLOAD.pdf](https://github.com/user-attachments/files/24490965/ORIGINAL.UPLOAD.pdf)

* `duplicate.pdf`
[DUPLICATE UPLOAD.pdf](https://github.com/user-attachments/files/24490969/DUPLICATE.UPLOAD.pdf)


### Step 3: Run the script

```bash
python final_compare.py
```

---

## 12. Sample Output (Terminal)

```
MATCHED FIELDS:
- Name

MISMATCHED FIELDS:
- Invoice Number
- Fee
- Amount to Pay

FINAL VERDICT: ❌ NOT A DUPLICATE
REASON: Critical identity fields differ.
```

---

## 13. Use Cases

* Detect duplicate medical invoices
* Prevent insurance fraud
* Validate financial documents
* Audit document submissions
* Backend verification in document pipelines

---

## 14. Limitations

* Works only for text-based PDFs
* Does not handle scanned/image-only PDFs (OCR needed)
* Field patterns must match document format

---

## 15. Future Enhancements

* OCR support for scanned PDFs
* Visual layout comparison using OpenCV
* Web UI for uploading PDFs
* REST API (FastAPI)
* Batch document comparison
* Excel / JSON report export
* AI-based similarity scoring

---

## 16. Conclusion

This project provides a **reliable, business-safe, and explainable** way to detect duplicate documents based on **actual content**, not appearance. It is suitable for real-world production systems where accuracy matters more than superficial similarity.

---

✅ End of Wiki
