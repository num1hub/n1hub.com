# N1Hub v0.1 User Guide

Welcome to N1Hub v0.1! This guide will help you get started with transforming your content into structured capsules and using them for intelligent chat queries.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Content](#uploading-content)
3. [Understanding Capsules](#understanding-capsules)
4. [Managing Capsules](#managing-capsules)
5. [Using RAG-Scope Profiles](#using-rag-scope-profiles)
6. [Chat Best Practices](#chat-best-practices)
7. [Graph Navigation](#graph-navigation)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### What is N1Hub?

N1Hub transforms any content (documents, notes, articles) into structured "capsules" that can be searched, linked, and queried using AI-powered chat. Think of it as your personal knowledge base with intelligent search.

### Key Concepts

- **Capsule**: A structured representation of your content with metadata, summary, keywords, and links
- **Job**: A background process that converts your content into a capsule
- **RAG-Scope**: Filters that control which capsules are used for chat queries
- **Graph**: Visual representation of relationships between capsules

### First Steps

1. **Upload Your First Document**
   - Go to the home page (`/`)
   - Enter a title and paste your content
   - Add tags (comma-separated, 3-10 tags recommended)
   - Click "Create Capsule"

2. **Monitor Job Progress**
   - Go to `/inbox` to see your upload jobs
   - Jobs show real-time status updates
   - Wait for status to change to "succeeded"

3. **View Your Capsules**
   - Go to `/capsules` to see all your capsules
   - Click on any capsule to see details

4. **Try Chat**
   - Go to `/chat`
   - Ask questions about your capsules
   - See answers with citations

## Uploading Content

### Supported Content Types

N1Hub accepts any text content:
- Articles and blog posts
- Notes and documentation
- Research papers
- Meeting notes
- Code documentation
- Any structured or unstructured text

### Upload Form Fields

**Title** (Required)
- A descriptive title for your capsule
- Example: "Machine Learning Fundamentals"

**Material** (Required)
- The actual content to process
- Can be plain text, markdown, or structured content
- Minimum: A few sentences
- Recommended: 200+ words for best results

**Tags** (Optional, but recommended)
- Comma-separated tags (e.g., `machine-learning, ai, algorithms`)
- 3-10 tags are optimal
- Tags help with organization and filtering
- Use lowercase, descriptive terms

**Include in RAG scope** (Checkbox)
- Controls whether the capsule is used for chat queries
- Checked by default
- Uncheck for private notes you don't want in chat

### Upload Process

1. Fill in the form with your content
2. Click "Create Capsule"
3. A job is created and processing begins
4. You'll see the job ID and can monitor progress
5. Once complete, your capsule appears in `/capsules`

### Best Practices for Uploads

- **Clear Titles**: Use descriptive titles that summarize the content
- **Complete Content**: Include full context, not just snippets
- **Good Tags**: Use consistent tagging conventions
- **Relevant Tags**: Tags should reflect the content's main topics
- **Privacy**: Uncheck "Include in RAG" for sensitive content

## Understanding Capsules

### Capsule Structure

Each capsule has four main sections:

1. **Metadata**
   - Capsule ID (unique identifier)
   - Version, status, author
   - Creation timestamp
   - Language and source information
   - Tags (3-10 items)
   - Semantic hash (for deduplication)

2. **Core Payload**
   - The original content
   - Content type (usually `text/markdown`)
   - Truncation note (if content was too long)

3. **Neuro Concentrate**
   - Summary (70-140 words)
   - Keywords (5-12 items)
   - Entities, claims, insights
   - Questions and archetypes
   - Emotional charge score
   - Vector hint (for search)

4. **Recursive**
   - Links to other capsules
   - Actions and prompts
   - Confidence score

### Capsule Status

- **Draft**: Capsule is being created or needs review
- **Active**: Capsule is ready and included in searches
- **Archived**: Capsule is hidden but preserved

### Viewing Capsule Details

1. Go to `/capsules`
2. Click on any capsule card
3. View full details including:
   - Complete metadata
   - Original content
   - Generated summary and keywords
   - Links to related capsules
   - Semantic hash information

## Managing Capsules

### Filtering Capsules

On the `/capsules` page, you can filter by:
- **Include in RAG**: Show only capsules included in chat queries
- **Status**: Filter by draft, active, or archived
- **Tags**: Filter by specific tags (coming soon)

### Updating Capsules

You can update capsules using the PATCH API or through the UI:

**Update Tags**
- Change tags to improve organization
- Tags must be 3-10 items
- Tags are automatically lowercased
- PII is not allowed in tags

**Change Status**
- Move capsules between draft, active, and archived
- Archived capsules are hidden from normal views
- Status changes are logged in audit trail

**Toggle RAG Inclusion**
- Include/exclude capsules from chat queries
- Useful for private notes or test content
- Changes are logged in audit trail

### Exporting Capsules

- Click on a capsule to view details
- Use the export button to download as JSON
- JSON includes all capsule sections

## Using RAG-Scope Profiles

RAG-Scope controls which capsules are used when answering chat queries. Choose the right scope for your needs.

### My Capsules (Default)

**When to use**: Personal queries about your own content

**What it includes**:
- Only your active capsules
- Capsules with `include_in_rag=true`
- Default scope for all queries

**Example queries**:
- "What did I write about machine learning?"
- "Summarize my notes on project X"

### All Public

**When to use**: Queries about public/shared content

**What it includes**:
- Active capsules from all users (in multi-user setup)
- Capsules meeting quality threshold (score ≥ 0.62)
- Higher quality, curated content

**Example queries**:
- "What are the best practices for..."
- "What do others know about..."

### Collection: Inbox

**When to use**: Recent content only

**What it includes**:
- Capsules created in the last 30 days
- Active capsules only
- Great for recent work

**Example queries**:
- "What have I been working on recently?"
- "Summarize my latest notes"

### Tags

**When to use**: Focused queries on specific topics

**What it includes**:
- Capsules matching selected tags
- Active capsules only
- Precise topic filtering

**Example queries**:
- Select tags: `machine-learning`, `neural-networks`
- Query: "Explain the relationship between these concepts"

### Switching Scopes

1. Go to `/chat` page
2. Use the RAG-Scope selector at the top
3. Choose your desired scope profile
4. For tag-based scope, select specific tags
5. Your queries will use the selected scope

## Chat Best Practices

### Writing Effective Queries

**Be Specific**
- ❌ "Tell me about stuff"
- ✅ "What are the key concepts in machine learning?"

**Ask Focused Questions**
- ❌ "Everything about AI"
- ✅ "What are the differences between supervised and unsupervised learning?"

**Use Context**
- Reference specific topics from your capsules
- Mention tags or document titles
- Ask follow-up questions

### Understanding Answers

**Citations**
- Answers include source capsule IDs
- Click on citations to view source capsules
- Multiple citations indicate well-grounded answers

**Metrics**
- **Retrieval Recall**: How well relevant capsules were found
- **Faithfulness**: How accurately the answer reflects sources
- **Citation Share**: Percentage of answer backed by citations

**Fallback Messages**
- If insufficient sources: "idk+dig_deep"
- System needs ≥2 distinct sources for quality answers
- Add more capsules to improve answers

### Improving Chat Results

1. **Upload More Content**: More capsules = better answers
2. **Use Good Tags**: Consistent tagging improves retrieval
3. **Choose Right Scope**: Match scope to your query intent
4. **Ask Follow-ups**: Build on previous answers
5. **Check Citations**: Verify answers match your content

## Graph Navigation

### Understanding the Graph

The graph view (`/graph`) shows relationships between capsules:
- **Nodes**: Your capsules
- **Edges**: Links between related capsules
- **Link Types**: Seven relationship types (extends, references, etc.)

### Using the Graph

1. **Navigate**: Click on capsules to see details
2. **Explore Links**: Follow connections to related content
3. **Discover Relationships**: Find unexpected connections
4. **Visualize Knowledge**: See how your content connects

### Link Types

- **extends**: One capsule builds on another
- **references**: One capsule mentions another
- **duplicates**: Similar or duplicate content
- **contradicts**: Conflicting information
- **supports**: Supporting evidence
- **challenges**: Challenging or questioning
- **related**: General relationship

## Troubleshooting

### Common Issues

**Job Stuck in "Processing"**
- Wait a bit longer (processing can take 10-30 seconds)
- Check if content is too large (max 20 MB)
- Try uploading again with smaller content

**No Answers in Chat**
- Ensure you have capsules with `include_in_rag=true`
- Check that you have ≥2 capsules for quality answers
- Try different RAG-Scope profiles
- Verify your query is clear and specific

**Capsule Not Appearing**
- Check job status in `/inbox`
- Verify job completed successfully
- Check filters on `/capsules` page
- Ensure capsule status is "active"

**Poor Chat Answers**
- Upload more related content
- Improve tag consistency
- Use more specific queries
- Check that relevant capsules are included in RAG scope

**Rate Limiting Errors**
- You've exceeded the rate limit (60 requests/minute)
- Wait a moment and try again
- Check the error message for retry time

### Getting Help

1. **Check Documentation**: Review this guide and architecture docs
2. **Check Health**: Visit `/healthz` endpoint to verify system status
3. **Review Logs**: Check job logs for error details
4. **Validate Capsules**: Use validation endpoints to check capsule quality

### Tips for Success

- **Start Small**: Upload a few documents to get familiar
- **Use Consistent Tags**: Develop a tagging system
- **Review Capsules**: Check generated summaries and keywords
- **Iterate**: Refine tags and content based on results
- **Explore**: Try different scopes and queries

## Advanced Features

### Observability

Monitor system health and quality:
- **Retrieval Metrics**: See how well search is working
- **Router Diagnostics**: Check for routing issues
- **Semantic Hash Integrity**: Verify data consistency
- **PII Scanning**: Ensure privacy compliance

### API Access

All features are available via API:
- Upload: `POST /api/import`
- List Capsules: `GET /api/capsules`
- Chat: `POST /api/chat`
- Update: `PATCH /api/capsules/{id}`

See [API Reference](api-reference.md) for details.

### Best Practices Summary

1. **Content**: Clear, complete, well-structured
2. **Tags**: Consistent, descriptive, 3-10 items
3. **Scope**: Match scope to query intent
4. **Queries**: Specific, focused, contextual
5. **Management**: Regular review and updates

## Next Steps

- Explore the [API Reference](api-reference.md) for programmatic access
- Check [Architecture Documentation](N1Hub-v0.1-architecture.md) for technical details
- Review [Deployment Guide](deployment.md) for production setup
- Try the example scenarios in `docs/examples/`

Happy capsule building!
