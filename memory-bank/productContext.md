# Product Context: vocabulator

**Last Updated**: 2025-11-12

## Why This Project Exists

### Problem Statement
Middle school educators currently struggle with manually identifying vocabulary gaps in students' language use. This process is time-consuming and often fails to provide personalized recommendations that align with each student's current proficiency level. The lack of tailored vocabulary development opportunities may hinder students' language acquisition and overall academic performance.

### User Pain Points
1. **Time-Consuming Manual Analysis**: Teachers spend hours analyzing student transcripts and writing samples to identify vocabulary gaps
2. **Lack of Personalization**: Generic vocabulary lists don't account for individual student proficiency levels
3. **Inconsistent Recommendations**: Manual analysis leads to inconsistent quality and coverage of vocabulary recommendations
4. **Limited Common Core Alignment**: Difficult to ensure recommendations align with grade-level Common Core standards

### Our Solution
Vocabulator automates the vocabulary gap analysis process using AI. The system:
- Analyzes student transcripts and writing samples to extract vocabulary
- Compares student vocabulary against Common Core standards for their grade level
- Identifies gaps and generates personalized recommendations (10-15 words per student)
- Provides teachers with HTML reports showing student profiles and recommendations
- Supports batch processing for entire classrooms

---

## Target Users

### Primary User Persona
- **Name**: Middle School Teacher
- **Role**: 6th-8th grade educator (ELA, Math, Science, or general)
- **Goals**: 
  - Quickly identify vocabulary gaps in students
  - Provide personalized vocabulary recommendations
  - Track student vocabulary growth over time
  - Reduce time spent on manual analysis
- **Frustrations**: 
  - Manual vocabulary analysis is time-consuming
  - Difficult to personalize recommendations for each student
  - Hard to ensure Common Core alignment
- **Tech Savviness**: Intermediate (comfortable with web interfaces, file uploads)

### Secondary User Persona
- **Name**: Curriculum Coordinator
- **Role**: School administrator responsible for curriculum alignment
- **Goals**: 
  - Ensure vocabulary recommendations align with Common Core standards
  - Track vocabulary development across grade levels
  - Generate reports for school leadership

---

## Key User Flows

### Flow 1: Upload Single Writing Sample
1. Teacher uploads writing sample via web form (text or file)
2. System stores raw text in S3
3. System extracts vocabulary using GPT-4o-mini
4. System updates student profile in DynamoDB
5. System returns response with words added
6. Result: Student profile updated with new vocabulary

### Flow 2: Batch Process Full-Day Transcripts
1. Teacher uploads CSV with student transcripts
2. System submits AWS Batch job
3. Batch processes transcripts in parallel (10 students per container)
4. For each student:
   - Extract vocabulary (GPT-4o-mini)
   - Update profile (DynamoDB)
   - Identify gaps vs Common Core (GPT-4o)
   - Generate recommendations (GPT-4o)
   - Store recommendations (DynamoDB)
   - Generate HTML report (Jinja2)
   - Upload report to S3
5. System sends completion notification
6. Teacher accesses results via API or S3 URLs
7. Result: All students have updated profiles and recommendations

### Flow 3: View Student Vocabulary Profile
1. Teacher requests student profile via API
2. System retrieves profile from DynamoDB
3. System retrieves recent recommendations
4. System generates HTML report
5. System returns report URL (S3 + CloudFront)
6. Result: Teacher views student vocabulary profile and recommendations

---

## Product Goals

### Short-term (MVP)
- Automate vocabulary gap identification for 500+ students
- Generate personalized recommendations aligned with Common Core
- Reduce teacher analysis time by 80%+
- Support batch processing for full classrooms
- Provide HTML reports for easy sharing

### Long-term (Future)
- Real-time processing (not just batch)
- Student-facing interface for vocabulary practice
- Advanced analytics and progress tracking
- Integration with LMS systems
- Multi-language support
- Mobile app for teachers

---

## Success Metrics

### User Engagement
- **Adoption Rate**: % of teachers using the system monthly
- **Upload Frequency**: Average number of uploads per teacher per week
- **Report Views**: Average number of reports viewed per teacher per month

### Business Impact
- **Time Saved**: Reduction in teacher time spent on vocabulary analysis (target: 80%+)
- **Student Growth**: Increase in novel words used by students over time
- **Teacher Satisfaction**: Positive feedback score (target: 4.0+ / 5.0)

### Technical Performance
- **Processing Speed**: Batch processing time (target: < 5 min for 50 students)
- **API Response Time**: p95 latency (target: < 200ms)
- **System Reliability**: Uptime (target: 99.9%)
- **Cost Efficiency**: Monthly cost per student (target: < $0.10/student)
