"""Synthetic golden dataset and log-file loader for Alakazam filename evaluations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


GOLDEN_DATASET: List[Dict] = [
    {
        "id": "auto_insurance_claim_notice",
        "original_filename": "2026-06-21_STATE REQUIRED NOTICE.pdf",
        "expected_sources": ["AAIC", "Allied Auto Insurance Group"],
        "bad_legacy_filename": "2026-04-21 AAIC Auto Insurance Claim Correspondence For Jane Doe.pdf",
        "analysis": {
            "document_date": "2026-04-21",
            "document_type": "insurance_claim",
            "description": "AAIC auto insurance claim correspondence for Jane Doe regarding claim 000123456-001 (policyholder Robert Roe, date of loss April 20, 2026), including a State Required Notice and Settlement Check Notice.",
            "metadata": {
                "provider_name": "Allied Auto Insurance Corporation (AAIC)",
                "recipient_name": "Jane Doe",
                "claim_number": "000123456-001",
            },
        },
    },
    {
        "id": "inactive_ira_notice",
        "original_filename": "2026-01-05_100 Main St Suite 7 Horizon 800.555.0199.pdf",
        "expected_sources": ["Horizon Trust"],
        "bad_legacy_filename": "2026-01-05 Notice From Horizon Trust To Jane Doe Regarding An Inactive IRA.pdf",
        "analysis": {
            "document_date": "2026-01-05",
            "document_type": "letter",
            "description": "Notice from Horizon Trust to Jane Doe regarding an inactive IRA account with an estimated value of $2,500.00 requiring address confirmation.",
            "metadata": {
                "provider_name": "Horizon Trust",
                "recipient_name": "Jane Doe",
                "account_type": "IRA Account",
            },
        },
    },
    {
        "id": "university_undergrad_transcript",
        "original_filename": "2026-06-09_scan.pdf",
        "expected_sources": ["UO Springfield", "University of Oregon Springfield", "Springfield"],
        "bad_legacy_filename": "2016-08-23 Official Academic Transcript From The University Of Oregon,.pdf",
        "analysis": {
            "document_date": "2016-08-23",
            "document_type": "academic_transcript",
            "description": "Official academic transcript from the University of Oregon, Springfield for Jane Marie Doe, conferring a Bachelor of Arts in Political Science on August 13, 2010.",
            "metadata": {
                "provider_name": "University of Oregon, Springfield",
                "student_name": "Jane Marie Doe",
            },
        },
    },
    {
        "id": "graduate_academic_transcript",
        "original_filename": "2015-01-21_PACIFIC STATE UNIVERSITY.pdf",
        "expected_sources": ["PSU", "Pacific State University"],
        "bad_legacy_filename": "2016-05-27 Official Graduate Academic Transcript From PSU For Jane.pdf",
        "analysis": {
            "document_date": "2016-05-27",
            "document_type": "academic_transcript",
            "description": "Official graduate academic transcript from PSU for Jane Marie Doe in the Master of Education program, showing coursework completed through Spring Quarter 2016 with a 4.000 GPA and advancement to candidacy.",
            "metadata": {
                "provider_name": "Pacific State University",
                "institution_abbreviation": "PSU",
                "student_name": "Jane Marie Doe",
            },
        },
    },
    {
        "id": "elementary_pta_reimbursement",
        "original_filename": "2026-05-31_OAK CREEK ELEMENTARY PTA PAYMENT AUTHORIZATION.pdf",
        "expected_sources": ["Oak Creek Elementary PTA", "Oak Creek PTA"],
        "bad_legacy_filename": "2026-05-31 Payment Authorization And Reimbursement Request Form Submitted.pdf",
        "analysis": {
            "document_date": "2026-05-31",
            "document_type": "reimbursement_request",
            "description": "Payment authorization and reimbursement request form submitted to Oak Creek Elementary PTA by Jane Doe for Spring Festival pastries expenditure.",
            "metadata": {
                "organization": "Oak Creek Elementary PTA",
                "payee_name": "Jane Doe",
                "expenditure_purpose": "Spring Festival",
            },
        },
    },
    {
        "id": "bakery_purchase_order",
        "original_filename": "Spring Festival Bakery Receipt.pdf",
        "expected_sources": ["Sunrise Bakery", "Oak Creek"],
        "bad_legacy_filename": "2026-05-29 Purchase Order 100200 For Assorted Pastries (12 Lb) Totaling.pdf",
        "analysis": {
            "document_date": "2026-05-29",
            "document_type": "purchase_order",
            "description": "Purchase order 100200 from Sunrise Bakery for assorted pastries totaling $120.00 for Jane Doe",
            "metadata": {
                "vendor": "Sunrise Bakery",
                "purchase_order_number": "100200",
                "recipient_name": "Jane Doe",
            },
        },
    },
    {
        "id": "dental_benefits_claim",
        "original_filename": "2026-04-01_CLAIM_STATEMENT_001.pdf",
        "expected_sources": ["Premier Dental", "Premier Dental of California"],
        "bad_legacy_filename": "2026-03-12 Premier Dental Of California Benefits Claim Statement For Jane M.pdf",
        "analysis": {
            "document_date": "2026-03-12",
            "document_type": "insurance_claim",
            "description": "Premier Dental of California benefits claim statement for Jane M Doe covering adult orthodontic treatment on February 11, 2026.",
            "metadata": {
                "provider_name": "Premier Dental of California",
                "patient_name": "Jane M Doe",
            },
        },
    },
    {
        "id": "pest_control_invoice",
        "original_filename": "2025-08-07_Invoice.pdf",
        "expected_sources": ["Apex Pest Control"],
        "bad_legacy_filename": "2025-08-07 Invoice #90100 From Apex Pest Control For Ant Pest Control.pdf",
        "analysis": {
            "document_date": "2025-08-07",
            "document_type": "invoice",
            "description": "Invoice #90100 from Apex Pest Control for ant pest control treatment billed to Jane Doe",
            "metadata": {
                "provider_name": "Apex Pest Control",
                "customer_name": "Jane Doe",
                "invoice_number": "90100",
            },
        },
    },
    {
        "id": "garage_doors_invoice",
        "original_filename": "2026-03-06_New Garage Door Estimate.pdf",
        "expected_sources": ["Summit Garage Doors"],
        "bad_legacy_filename": "2025-08-25 Invoice #40500 From Summit Garage Doors, Inc. For Garage Door.pdf",
        "analysis": {
            "document_date": "2025-08-25",
            "document_type": "invoice",
            "description": "Invoice #40500 from Summit Garage Doors, Inc. for garage door sensor replacement, re-wiring, and labor for John Smith at 123 Maple St, totaling $350.00 paid via check.",
            "metadata": {
                "provider_name": "Summit Garage Doors, Inc.",
                "customer_name": "John Smith",
                "invoice_number": "40500",
            },
        },
    },
    {
        "id": "optometry_eyewear_rx",
        "original_filename": "2026-01-26_Date.pdf",
        "expected_sources": ["ClearView Optometry", "ClearView"],
        "bad_legacy_filename": "2026-01-26 Eyewear Prescription (final Spectacle Rx) For John Smith From.pdf",
        "analysis": {
            "document_date": "2026-01-26",
            "document_type": "medical_prescription",
            "description": "Eyewear prescription (Final Spectacle Rx) for John Smith from ClearView Optometry",
            "metadata": {
                "provider_name": "ClearView Optometry",
                "patient_name": "John Smith",
            },
        },
    },
    {
        "id": "university_1098t",
        "original_filename": "2026-03-02_Payments received for qualified tuition.pdf",
        "expected_sources": ["Metro State University", "Metro State", "MSU"],
        "bad_legacy_filename": "2025-01-01 IRS Form 1098-T (tuition Statement) From Metro State.pdf",
        "analysis": {
            "document_date": "2025-01-01",
            "document_type": "tax_document",
            "description": "IRS Form 1098-T (Tuition Statement) from Metro State University for student Jane Marie Doe, Copy B.",
            "metadata": {
                "provider_name": "Metro State University - Bursar's Office",
                "student_name": "JANE MARIE DOE",
            },
        },
    },
    {
        "id": "state_tax_1099g",
        "original_filename": "2026-03-02_STATE TAX BOARD RECIPIENTS TIN.pdf",
        "expected_sources": ["Franchise Tax Board", "Oregon Franchise Tax Board", "State of Oregon Franchise Tax Board"],
        "bad_legacy_filename": "2024-01-01 Oregon Franchise Tax Board Form 1099-G Reporting State.pdf",
        "analysis": {
            "document_date": "2024-01-01",
            "document_type": "tax_document",
            "description": "Oregon Franchise Tax Board Form 1099-G reporting state income tax refund for tax year 2024.",
            "metadata": {
                "provider_name": "State of Oregon Franchise Tax Board",
                "form_type": "1099-G",
            },
        },
    },
]


def load_eval_cases_from_log(log_path: Path, limit: int = 20) -> List[Dict]:
    """Load recent rename records from a .alakazam.log file as evaluation test cases."""
    data = json.loads(log_path.read_text(encoding="utf-8"))
    renames = data.get("renames", [])
    if limit > 0:
        renames = renames[-limit:]

    cases: List[Dict] = []
    for idx, entry in enumerate(renames):
        old_name = entry.get("old_name", f"doc_{idx}.pdf")
        new_name = entry.get("new_name")
        analysis = {
            "document_date": entry.get("document_date", "2024-01-01"),
            "document_type": entry.get("document_type", "unknown"),
            "document_source": entry.get("document_source"),
            "description": entry.get("description", ""),
            "metadata": entry.get("metadata") or {},
        }
        cases.append(
            {
                "id": f"log_{idx + 1}_{Path(old_name).stem[:24]}",
                "original_filename": old_name,
                "recorded_filename": new_name,
                "expected_sources": [],
                "analysis": analysis,
            }
        )
    return cases
