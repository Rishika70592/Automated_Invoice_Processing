Automated Invoice Processing

An intelligent, AI-powered invoice processing and management system designed to automate invoice collection, document extraction, data validation, duplicate detection, and financial record management.

1. Project Overview

The Automated Invoice Processing and Management System is a web-based application designed to automate invoice collection, data extraction, validation, and document management.

Businesses receive invoices through emails, cloud storage, and other digital channels. Employees often spend significant time downloading documents, entering invoice details into spreadsheets, checking calculations, and organizing financial records.

These activities become increasingly difficult when businesses receive thousands of invoices every month or need to import existing archives containing hundreds of thousands of documents.

The proposed system automates these repetitive tasks using OCR, AI-based document extraction, automated ingestion, and business-rule validation.

It provides a centralized dashboard where employees can monitor documents, review extracted information, correct errors, and export structured invoice records.

Primary Goal: Eliminate repetitive document-handling tasks while providing visibility into invoice processing and maintaining human oversight for exceptions.

2. Problem Statement

Traditional invoice processing creates several operational challenges:

Manual Uploads: Employees must download and upload invoice documents individually.
Repetitive Data Entry: Invoice numbers, supplier information, line items, taxes, and totals must be entered manually.
Human Errors: Incorrect amounts, missing fields, and calculation mistakes can affect financial records.
Different Document Formats: Suppliers provide invoices as digital PDFs, scanned documents, and images with different layouts.
Duplicate Documents: The same invoice may arrive through multiple channels or be imported more than once.
Large Document Volumes: Processing thousands of invoices manually becomes inefficient and difficult to manage.
Limited Visibility: Employees may not know which documents were processed successfully, failed, or require review.

This project addresses these challenges by automatically collecting documents, extracting and validating invoice information, tracking processing activities, and presenting results through a centralized dashboard.

3. Project Objectives

The main objectives of the system are:

Extract invoice information and line items from PDFs and scanned images.
Validate extracted values using business rules.
Store structured invoice records in PostgreSQL.
Provide a dashboard for viewing, searching, and correcting invoices.
Export invoice data in JSON and CSV formats.
Automatically collect invoice attachments from configured email accounts.
Detect newly uploaded invoices in cloud storage.
Import existing document archives in batches with resumable progress.
Detect duplicate files and flag potential duplicate invoices.
Maintain a centralized ingestion registry for tracking document sources and processing status.
Record processing failures and retry eligible operations.
Minimize manual work while maintaining appropriate human oversight.

4. Technology Stack
Technology	Purpose
Python	Core application development
FastAPI	Backend API architecture
SQLAlchemy	ORM and database operations
Pydantic	Data validation and schema enforcement
PyMuPDF	PDF text extraction
Tesseract OCR	Scanned document text extraction
Ollama	Local LLM execution
Llama 3.2 3B	AI-based invoice information extraction
SQLite / PostgreSQL	Relational database storage
SHA-256	Document integrity verification

5. How the System Works

The system follows an automated invoice-processing pipeline.

Document Ingestion: Collects invoice documents through manual uploads, configured email accounts, cloud storage, or bulk archive imports.

File Validation: Checks file extension, MIME type, file size, and file signature.

Document Storage: Generates a UUID, calculates the SHA-256 hash, and stores the original document.

Text Extraction: Uses PyMuPDF for digital PDFs and Tesseract OCR for scanned pages and images.

AI-Based Extraction: Sends extracted text to Ollama using the Llama 3.2 3B model to generate structured invoice information.

Data Normalization: Normalizes extracted values and validates the generated JSON using Pydantic.

Business Validation: Checks mandatory fields, dates, currency, monetary calculations, and line items.

Duplicate Detection: Identifies duplicate files and potential duplicate invoices.

Database Persistence: Stores supplier information, invoices, line items, and validation results using SQLAlchemy.

Processing Tracking: Updates processing job status and records audit events.

Dashboard and Export: Provides invoice monitoring, manual review, correction, and JSON/CSV export capabilities.

