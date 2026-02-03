#!/usr/bin/env python3
"""Create test PDF files for Alakazam testing."""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path

def create_invoice_pdf():
    """Create a test invoice PDF."""
    pdf = canvas.Canvas("test_invoice.pdf", pagesize=letter)
    width, height = letter

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "INVOICE")

    # Company info
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, "Acme Corporation")
    pdf.drawString(50, height - 95, "123 Main Street")
    pdf.drawString(50, height - 110, "Anytown, CA 12345")

    # Invoice details
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 140, "Date: January 15, 2024")
    pdf.drawString(50, height - 155, "Invoice #: INV-2024-001")

    # Bill to
    pdf.drawString(50, height - 185, "Bill To:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 200, "John Doe")
    pdf.drawString(50, height - 215, "456 Oak Avenue")
    pdf.drawString(50, height - 230, "Springfield, IL 67890")

    # Line items
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 270, "Description")
    pdf.drawString(400, height - 270, "Amount")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 290, "Web Development Services")
    pdf.drawString(400, height - 290, "$2,500.00")
    pdf.drawString(50, height - 305, "Consulting Hours (10 hrs)")
    pdf.drawString(400, height - 305, "$1,500.00")
    pdf.drawString(50, height - 320, "Server Setup")
    pdf.drawString(400, height - 320, "$  500.00")

    # Total
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 350, "Total Due:")
    pdf.drawString(400, height - 350, "$4,882.50")

    pdf.drawString(50, height - 380, "Payment Terms: Net 30")
    pdf.drawString(50, height - 395, "Due Date: February 15, 2024")

    pdf.save()
    print("✓ Created test_invoice.pdf")

def create_medical_pdf():
    """Create a test medical statement PDF."""
    pdf = canvas.Canvas("medical_record.pdf", pagesize=letter)
    width, height = letter

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "MEDICAL STATEMENT")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, "Kaiser Permanente Medical Center")

    # Patient info
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 110, "Patient: Jane Smith")
    pdf.drawString(50, height - 125, "Date of Service: January 20, 2024")
    pdf.drawString(50, height - 140, "Member ID: KP123456789")

    # Services
    pdf.drawString(50, height - 170, "STATEMENT OF SERVICES")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 195, "Office Visit - General")
    pdf.drawString(400, height - 195, "$150.00")
    pdf.drawString(50, height - 210, "Lab Work - Blood Panel")
    pdf.drawString(400, height - 210, "$200.00")
    pdf.drawString(50, height - 225, "Prescription - Medication")
    pdf.drawString(400, height - 225, "$ 45.00")

    # Total
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 255, "Total Charges:")
    pdf.drawString(400, height - 255, "$395.00")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 270, "Insurance Payment:")
    pdf.drawString(400, height - 270, "$315.00")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 290, "Patient Responsibility:")
    pdf.drawString(400, height - 290, "$ 80.00")

    pdf.save()
    print("✓ Created medical_record.pdf")

def create_tax_pdf():
    """Create a test property tax PDF."""
    pdf = canvas.Canvas("property_tax_statement.pdf", pagesize=letter)
    width, height = letter

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "PROPERTY TAX STATEMENT")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, "County of Santa Clara")
    pdf.drawString(50, height - 95, "Tax Collector's Office")

    # Property info
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 125, "Property Address: 789 Elm Street, San Jose, CA 95123")
    pdf.drawString(50, height - 140, "Parcel Number: 123-45-678")
    pdf.drawString(50, height - 155, "Tax Year: 2024")

    # Assessment
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 185, "Assessment Details:")
    pdf.drawString(70, height - 200, "Land Value:")
    pdf.drawString(300, height - 200, "$500,000")
    pdf.drawString(70, height - 215, "Improvement Value:")
    pdf.drawString(300, height - 215, "$800,000")
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(70, height - 230, "Total Assessed Value:")
    pdf.drawString(300, height - 230, "$1,300,000")

    # Tax calculation
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 260, "Tax Calculation:")
    pdf.drawString(70, height - 275, "Base Tax Rate:")
    pdf.drawString(300, height - 275, "1.00%")
    pdf.drawString(70, height - 290, "Special Assessments:")
    pdf.drawString(300, height - 290, "0.15%")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 320, "Annual Tax Amount: $14,950.00")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 350, "Due Dates:")
    pdf.drawString(70, height - 365, "First Installment:  December 10, 2024")
    pdf.drawString(70, height - 380, "Second Installment: April 10, 2025")

    pdf.save()
    print("✓ Created property_tax_statement.pdf")

def create_random_scan():
    """Create a random scan PDF."""
    pdf = canvas.Canvas("IMG_2341_scan.pdf", pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "JURY SUMMONS")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, "Superior Court of California")
    pdf.drawString(50, height - 95, "County of San Diego")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 125, "Andrew Hao")
    pdf.drawString(50, height - 140, "123 Your Street")
    pdf.drawString(50, height - 155, "San Diego, CA 92101")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 185, "You are hereby summoned to appear for jury duty on:")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 210, "Date: December 5, 2022")
    pdf.drawString(50, height - 225, "Time: 8:00 AM")
    pdf.drawString(50, height - 240, "Location: 220 West Broadway, San Diego, CA 92101")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 270, "Please complete the enclosed juror questionnaire and bring it with you.")
    pdf.drawString(50, height - 290, "Failure to appear may result in penalties.")

    pdf.save()
    print("✓ Created IMG_2341_scan.pdf")

if __name__ == "__main__":
    print("Creating test PDF files...")
    print()
    create_invoice_pdf()
    create_medical_pdf()
    create_tax_pdf()
    create_random_scan()
    print()
    print("✓ All test PDFs created successfully!")
