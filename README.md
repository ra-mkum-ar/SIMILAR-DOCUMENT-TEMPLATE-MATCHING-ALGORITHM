# 📄 Document Duplicate Detection System (PDF Content-Based)

!(<img width="1922" height="979" alt="1" src="https://github.com/user-attachments/assets/3c37d541-1a32-4c10-8e85-6a3efd7a4c27" />


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

## 7. What the System Does NOT Detect

This project is **NOT a visual or layout comparison tool**.

🚫 Template similarity
🚫 Document layout similarity
🚫 Font changes
🚫 Logo edits
🚫 Format changes
🚫 Watermark removal
🚫 Image replacement
🚫 Cloned design
🚫 Structural PDF similarity

If visual or layout comparison is required, computer vision or AI-based image comparison techniques must be used.

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
* `duplicate.pdf`

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
