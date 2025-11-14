# Example: Using RAG-Scope Profiles

This guide demonstrates when and how to use each RAG-Scope profile.

## Overview

RAG-Scope controls which capsules are searched when answering chat queries. Choosing the right scope improves answer quality and relevance.

## Profile Comparison

| Profile | Use Case | Includes | Best For |
|---------|----------|----------|----------|
| **My Capsules** | Personal queries | Your active capsules | Personal knowledge base |
| **All Public** | General queries | Public capsules (score ≥ 0.62) | Curated, high-quality content |
| **Collection: Inbox** | Recent work | Last 30 days | Recent activity |
| **Tags** | Topic-specific | Matching tags | Focused research |

## My Capsules (Default)

### When to Use

- Querying your personal content
- Building on your own notes
- Reviewing what you've learned
- Personal knowledge management

### Example Queries

**Good:**
- "What did I write about neural networks?"
- "Summarize my notes on project X"
- "What concepts have I covered?"

**Not Ideal:**
- General knowledge questions (use "All Public")
- Questions about others' content

### How to Use

1. Go to `/chat`
2. Scope defaults to "My Capsules"
3. Ask your question
4. Answers use only your capsules

### Expected Behavior

- Only searches your capsules
- Answers reflect your content
- Personal perspective maintained
- No public/shared content included

## All Public

### When to Use

- General knowledge queries
- Best practices questions
- Curated content searches
- High-quality answers needed

### Example Queries

**Good:**
- "What are best practices for..."
- "What do experts recommend for..."
- "What is the standard approach to..."

**Not Ideal:**
- Personal notes queries
- Recent work questions

### How to Use

1. Go to `/chat`
2. Select "All Public" scope
3. Ask your question
4. Answers use public capsules meeting quality threshold

### Expected Behavior

- Only capsules with score ≥ 0.62 included
- Higher quality, curated content
- Multiple perspectives
- Quality gate ensures relevance

### Score Threshold

The public scope enforces a minimum similarity score (default: 0.62). This ensures:
- Only highly relevant content included
- Better answer quality
- Reduced noise

## Collection: Inbox

### When to Use

- Recent work queries
- This week's content
- Recent activity review
- Time-bound questions

### Example Queries

**Good:**
- "What have I been working on recently?"
- "Summarize my latest notes"
- "What did I learn this week?"

**Not Ideal:**
- Historical content queries
- All-time knowledge questions

### How to Use

1. Go to `/chat`
2. Select "Collection: Inbox" scope
3. Ask your question
4. Answers use only last 30 days of capsules

### Expected Behavior

- Only capsules from last 30 days
- Recent content prioritized
- Time-filtered results
- Great for current work

### Time Window

- **Window**: Last 30 days from current date
- **Based on**: `metadata.created_at` timestamp
- **Includes**: Active capsules only
- **Updates**: Automatically as time passes

## Tags

### When to Use

- Topic-specific queries
- Focused research
- Multi-topic comparison
- Precise filtering needed

### Example Queries

**Good:**
- Select tags: `neural-networks`, `training`
- Query: "What training methods work best?"
- Select tags: `python`, `api`
- Query: "How do I build a REST API in Python?"

**Not Ideal:**
- General queries (use "My Capsules")
- All content queries

### How to Use

1. Go to `/chat`
2. Select "Tags" scope type
3. Choose relevant tags (can select multiple)
4. Ask your question
5. Answers use only capsules with selected tags

### Expected Behavior

- Only capsules matching selected tags
- Precise topic filtering
- Can combine multiple tags
- Focused, relevant answers

### Tag Selection Tips

- **Be Specific**: Choose tags that match your query topic
- **Combine Tags**: Use multiple tags for intersection
- **Check Available**: See what tags exist in your capsules
- **Consistent Naming**: Use consistent tag conventions

## Real-World Scenarios

### Scenario 1: Research Project

**Setup:**
- Uploaded 10 research papers
- Tags: `research`, `ml`, `neural-networks`

**Workflow:**
1. **My Capsules** scope: "What have I learned from these papers?"
2. **Tags** scope (`research`, `ml`): "What are the key ML findings?"
3. **Collection: Inbox**: "What papers did I add this week?"

### Scenario 2: Personal Notes

**Setup:**
- Daily notes and journal entries
- Mixed topics and dates

**Workflow:**
1. **My Capsules** scope: "What did I write about today?"
2. **Collection: Inbox**: "What are my recent thoughts?"
3. **Tags** scope (`work`, `ideas`): "What work ideas do I have?"

### Scenario 3: Learning Journey

**Setup:**
- Learning materials on various topics
- Progressive content over time

**Workflow:**
1. **My Capsules** scope: "What have I learned about Python?"
2. **Collection: Inbox**: "What did I study recently?"
3. **Tags** scope (`python`, `advanced`): "What advanced Python concepts do I know?"

## Switching Between Scopes

### During a Conversation

You can switch scopes between queries:

1. Query 1 (My Capsules): "What is machine learning?"
2. Switch to Tags (`neural-networks`)
3. Query 2: "How do neural networks work?"
4. Switch to Collection: Inbox
5. Query 3: "What did I learn about this recently?"

### Scope Selection Strategy

1. **Start Broad**: Use "My Capsules" for general queries
2. **Narrow Down**: Use tags for specific topics
3. **Check Recent**: Use "Inbox" for time-bound questions
4. **Quality Focus**: Use "All Public" for curated answers

## Best Practices

### Choose the Right Scope

- **Personal content** → "My Capsules"
- **General knowledge** → "All Public"
- **Recent work** → "Collection: Inbox"
- **Specific topics** → "Tags"

### Combine Strategies

- Start with broader scope
- Narrow down with tags
- Use inbox for recent content
- Switch as needed

### Tag Management

- Use consistent tag names
- 3-10 tags per capsule
- Descriptive, lowercase tags
- Avoid PII in tags

### Query Optimization

- Match query to scope
- Use scope-appropriate questions
- Leverage scope strengths
- Experiment with different scopes

## Troubleshooting

### No Results

**Problem:** Query returns fallback message

**Solutions:**
- Check scope has matching capsules
- Verify capsules have `include_in_rag=true`
- Try broader scope
- Upload more content

### Too Many Results

**Problem:** Answers include irrelevant content

**Solutions:**
- Use tag-based scope for filtering
- Be more specific in query
- Use "All Public" for quality gate
- Refine tags

### Wrong Content

**Problem:** Answers don't match scope intent

**Solutions:**
- Verify scope selection
- Check capsule tags match
- Ensure correct scope type
- Review capsule status

## Advanced Usage

### Scope Combinations

While you can't combine scope types in a single query, you can:
1. Query with one scope
2. Review results
3. Switch scope
4. Query again for comparison

### Scope-Specific Queries

Tailor your query to the scope:
- **My Capsules**: "What did I write about..."
- **All Public**: "What are the best practices..."
- **Inbox**: "What have I been working on..."
- **Tags**: "Explain [topic] in detail..."

### Performance Considerations

- **My Capsules**: Fastest (smallest set)
- **Tags**: Fast (filtered set)
- **Inbox**: Medium (time-filtered)
- **All Public**: May be slower (quality checks)

## Summary

Choose your RAG-Scope based on:
1. **Query Intent**: What are you trying to find?
2. **Content Type**: Personal vs. public vs. recent
3. **Topic Focus**: General vs. specific
4. **Time Frame**: All-time vs. recent

Experiment with different scopes to find what works best for your use case!
