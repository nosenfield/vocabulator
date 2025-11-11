# Project Brief: vocabulator

**Version**: 1.0
**Last Updated**: 2025-11-10

## Project Overview

### What We're Building
Vocabulator is an AI-powered personalized vocabulary recommendation engine for middle school students (grades 6-8). The system analyzes student conversation transcripts and writing samples to identify vocabulary gaps and generate personalized word recommendations aligned with Common Core standards.

### Core Problem
Middle school educators struggle with manually identifying vocabulary gaps in students' language use. This process is time-consuming and often fails to provide personalized recommendations that align with each student's current proficiency level. The lack of tailored vocabulary development opportunities may hinder students' language acquisition and overall academic performance.

### Target Users
- **Primary**: Middle school educators (grades 6-8)
- **Secondary**: School administrators and curriculum coordinators

### Success Criteria
- Increase in the rate of novel words properly used by students over time
- Reduction in teacher time spent on manual vocabulary gap analysis
- Positive feedback from educators regarding the usefulness of vocabulary recommendations
- System processes 500+ students efficiently
- Cost-effective operation ($51/month target for 500 students)

---

## MVP Scope

### Must Have
- Upload and process student transcripts and writing samples
- Extract vocabulary from text using AI
- Identify vocabulary gaps vs Common Core standards
- Generate personalized word recommendations (10-15 words per student)
- Store student profiles and recommendations in DynamoDB
- Generate HTML reports for teachers
- Batch processing for full-day transcripts
- Anonymous student IDs (COPPA-compliant)

### Explicitly Out of Scope
- Real-time processing (batch processing only for MVP)
- Student-facing interface (teacher-only for MVP)
- Mobile app (web-based reports only)
- Advanced analytics and dashboards (basic reports only)
- Multi-language support (English only for MVP)
- Integration with LMS systems (manual upload for MVP)

---

## Technical Constraints

### Performance Targets
- API response time: < 200ms (p95) for simple queries
- Batch processing: Process 50 students in < 5 minutes
- DynamoDB queries: < 100ms (p95)
- S3 upload/download: < 2s for typical files (< 1MB)

### Platform Requirements
- AWS (Lambda, DynamoDB, S3, Batch, Fargate)
- Python 3.11+
- OpenAI API (GPT-4o-mini, GPT-4o)
- LocalStack for local development

### Dependencies
- OpenAI API (for vocabulary extraction and analysis)
- AWS services (Lambda, DynamoDB, S3, Batch, Fargate)
- Common Core vocabulary corpus (grades 6-8)

---

## Project Timeline

- **MVP Target**: 6-8 weeks (1 developer, 200-260 hours)
- **Key Milestones**:
  - Phase 0: Project Setup & Foundation - ✅ COMPLETE (2025-11-10)
  - Phase 1: Data Layer & Storage - ✅ COMPLETE (2025-11-10)
  - Phase 2: AI/ML Layer - ✅ COMPLETE (2025-01-01)
  - Phase 3: Processing Layer - In Progress
  - Phase 4: API Layer - Planned
  - Phase 5: Frontend Layer - Planned
  - Phase 6: Infrastructure & Deployment - Planned
  - Phase 7: Testing & Quality Assurance - Planned
  - Phase 8: Documentation & Polish - Planned
  - Phase 9: MVP Launch Preparation - Planned