6. System Architecture

The application follows a modular, service-oriented architecture with separation between the API, service, database, storage, and external processing components.

Service Layer
Service	Responsibility
Document Service	Document registration, uploading, retrieval, and metadata management
File Validation Service	File type, size, MIME, and signature validation
Storage Service	Physical document storage and deletion
PDF Extraction Service	Extracts embedded PDF text
OCR Service	Extracts text from scanned documents and images
Unified Extraction Service	Coordinates PDF extraction and OCR
Invoice Extraction Service	Extracts structured invoice data using Ollama and Llama 3.2
Invoice Validation Service	Validates invoice information using business rules
Duplicate Detection Service	Identifies potential duplicate invoices
Invoice Persistence Service	Saves invoices, suppliers, and line items
Processing Workflow Service	Coordinates the complete invoice-processing pipeline
Processing Job Service	Manages processing job status and lifecycle
Audit Logging	Records important application activities
High-Level Architecture
text
                 Client / Frontend
                        |
                        v
                 API / Controller
                        |
                        v
                   Service Layer
                        |
       +----------------+----------------+
       |                |                |
       v                v                v
 Document          Extraction       Validation
 Services          Services         Services
       |                |                |
       +----------------+----------------+
                        |
                        v
               Processing Workflow
                        |
            +-----------+-----------+
            |           |           |
            v           v           v
         Duplicate  Persistence   Job & Audit
         Detection    Service      Services
            |           |
            +-----------+
                        |
                        v
                 Database Layer
                        |
                        v
               SQLite / PostgreSQL

External Processing:
PyMuPDF | Tesseract OCR | Ollama | Llama 3.2

Document Storage:
Local File Storage / Future Cloud Storage

7. Document Ingestion

The ingestion layer is responsible for collecting invoice documents from different sources.

Supported Ingestion Sources
Manual document uploads.
Email invoice attachments from configured accounts.
Newly uploaded documents in configured cloud storage.
Bulk import of existing document archives.
Ingestion Management

The system maintains a centralized ingestion registry to track:

Document source.
Original filename.
Document identifier.
File hash.
Ingestion timestamp.
Processing status.
Failure information.
Retry eligibility.

Bulk archive imports are designed to support batch processing and resumable progress, making large document migrations easier to manage.

8. Invoice Information Extraction

The Invoice Extraction Service uses Ollama with the Llama 3.2 3B model to convert extracted document text into structured invoice information.

Extracted Information
Invoice number.
Supplier name and tax ID.
Invoice date and due date.
Currency.
Subtotal.
Tax amount and tax rate.
Discount.
Total amount.
Individual invoice line items.
Extraction Pipeline
text
Extracted Invoice Text
          |
          v
      Prompt Builder
          |
          v
       Ollama API
          |
          v
      Llama 3.2 3B
          |
          v
      JSON Parsing
          |
          v
   Data Normalization
          |
          v
   Pydantic Validation
          |
          v
 Structured Invoice Data


The extraction service also identifies missing fields, records uncertainties, and captures model performance metrics.

9. Business Validation

The Invoice Validation Service independently verifies AI-extracted information using deterministic business rules.

Validation Rules
Mandatory field validation.
Currency format validation.
Monetary value validation.
Financial consistency checks.
Invoice date and due date validation.
Line-item quantity and price validation.
Missing-field detection.
Extraction uncertainty checks.
Financial Consistency

The system verifies:

Expected Total = Subtotal + Tax - Discount

A tolerance of 0.02 is currently used to account for minor rounding differences.

Validation Status
completed – No validation errors or warnings.
needs_review – Errors or warnings require attention.

The system does not automatically modify incorrect financial values.

10. Duplicate Invoice Detection

The Duplicate Detection Service identifies invoices that may already exist in the database.

Matching Strategies

Strong Duplicate Match

Same supplier.
Same normalized invoice number.

Potential Duplicate Match

Same supplier.
Same invoice date.
Same total amount.
Same currency.

