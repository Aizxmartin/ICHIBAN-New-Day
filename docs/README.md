# ICHIBAN New Day Documentation

## Purpose

This directory contains documentation for:

- Architecture
- Module Design
- Adjustment Philosophy
- Market Analysis Logic
- Future Enhancements

## Architecture Overview

ICHIBAN uses a 3-layer architecture:

1. User Input Layer
2. Private Logic Layer
3. Output Layer

Private logic remains separate from public UI.

## Modules

### Module 1 — Intake
Upload files and validate required inputs.

### Module 2 — Subject Property Extraction Engine
Parse uploaded subject property PDFs, normalize core property facts, and log missing-data issues.

Current Module 2 goals:
- Flexible PDF parsing across REcolorado, CoreLogic, and county-style reports
- Canonical subject property JSON output
- Missing-data issue tracking instead of visible confidence scoring
- Clean handoff to later modules and report language

### Module 3 — Readiness / Decision Engine
Evaluate whether extracted subject data and market inputs are strong enough for a full report, a limited-scope valuation, or an insufficient-data stop.

### Module 4 — Comp Filtering
Apply objective comp filters and comp selection rules.

### Module 5 — Adjustment Engine
Run concrete property adjustments using the approved schema.

### Module 6+ — Report and GPT Interpretation Layers
Build the final report, including Data Verification Notes and GPT Market Interpretation.

## Current Report Philosophy

- Objective adjustments first
- GPT interpretation after concrete math
- No visible confidence scoring
- Missing data explained in plain language

## Future Enhancements

- Subdivision / amenity enrichment
- Deeper remarks mining after structured adjustments
- API-based AVM retrieval
- Automated 1004MC parsing
