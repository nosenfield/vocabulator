# Vocabulator Required Reading List

**Project:** Personalized Vocabulary Recommendation Engine for Middle School Students
**Version:** 1.0.0 (MVP)
**Last Updated:** 2025-11-10

---

## Overview

This document provides a curated list of essential resources for developers working on the Vocabulator project. These resources cover the specific technologies, frameworks, and domain knowledge necessary to contribute effectively.

**Target Audience:** New developers joining the project, or existing team members ramping up on specific technologies.

**Estimated Total Reading Time:** 8-12 hours

---

## Table of Contents

1. [Priority 0: Essential Reading (Must Read First)](#priority-0-essential-reading-must-read-first)
2. [Priority 1: Core Technologies](#priority-1-core-technologies)
3. [Priority 2: AWS Services](#priority-2-aws-services)
4. [Priority 3: Domain Knowledge](#priority-3-domain-knowledge)
5. [Priority 4: Advanced Topics](#priority-4-advanced-topics)
6. [Additional Resources](#additional-resources)

---

## Priority 0: Essential Reading (Must Read First)

**Complete these before writing any code.**

### Project Documentation (Internal)

| Resource | Type | Time | Description |
|----------|------|------|-------------|
| [PRD_Flourish_Schools_Personalized_Vocabulary_Recommendation_Engine_for_.md](PRD_Flourish_Schools_Personalized_Vocabulary_Recommendation_Engine_for_.md) | Internal Doc | 20 min | Product requirements, goals, success metrics |
| [architecture.md](architecture.md) | Internal Doc | 45 min | System architecture, tech stack, data flow |
| [task-list.md](task-list.md) | Internal Doc | 30 min | MVP task breakdown, timeline, dependencies |
| [best-practices.md](best-practices.md) | Internal Doc | 60 min | Coding standards, patterns, guidelines |
| [test-first-workflow.md](guides/test-first-workflow.md) | Internal Doc | 15 min | TDD process, red-green-refactor cycle |

**Total Time: ~3 hours**

**Why Essential:**
- Understand product goals and user needs
- Know system architecture and design decisions
- Learn coding standards and team conventions
- Master the test-first development workflow

---

## Priority 1: Core Technologies

**Master these technologies - they're used daily.**

### Python 3.11+ Fundamentals

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Python Type Hints Guide | Tutorial | 30 min | [Real Python: Type Checking](https://realpython.com/python-type-checking/) | Essential for type hints (we use mypy strict mode) |
| Async/Await in Python | Tutorial | 45 min | [Real Python: Async IO](https://realpython.com/async-io-python/) | Understand async patterns (FastAPI is async) |
| Context Managers | Tutorial | 20 min | [Python Docs: Context Managers](https://docs.python.org/3/library/contextlib.html) | Used extensively for resource management |
| Python Pathlib | Tutorial | 15 min | [Real Python: Pathlib](https://realpython.com/python-pathlib/) | Modern file path handling |

**Total Time: ~2 hours**

**Key Takeaways:**
- Type hints are mandatory (all function signatures)
- Use async/await for I/O operations
- Context managers for cleanup (databases, files)
- Pathlib over os.path

---

### FastAPI

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| FastAPI Tutorial | Official Docs | 60 min | [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/) | Complete tutorial sections 1-9 |
| Dependency Injection | Official Docs | 30 min | [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) | Critical pattern we use extensively |
| Request/Response Models | Official Docs | 20 min | [FastAPI Pydantic](https://fastapi.tiangolo.com/tutorial/body/) | All API models use Pydantic |
| Testing FastAPI | Official Docs | 20 min | [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/) | Using TestClient |

**Total Time: ~2 hours**

**Key Takeaways:**
- Dependency injection for database clients, auth
- Pydantic models for validation
- Automatic OpenAPI docs
- TestClient for endpoint testing

**Code Example to Practice:**
```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.post("/items")
async def create_item(item: ItemCreate, db: Database = Depends(get_db)):
    return db.create(item)
```

---

### Pydantic V2

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Pydantic V2 Concepts | Official Docs | 30 min | [Pydantic Concepts](https://docs.pydantic.dev/latest/concepts/models/) | Data validation fundamentals |
| Field Validators | Official Docs | 20 min | [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/) | Custom validation logic |
| Pydantic Config | Official Docs | 15 min | [Model Config](https://docs.pydantic.dev/latest/concepts/config/) | Configuration options |

**Total Time: ~1 hour**

**Key Takeaways:**
- BaseModel for all data structures
- Field() for constraints and documentation
- Validators for custom logic
- Automatic JSON serialization

---

### Pytest

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Pytest Documentation | Official Docs | 45 min | [Pytest Getting Started](https://docs.pytest.org/en/stable/getting-started.html) | Basic pytest usage |
| Fixtures | Official Docs | 30 min | [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html) | Setup/teardown for tests |
| Parametrize | Official Docs | 15 min | [Pytest Parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) | Test multiple scenarios |
| Mocking | Tutorial | 30 min | [Real Python: Mocking](https://realpython.com/python-mock-library/) | Mock external dependencies |
| pytest-asyncio | Docs | 15 min | [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Testing async functions |

**Total Time: ~2 hours**

**Key Takeaways:**
- Write tests before implementation (TDD)
- Use fixtures for setup/teardown
- Parametrize for multiple test cases
- Mock external services (OpenAI, AWS)
- pytest-asyncio for async tests

---

### OpenAI API

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| OpenAI API Quickstart | Official Docs | 30 min | [OpenAI Quickstart](https://platform.openai.com/docs/quickstart) | Basic API usage |
| Chat Completions API | Official Docs | 30 min | [Chat Completions](https://platform.openai.com/docs/guides/chat-completions) | Core API we use |
| Prompt Engineering Guide | Official Docs | 45 min | [Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering) | Writing effective prompts |
| Best Practices | Official Docs | 20 min | [OpenAI Best Practices](https://platform.openai.com/docs/guides/production-best-practices) | Safety, reliability, performance |
| Rate Limits | Official Docs | 15 min | [Rate Limits](https://platform.openai.com/docs/guides/rate-limits) | Understanding limits and tiers |

**Total Time: ~2.5 hours**

**Key Takeaways:**
- Use GPT-4o-mini for extraction (cheap)
- Use GPT-4o for analysis (expensive but better)
- Temperature 0.1-0.3 for consistent extraction
- Implement exponential backoff for rate limits
- Monitor token usage and costs

**Cost Awareness (Critical):**
- GPT-4o-mini: ~$0.15 per 1M input tokens
- GPT-4o: ~$2.50 per 1M input tokens
- 1 transcript (2000 words) ≈ 2500 tokens
- Always use mini for extraction, GPT-4o only for final analysis

---

## Priority 2: AWS Services

**Learn AWS services used in architecture.**

### AWS General

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| AWS Well-Architected Framework | Official Docs | 30 min | [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/) | Best practices overview |
| IAM Best Practices | Official Docs | 30 min | [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) | Security fundamentals |
| boto3 Basics | Official Docs | 30 min | [Boto3 Quickstart](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html) | AWS SDK for Python |

**Total Time: ~1.5 hours**

**Key Takeaways:**
- Least privilege IAM policies
- Use IAM roles (not long-term credentials)
- boto3 for all AWS operations
- Configure retries and timeouts

---

### DynamoDB

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| DynamoDB Core Components | Official Docs | 30 min | [DynamoDB Core Components](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html) | Tables, items, attributes |
| DynamoDB Best Practices | Official Docs | 45 min | [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html) | Query patterns, GSI usage |
| boto3 DynamoDB | Official Docs | 30 min | [Boto3 DynamoDB](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html) | Python SDK for DynamoDB |
| DynamoDB Python Examples | Tutorial | 30 min | [DynamoDB Python Tutorial](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.html) | Hands-on examples |

**Total Time: ~2 hours**

**Key Takeaways:**
- Use `get_item` for single item (not query)
- Use GSI for non-key queries
- Batch operations for multiple items
- Eventually consistent reads (cheaper)
- Avoid `scan` operations

**Code Example:**
```python
# Good - Get single item
response = table.get_item(Key={"student_id": "STU-001"})

# Good - Query with GSI
response = table.query(
    IndexName="grade_level-index",
    KeyConditionExpression=Key("grade_level").eq(7)
)

# Bad - Scan (expensive)
response = table.scan()
```

---

### S3

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| S3 Getting Started | Official Docs | 20 min | [S3 Getting Started](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GetStartedWithS3.html) | Basic concepts |
| S3 Best Practices | Official Docs | 30 min | [S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html) | Security and performance |
| boto3 S3 | Official Docs | 30 min | [Boto3 S3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3.html) | Python SDK for S3 |
| S3 Lifecycle Policies | Official Docs | 20 min | [Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) | Automatic cleanup |

**Total Time: ~1.5 hours**

**Key Takeaways:**
- Multipart upload for files > 5MB
- Server-side encryption by default
- Presigned URLs for temporary access
- Lifecycle policies for auto-deletion
- Never make buckets public

---

### AWS Lambda

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Lambda Foundations | Official Docs | 30 min | [Lambda Foundations](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) | Lambda basics |
| Lambda Best Practices | Official Docs | 30 min | [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) | Performance, cold starts |
| Lambda Python | Official Docs | 20 min | [Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html) | Python runtime |

**Total Time: ~1.5 hours**

**Key Takeaways:**
- Initialize clients outside handler
- Set appropriate memory (512MB-1GB)
- Use environment variables for config
- Keep deployment package small
- Timeout: 30s for API, longer for batch

**Cold Start Optimization:**
```python
# Initialize outside handler (reused)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    # Handler code uses pre-initialized clients
    pass
```

---

### AWS Batch + Fargate

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| AWS Batch Concepts | Official Docs | 30 min | [AWS Batch Concepts](https://docs.aws.amazon.com/batch/latest/userguide/what-is-batch.html) | Jobs, queues, compute environments |
| AWS Fargate | Official Docs | 20 min | [Fargate Overview](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) | Serverless containers |
| Batch Best Practices | Official Docs | 30 min | [Batch Best Practices](https://docs.aws.amazon.com/batch/latest/userguide/best-practices.html) | Optimization strategies |

**Total Time: ~1.5 hours**

**Key Takeaways:**
- Batch for job orchestration
- Fargate for serverless compute
- Job definition = container config
- Automatic retries and scaling
- Cost-effective for batch workloads

---

## Priority 3: Domain Knowledge

**Understand the educational and technical domain.**

### Vocabulary Development & Assessment

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Zone of Proximal Development | Article | 20 min | [Wikipedia: ZPD](https://en.wikipedia.org/wiki/Zone_of_proximal_development) | Learning theory foundation |
| Common Core State Standards | Official | 30 min | [Common Core Standards](http://www.corestandards.org/ELA-Literacy/) | ELA standards for grades 6-8 |
| Vocabulary Instruction Best Practices | Research | 30 min | [Reading Rockets: Vocabulary](https://www.readingrockets.org/topics/vocabulary-instruction) | Effective vocabulary teaching |

**Total Time: ~1.5 hours**

**Key Takeaways:**
- ZPD: Optimal challenge level (not too easy, not too hard)
- Common Core defines grade-level expectations
- Vocabulary instruction should be contextualized
- Multiple exposures needed for retention

---

### COPPA & Student Privacy

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| COPPA Compliance Guide | Official | 30 min | [FTC COPPA FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions) | Under-13 privacy requirements |
| FERPA Overview | Official | 20 min | [ED.gov FERPA](https://studentprivacy.ed.gov/ferpa) | Student records privacy |
| Educational Data Privacy | Article | 20 min | [Student Privacy Matters](https://studentprivacymatters.org/) | Best practices overview |

**Total Time: ~1 hour**

**Key Takeaways:**
- COPPA applies to children under 13
- Anonymous student IDs avoid COPPA complexity
- FERPA governs educational records
- Schools can consent as proxy for educational tools
- Never collect PII without clear legal basis

---

### Natural Language Processing (NLP) Concepts

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| NLP Overview | Tutorial | 30 min | [Stanford NLP](https://web.stanford.edu/~jurafsky/slp3/) | Read Chapter 1 (Introduction) |
| Tokenization | Article | 15 min | [NLP Tokenization](https://nlp.stanford.edu/IR-book/html/htmledition/tokenization-1.html) | Breaking text into words |
| Lemmatization vs Stemming | Tutorial | 15 min | [Lemmatization Guide](https://nlp.stanford.edu/IR-book/html/htmledition/stemming-and-lemmatization-1.html) | Word normalization |

**Total Time: ~1 hour**

**Key Takeaways:**
- Tokenization: Split text into words
- Lemmatization: Convert to base form (running → run)
- Stopwords: Common words to exclude (the, a, is)
- Part-of-speech: Word grammatical roles
- (Note: OpenAI handles most NLP for us)

---

## Priority 4: Advanced Topics

**Optional but helpful for advanced features.**

### Parallel Processing in Python

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Multiprocessing Guide | Official Docs | 30 min | [Python Multiprocessing](https://docs.python.org/3/library/multiprocessing.html) | CPU-bound parallelism |
| asyncio for Concurrency | Tutorial | 45 min | [Real Python: asyncio](https://realpython.com/async-io-python/) | I/O-bound concurrency |
| Threading vs Multiprocessing vs Async | Article | 20 min | [Concurrency in Python](https://realpython.com/python-concurrency/) | When to use each |

**Total Time: ~1.5 hours**

**Key Decision Matrix:**
- **CPU-bound (data processing)** → multiprocessing
- **I/O-bound (API calls, DB)** → asyncio
- **Thread-unsafe libraries** → multiprocessing

---

### Prompt Engineering

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| Prompt Engineering Guide | Guide | 60 min | [Prompt Engineering Guide](https://www.promptingguide.ai/) | Comprehensive techniques |
| OpenAI Prompt Examples | Examples | 30 min | [OpenAI Examples](https://platform.openai.com/examples) | Practical patterns |
| Chain-of-Thought Prompting | Paper | 30 min | [CoT Paper](https://arxiv.org/abs/2201.11903) | Advanced reasoning technique |

**Total Time: ~2 hours**

**Key Techniques:**
- Few-shot learning (provide examples)
- Chain-of-thought (step-by-step reasoning)
- Output format specification (JSON)
- Temperature control (lower = more consistent)
- System vs user messages

---

### CloudFormation / Infrastructure as Code

| Resource | Type | Time | Link | Description |
|----------|------|------|------|-------------|
| CloudFormation Basics | Official Docs | 45 min | [CloudFormation Getting Started](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/GettingStarted.html) | Templates, stacks, resources |
| CloudFormation Best Practices | Official Docs | 30 min | [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html) | Organization, reuse |

**Total Time: ~1.5 hours**

**Key Takeaways:**
- Infrastructure defined in YAML/JSON
- Stacks = deployed resources
- Parameters for configurability
- Outputs for cross-stack references
- Nested stacks for organization

---

## Additional Resources

### Books (Optional Deep Dives)

| Title | Author | Topics | When to Read |
|-------|--------|--------|--------------|
| Python Testing with pytest | Brian Okken | Testing best practices | When writing complex tests |
| Robust Python | Patrick Viafore | Type hints, maintainability | When refactoring/scaling |
| Designing Data-Intensive Applications | Martin Kleppmann | Distributed systems, databases | When optimizing architecture |

---

### Video Courses (Optional)

| Course | Platform | Duration | Topics |
|--------|----------|----------|--------|
| FastAPI Full Course | YouTube (freeCodeCamp) | 4 hours | Comprehensive FastAPI |
| AWS Developer Associate | A Cloud Guru | 20 hours | AWS services deep dive |
| Advanced Pytest | Test Automation University | 2 hours | Fixtures, plugins, CI/CD |

---

### Tools & Utilities

| Tool | Purpose | Documentation |
|------|---------|---------------|
| **LocalStack** | Local AWS emulation | [LocalStack Docs](https://docs.localstack.cloud/) |
| **moto** | Mock AWS in tests | [moto Docs](https://docs.getmoto.org/) |
| **Black** | Code formatting | [Black Docs](https://black.readthedocs.io/) |
| **Ruff** | Fast linting | [Ruff Docs](https://docs.astral.sh/ruff/) |
| **mypy** | Static type checking | [mypy Docs](https://mypy.readthedocs.io/) |
| **pytest-cov** | Test coverage | [pytest-cov Docs](https://pytest-cov.readthedocs.io/) |

---

## Learning Path Recommendations

### Week 1: Foundation
1. Read all Priority 0 (Project Documentation)
2. Complete Python 3.11+ fundamentals
3. Work through FastAPI tutorial
4. Practice with pytest basics

**Outcome:** Understand project goals, can write basic API endpoints with tests

---

### Week 2: Core Technologies
1. Deep dive into Pydantic V2
2. Learn OpenAI API and prompt engineering
3. Complete AWS General and IAM sections
4. Study DynamoDB patterns

**Outcome:** Can integrate OpenAI API, understand data storage patterns

---

### Week 3: AWS Deep Dive
1. Learn S3 operations
2. Understand Lambda best practices
3. Study AWS Batch + Fargate
4. Practice with boto3

**Outcome:** Can work with all AWS services in architecture

---

### Week 4: Domain & Advanced
1. Study vocabulary development concepts
2. Review COPPA/FERPA requirements
3. Learn parallel processing patterns
4. Explore advanced prompt engineering

**Outcome:** Understand domain context, can optimize performance

---

## Quick Reference Cheat Sheets

### Essential Commands

```bash
# Development
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v --cov=src
black src/ tests/
ruff check src/ tests/
mypy src/

# AWS
aws s3 ls s3://vocabulator-data-dev/
aws dynamodb get-item --table-name StudentProfiles --key '{"student_id": {"S": "STU-001"}}'
aws lambda invoke --function-name vocabulator-api response.json

# Docker
docker build -t vocabulator-batch -f infrastructure/docker/Dockerfile.batch .
docker run vocabulator-batch

# Git
git checkout -b feat/new-feature
git commit -m "feat: add new feature"
git push origin feat/new-feature
```

---

### Common Patterns

**OpenAI API Call:**
```python
response = await openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a vocabulary expert."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=2000
)
```

**DynamoDB Query:**
```python
response = table.query(
    IndexName="grade_level-index",
    KeyConditionExpression=Key("grade_level").eq(7)
)
```

**FastAPI Endpoint:**
```python
@app.post("/api/v1/resource")
async def create_resource(
    request: ResourceRequest,
    db: Annotated[Database, Depends(get_db)]
):
    result = await db.create(request)
    return result
```

---

## Onboarding Checklist

### Day 1
- [ ] Read PRD and architecture documents
- [ ] Set up development environment
- [ ] Clone repository and install dependencies
- [ ] Run tests to verify setup
- [ ] Review codebase structure

### Week 1
- [ ] Complete Priority 0 reading (project docs)
- [ ] Complete Python and FastAPI tutorials
- [ ] Write first test (TDD practice)
- [ ] Make first small contribution (documentation fix)

### Week 2
- [ ] Complete Priority 1 reading (core technologies)
- [ ] Implement small feature with tests
- [ ] Review OpenAI API integration code
- [ ] Deploy to dev environment

### Week 3
- [ ] Complete Priority 2 reading (AWS services)
- [ ] Work on AWS integration tasks
- [ ] Participate in code reviews
- [ ] Deploy to staging environment

### Month 1
- [ ] Complete all essential reading
- [ ] Contribute to multiple features
- [ ] Mentor another new developer
- [ ] Lead a feature from design to deployment

---

## Getting Help

### Internal Resources
- **Architecture Questions:** Review [architecture.md](architecture.md), ask tech lead
- **Code Standards:** Review [best-practices.md](best-practices.md)
- **Task Questions:** Review [task-list.md](task-list.md)
- **Test Workflow:** Review [test-first-workflow.md](guides/test-first-workflow.md)

### External Resources
- **Python:** [Python Discord](https://discord.gg/python), Stack Overflow
- **FastAPI:** [FastAPI Discord](https://discord.gg/fastapi), GitHub Discussions
- **AWS:** AWS Documentation, AWS re:Post
- **OpenAI:** [OpenAI Community Forum](https://community.openai.com/)

### Best Practices for Asking Questions
1. Search documentation first
2. Check existing issues/PRs
3. Provide context and what you've tried
4. Include error messages and logs
5. Create minimal reproducible example

---

## Progress Tracking

**Recommended approach:**
1. Create copy of this document
2. Check off resources as completed
3. Note key takeaways in Memory Bank
4. Track time spent on each section
5. Review with team lead weekly

---

## Updates & Maintenance

This document will be updated:
- When new technologies are added to tech stack
- When critical resources are discovered
- Quarterly review of link validity
- After major architectural changes

**Last Reviewed:** 2025-11-10
**Next Review:** 2026-02-10 (3 months)

---

**Document Status:** Active Reference
**Owner:** Technical Lead
**Feedback:** Submit suggestions via PR or team chat