Document-level SHA-256 hashing also supports identification of identical file contents.

Potential duplicates are flagged for manual review instead of being automatically rejected.

11. Database Architecture

The application uses SQLAlchemy ORM with a relational database design compatible with SQLite and PostgreSQL.

Main Database Entities
Entity	Description
Document	Stores uploaded document metadata
Supplier	Stores supplier information
Invoice	Stores extracted invoice information
InvoiceLineItem	Stores individual invoice items
ValidationResult	Stores validation errors, warnings, and status
ProcessingJob	Tracks processing operations
AuditLog	Maintains historical application activities
IngestionRegistry	Tracks document sources and ingestion status

Invoice line items are stored separately with a one-to-many relationship to invoices.

12. Dashboard and Invoice Management

The centralized dashboard provides visibility into invoice-processing activities.

Planned Dashboard Capabilities
View uploaded and ingested documents.
Monitor processing status.
Search and filter invoice records.
View extracted invoice information.
Review missing or uncertain fields.
Correct extracted invoice information.
Identify potential duplicate invoices.
View processing failures.
Track document ingestion progress.
Export structured invoice records.
13. Data Export

The system supports exporting structured invoice information for reporting and integration purposes.

Supported export formats:

JSON
CSV

Exported records can include invoice information, supplier details, financial values, and line items.

14. Processing Job Management

The Processing Job Service manages the lifecycle of invoice-processing operations.

Supported Job Statuses
pending
processing
completed
failed

The service records job creation, completion timestamps, failure information, and associated document status.

Eligible failed operations can be retried according to the configured retry strategy.

15. Audit Logging

The Audit Logging mechanism maintains a historical record of important system operations.

Recorded Events
document_uploaded
document_text_extracted
document_extraction_failed
invoice_extracted
processing_started
processing_completed
processing_failed

Audit records support traceability, debugging, and operational monitoring.

16. Error Handling and Reliability

The system implements error handling at individual service and workflow levels.

Invalid uploads are rejected during file validation.
Partial files are removed when storage operations fail.
Database failures trigger transaction rollback.
PDF and OCR extraction failures are reported.
Invalid LLM responses and JSON structures are rejected.
Business validation issues are recorded for review.
Processing failures update job status and generate audit events.
Eligible operations can be retried.
Batch imports maintain progress for resumable execution.

The workflow service coordinates database transaction handling across the processing pipeline.

17. Performance Optimization

The application includes several resource-conscious design decisions.

Avoids unnecessary OCR by extracting embedded PDF text first.
Uses page-level OCR for scanned PDF pages.
Uses the lightweight Llama 3.2 3B model.
Uses local Ollama inference instead of depending on an external LLM API.
Uses Decimal for financial calculations.
Supports batch-based document ingestion.
Tracks processing performance and model execution metrics.
Default LLM Configuration
Parameter	Value
Model	llama3.2:3b
Temperature	0
Context Window	4096
Maximum Generated Tokens	2048
Batch Size	64
CPU Threads	4
Keep Alive	10m

These are configurable starting values and can be adjusted according to available hardware and processing requirements.

18. Architectural Benefits
Automation: Reduces repetitive invoice collection and data-entry tasks.
Modular Architecture: Separates application functionality into independent services.
Separation of Concerns: Separates ingestion, document processing, AI extraction, validation, and persistence.
Maintainability: Individual services can be modified and tested independently.
Scalability: Provides a foundation for handling large document archives and high-volume invoice ingestion.
Extensibility: Supports future integration of different OCR engines, LLMs, storage backends, and databases.
Traceability: Maintains processing history and audit records.
Human-in-the-Loop: Flags uncertain, incomplete, inconsistent, and potentially duplicate invoices for manual review.
19. Complete Processing Pipeline
text
          Invoice Sources
                 |
       +---------+---------+
       |         |         |
       v         v         v
     Manual    Email     Cloud
     Upload    Ingestion Storage
       |         |         |
       +---------+---------+
                 |
                 v
          Document Ingestion
                 |
                 v
           File Validation
                 |
                 v
           Document Storage
                 |
                 v
           Text Extraction
                 |
          +------+------+
          |             |
       PyMuPDF       Tesseract
          |             |
          +------+------+
                 |
                 v
        Extracted Invoice Text
                 |
                 v
          Ollama / Llama 3.2
                 |
                 v
           Structured JSON
                 |
                 v
         Pydantic Validation
                 |
                 v
          Business Validation
                 |
                 v
          Duplicate Detection
                 |
                 v
         Database Persistence
                 |
                 v
         Processing Job Update
                 |
                 v
            Audit Logging
                 |
                 v
         Dashboard / Review
                 |
                 v
           JSON / CSV Export

