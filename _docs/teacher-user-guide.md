# Teacher User Guide: Vocabulator

**Version:** 1.0.0 (MVP)  
**Last Updated:** 2025-11-12

---

## Table of Contents

1. [Welcome](#welcome)
2. [Getting Started](#getting-started)
3. [Understanding Student IDs](#understanding-student-ids)
4. [Uploading Student Work](#uploading-student-work)
5. [Understanding Vocabulary Reports](#understanding-vocabulary-reports)
6. [Privacy and COPPA Compliance](#privacy-and-coppa-compliance)
7. [Frequently Asked Questions](#frequently-asked-questions)
8. [Troubleshooting](#troubleshooting)
9. [Support](#support)

---

## Welcome

Welcome to Vocabulator! This guide will help you use the system to analyze student language and get personalized vocabulary recommendations.

**What Vocabulator Does:**
- Analyzes student transcripts and writing samples
- Identifies vocabulary words students are using
- Finds vocabulary gaps (words students should learn)
- Recommends 10-15 personalized words per student
- Tracks vocabulary growth over time

**Who This Guide Is For:**
- Middle school teachers (grades 6-8)
- Educators working with vocabulary development
- Administrators managing student vocabulary programs

---

## Getting Started

### Step 1: Access the System

Vocabulator is accessed via API endpoints. Your school's IT administrator will provide:
- API endpoint URL (e.g., `https://api.vocabulator.example.com`)
- Authentication credentials (if required)

**Note:** In MVP, authentication is not yet implemented. Future versions will require API keys or login credentials.

### Step 2: Create Student Profiles

Before uploading student work, you need to create a profile for each student.

**Student ID Format:**
- Format: `STU-XXX` where `XXX` is a 3-digit number
- Examples: `STU-001`, `STU-123`, `STU-999`
- **Important:** Use anonymous IDs only (no real names)

**Create a Student Profile:**

```json
POST /api/v1/students
{
  "student_id": "STU-001",
  "grade_level": 7
}
```

**Response:**
```json
{
  "student_id": "STU-001",
  "grade_level": 7,
  "vocabulary_size": 0,
  "proficiency_score": 0.0,
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T10:00:00Z"
}
```

**What Happens:**
- System creates a new vocabulary profile
- Initial vocabulary size is 0 (no words yet)
- Proficiency score starts at 0.0

---

## Understanding Student IDs

### Why Anonymous IDs?

Vocabulator uses anonymous student identifiers (like `STU-001`) to comply with **COPPA** (Children's Online Privacy Protection Act). This means:

- ✅ **No personal information collected** (no names, addresses, emails)
- ✅ **Privacy-protected** - student identity stays with you
- ✅ **COPPA-compliant** - safe for students under 13

### Creating Student IDs

**Best Practices:**
- Use sequential numbers: `STU-001`, `STU-002`, `STU-003`
- Keep a private mapping (e.g., spreadsheet) linking IDs to actual students
- **Never** include student names in API requests
- **Never** share your ID mapping publicly

**Example Mapping (Keep Private):**
```
STU-001 → [Student Name]
STU-002 → [Student Name]
STU-003 → [Student Name]
```

---

## Uploading Student Work

Vocabulator can analyze two types of student work:

1. **Transcripts** - Spoken language (from classroom discussions, presentations)
2. **Writing Samples** - Written work (essays, assignments, journals)

### Uploading Transcripts

**When to Use:**
- Classroom discussion transcripts
- Student presentation transcripts
- Oral response transcripts

**How to Upload:**

```json
POST /api/v1/transcripts/upload
{
  "student_id": "STU-001",
  "text": "Today we learned about photosynthesis and how plants convert sunlight into energy. I think it's really interesting how plants make their own food.",
  "session_date": "2025-11-10",
  "grade_level": 7
}
```

**What Happens:**
1. System stores the transcript securely
2. AI extracts vocabulary words the student used
3. Student profile is updated with new words
4. System identifies vocabulary gaps
5. New recommendations are generated

**Response:**
```json
{
  "success": true,
  "student_id": "STU-001",
  "words_extracted": 15,
  "profile_url": "/api/v1/students/STU-001/profile"
}
```

**Tips:**
- Upload transcripts regularly (weekly or bi-weekly)
- Include full sentences (not just word lists)
- Minimum 10 characters, maximum 50,000 characters
- Date should match when the session occurred

### Uploading Writing Samples

**When to Use:**
- Essays and compositions
- Journal entries
- Written assignments
- Creative writing

**How to Upload:**

```json
POST /api/v1/writing/upload
{
  "student_id": "STU-001",
  "text": "In my essay, I will discuss the importance of vocabulary in academic success. Vocabulary helps us understand complex texts and express our ideas clearly.",
  "assignment_id": "ESSAY-001",
  "grade_level": 7
}
```

**What Happens:**
- Same process as transcript upload
- Writing sample is stored separately
- Vocabulary extraction and recommendations are generated

**Response:**
```json
{
  "success": true,
  "student_id": "STU-001",
  "words_extracted": 12,
  "assignment_id": "ESSAY-001"
}
```

**Tips:**
- Use `assignment_id` to track specific assignments
- Upload multiple samples over time for better analysis
- Include complete sentences (not fragments)

### Batch Processing (Multiple Students)

For processing multiple students at once:

```json
POST /api/v1/batch/process
{
  "student_ids": ["STU-001", "STU-002", "STU-003"],
  "s3_paths": [
    "s3://bucket/transcripts/STU-001.txt",
    "s3://bucket/transcripts/STU-002.txt",
    "s3://bucket/transcripts/STU-003.txt"
  ],
  "grade_level": 7
}
```

**What Happens:**
- System processes all students in parallel
- Returns a job ID for tracking
- Processing happens asynchronously (takes 10-15 minutes)

**Check Job Status:**

```json
GET /api/v1/batch/{job_id}/status
```

**Response:**
```json
{
  "job_id": "job-abc123",
  "status": "RUNNING",
  "progress": 50,
  "created_at": "2025-11-10T10:00:00Z"
}
```

**Status Values:**
- `SUBMITTED` - Job submitted, waiting to start
- `RUNNING` - Currently processing
- `SUCCEEDED` - Completed successfully
- `FAILED` - Processing failed (check error_message)

---

## Understanding Vocabulary Reports

Vocabulator generates two types of reports:

1. **Student Profile Report** - Shows vocabulary growth over time
2. **Recommendations Report** - Lists recommended words for the student

### Student Profile Report

**What It Shows:**
- Total vocabulary size (number of unique words)
- Proficiency score (0-100, based on word difficulty)
- Recent word acquisitions
- Growth chart over time

**How to Access:**

```json
GET /api/v1/students/STU-001/profile
```

**Response:**
```json
{
  "student_id": "STU-001",
  "grade_level": 7,
  "vocabulary_size": 150,
  "proficiency_score": 75.5,
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T15:30:00Z"
}
```

**Understanding the Metrics:**

- **Vocabulary Size:** Total number of unique words the student has used
  - Grows as you upload more transcripts/writing samples
  - Typical range: 50-500 words for middle school students

- **Proficiency Score:** Calculated score (0-100) based on word difficulty
  - Higher score = student uses more advanced vocabulary
  - Based on Common Core grade-level standards
  - Updates automatically as new words are added

### Recommendations Report

**What It Shows:**
- 10-15 recommended words per student
- Definitions and example sentences
- Difficulty scores (0.0 = easy, 1.0 = hard)
- Rationale for each recommendation

**How to Access:**

```json
GET /api/v1/students/STU-001/recommendations
```

**Response:**
```json
{
  "recommendations": [
    {
      "student_id": "STU-001",
      "recommendation_date": "2025-11-10",
      "words": [
        {
          "word": "photosynthesis",
          "definition": "The process by which plants convert light into energy",
          "grade_level": 7,
          "difficulty_score": 0.6,
          "rationale": "Important for science curriculum, appropriate for grade level",
          "example_sentences": [
            "Plants use photosynthesis to make food.",
            "Without photosynthesis, plants cannot grow."
          ]
        }
      ],
      "status": "pending"
    }
  ],
  "total": 1
}
```

**Understanding Recommendations:**

- **Word Selection:** Based on Zone of Proximal Development (ZPD)
  - Not too easy (student already knows)
  - Not too hard (beyond current level)
  - Just right (challenging but achievable)

- **Difficulty Score:** 0.0-1.0 scale
  - 0.0-0.3: Easy (student should learn soon)
  - 0.4-0.7: Moderate (good challenge level)
  - 0.8-1.0: Hard (advanced, may need support)

- **Status Values:**
  - `pending` - Recommendation generated, not yet assigned
  - `assigned` - You've assigned this word to the student
  - `learned` - Student has learned this word

**Updating Recommendation Status:**

```json
PATCH /api/v1/recommendations/STU-001:2025-11-10/status
{
  "status": "assigned"
}
```

---

## Privacy and COPPA Compliance

### What Data Is Collected?

**Collected:**
- ✅ Anonymous student IDs (`STU-001`, etc.)
- ✅ Grade level (6, 7, or 8)
- ✅ Transcript text (what students said)
- ✅ Writing sample text (what students wrote)
- ✅ Vocabulary words extracted from text

**NOT Collected:**
- ❌ Student names
- ❌ Email addresses
- ❌ Physical addresses
- ❌ Phone numbers
- ❌ Any personally identifiable information (PII)

### How Data Is Stored

- **Raw Transcripts/Writing:** Stored securely in AWS S3
- **Student Profiles:** Stored in AWS DynamoDB
- **Recommendations:** Stored in AWS DynamoDB
- **All Data:** Encrypted at rest and in transit

### Data Retention

- Student profiles: Retained while actively used
- Recommendations: Auto-deleted after 30 days (TTL)
- Raw transcripts: Retained per school policy

### Your Responsibilities

- **Keep ID Mapping Private:** Don't share your student ID mapping
- **Use Anonymous IDs:** Never include student names in API requests
- **Secure Access:** Protect your API credentials
- **Follow School Policy:** Comply with your school's data policies

---

## Frequently Asked Questions

### General Questions

**Q: How often should I upload student work?**  
A: Weekly or bi-weekly uploads provide the best results. More frequent uploads help track vocabulary growth over time.

**Q: Can I upload the same transcript twice?**  
A: Yes, but it won't add new vocabulary if the words are already in the student's profile. The system deduplicates words automatically.

**Q: What's the minimum text length?**  
A: At least 10 characters. For best results, use complete sentences (50+ characters).

**Q: How long does processing take?**  
A: Single uploads: 5-10 seconds. Batch processing: 10-15 minutes for 30 students.

### About Recommendations

**Q: How many words are recommended?**  
A: Typically 10-15 words per recommendation set. This is manageable for students and teachers.

**Q: How are words selected?**  
A: Using Zone of Proximal Development (ZPD) principles - words that are challenging but achievable based on the student's current vocabulary level.

**Q: Can I customize recommendations?**  
A: Not in MVP. Future versions may allow filtering by subject area or difficulty level.

**Q: How often are recommendations updated?**  
A: Recommendations are generated automatically after each transcript/writing upload. New recommendations replace old ones.

### Technical Questions

**Q: What if an upload fails?**  
A: Check the error message in the response. Common issues:
- Student profile doesn't exist (create it first)
- Invalid student ID format (must be `STU-XXX`)
- Text too short or too long
- Invalid date format

**Q: Can I delete a student profile?**  
A: Not via API in MVP. Contact support for profile deletion.

**Q: How do I update a student's grade level?**  
A: Use the update endpoint:
```json
PUT /api/v1/students/STU-001
{
  "grade_level": 8
}
```

**Q: What if I make a mistake with a student ID?**  
A: Student IDs cannot be changed. You'll need to create a new profile with the correct ID and contact support to remove the incorrect one.

---

## Troubleshooting

### Common Issues

#### "Student profile not found" Error

**Problem:** You're trying to upload work for a student that doesn't have a profile.

**Solution:**
1. Create the student profile first:
   ```json
   POST /api/v1/students
   {
     "student_id": "STU-001",
     "grade_level": 7
   }
   ```
2. Then upload the transcript/writing sample

#### "Invalid student ID format" Error

**Problem:** Student ID doesn't match the required format.

**Solution:**
- Use format: `STU-XXX` where `XXX` is exactly 3 digits
- Examples: `STU-001`, `STU-123`, `STU-999`
- **Not valid:** `STU-1`, `STU-12`, `STU-1234`, `student-001`

#### "Text too short" Error

**Problem:** Uploaded text is less than 10 characters.

**Solution:**
- Include complete sentences
- Minimum 10 characters required
- For best results, use 50+ characters

#### Batch Job Stuck in "RUNNING" Status

**Problem:** Batch job appears to be running but not completing.

**Solution:**
1. Wait 15-20 minutes (normal processing time)
2. Check job status again: `GET /api/v1/batch/{job_id}/status`
3. If still running after 30 minutes, check `error_message` field
4. Contact support if issue persists

#### No Recommendations Generated

**Problem:** Upload succeeded but no recommendations appear.

**Possible Causes:**
- Student vocabulary is already very advanced (no gaps found)
- Text didn't contain enough vocabulary to analyze
- System is still processing (wait a few minutes)

**Solution:**
1. Upload more transcripts/writing samples
2. Wait a few minutes and check again
3. Verify student profile shows vocabulary_size > 0
4. Contact support if issue persists

---

## Support

### Getting Help

**Documentation:**
- [API Documentation](api-documentation.md) - Complete API reference
- [Architecture Guide](architecture.md) - System overview

**Contact:**
- **Email:** [support email]
- **Issue Tracker:** [GitHub Issues URL]
- **Documentation:** `_docs/` directory

### Reporting Issues

When reporting an issue, please include:

1. **What you were trying to do:**
   - Upload transcript? Writing sample? Get recommendations?

2. **What happened:**
   - Error message (if any)
   - Unexpected behavior

3. **Student ID** (anonymized):
   - Format: `STU-XXX`
   - **Never include real student names**

4. **Request details:**
   - Endpoint used
   - Request body (anonymized)
   - Response received

5. **When it happened:**
   - Date and time
   - How often it occurs

---

## Quick Reference

### Student ID Format
```
STU-XXX  (where XXX is 3 digits)
Examples: STU-001, STU-123, STU-999
```

### Common Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/students` | POST | Create student profile |
| `/api/v1/students/{id}/profile` | GET | Get student profile |
| `/api/v1/transcripts/upload` | POST | Upload transcript |
| `/api/v1/writing/upload` | POST | Upload writing sample |
| `/api/v1/students/{id}/recommendations` | GET | Get recommendations |
| `/api/v1/batch/process` | POST | Batch process multiple students |

### Text Requirements

- **Minimum:** 10 characters
- **Maximum:** 50,000 characters
- **Best Practice:** Complete sentences, 50+ characters

### Grade Levels

- **6** - 6th grade
- **7** - 7th grade
- **8** - 8th grade

---

**Thank you for using Vocabulator!**

If you have questions or need help, don't hesitate to reach out to support.

---

**Last Updated:** 2025-11-12  
**Version:** 1.0.0 (MVP)