20. Project Objective

The primary objective is to develop an intelligent, reliable, and scalable invoice-processing solution that automates invoice collection, document extraction, information recognition, business validation, duplicate detection, and financial record management.

By combining OCR, local LLM inference, automated ingestion, and structured database management, the system provides a centralized platform for processing large volumes of invoices while maintaining data accuracy, traceability, and human oversight.


                  ┌──────────────────────────┐
                  │          USER            │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │     REACT FRONTEND       │
                  │                          │
                  │  • Invoice Dashboard     │
                  │  • Document Upload       │
                  │  • Invoice Details       │
                  │  • Review & Correction  │
                  │  • Search & Export       │
                  └────────────┬─────────────┘
                               │
                         REST API (HTTP)
                               │
                               ▼
                  ┌──────────────────────────┐
                  │      FASTAPI BACKEND     │
                  │                          │
                  │  • Document Management   │
                  │  • Invoice Management    │
                  │  • Processing Jobs       │
                  │  • Supplier Management   │
                  │  • Duplicate Detection   │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │   DOCUMENT PROCESSING    │
                  │                          │
                  │  • PDF Text Extraction   │
                  │  • OCR Processing        │
                  │  • Text Normalization    │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │   AI INVOICE EXTRACTION  │
                  │                          │
                  │  • Invoice Information   │
                  │  • Supplier Details      │
                  │  • Financial Information │
                  │  • Invoice Line Items    │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │   VALIDATION & MATCHING  │
                  │                          │
                  │  • Pydantic Validation   │
                  │  • Financial Validation  │
                  │  • Supplier Matching     │
                  │  • Duplicate Detection   │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │   INVOICE PERSISTENCE    │
                  │                          │
                  │  • Invoice Records       │
                  │  • Line Items            │
                  │  • Validation Results   │
                  │  • Processing Status    │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │       POSTGRESQL         │
                  │                          │
                  │  • Documents             │
                  │  • Invoices              │
                  │  • Suppliers             │
                  │  • Processing Jobs       │
                  │  • Audit Logs            │
                  └──────────────────────────┘


       ┌──────────────────────┐
       │   LOCAL FILE STORAGE │
       │                      │
       │  Original PDF Files  │
       │  Invoice Images      │
       └──────────────────────┘
                    ▲
                    │
             Document Upload


       ┌──────────────────────┐
       │   EMAIL INGESTION    │
       │                      │
       │  Gmail API           │
       │  Microsoft Graph     │
       └──────────┬───────────┘
                  │
                  ▼
          Document Management

       ┌──────────────────────┐
       │    BULK IMPORT       │
       └──────────┬───────────┘
                  │
                  ▼
          Document Management



## System Architecture

The application follows a modular monolithic architecture consisting of
a React frontend, FastAPI backend, invoice processing pipeline, and
PostgreSQL database.

The frontend communicates with the backend through REST APIs.
Uploaded invoice documents are stored in the local file system and
processed using PDF text extraction, OCR, and AI-based information
extraction.

The extracted invoice data is validated using Pydantic and custom
business validation logic. Supplier matching and duplicate detection
are performed before invoice information is persisted in PostgreSQL.

The backend also supports email-based invoice ingestion, bulk document
imports, processing job tracking, and error handling.
