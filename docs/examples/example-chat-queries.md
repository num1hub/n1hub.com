# Example: Chat Queries

This guide demonstrates effective chat query patterns and expected results.

## Prerequisites

You should have at least 2-3 capsules uploaded with related content. For best results, use the demo dataset or upload several related documents.

## Query Patterns

### Pattern 1: Direct Questions

**Query:** "What is machine learning?"

**Expected:**
- Answer defines machine learning
- Citations reference relevant capsules
- Metrics show good retrieval recall

**Best Practices:**
- Be specific and clear
- Use complete questions
- Reference topics from your capsules

### Pattern 2: Comparative Questions

**Query:** "What are the differences between supervised and unsupervised learning?"

**Expected:**
- Answer compares both approaches
- Multiple citations showing different perspectives
- High citation share metric

**Best Practices:**
- Ask about relationships
- Compare concepts
- Use "differences", "similarities", "compare"

### Pattern 3: Summarization

**Query:** "Summarize my notes on neural networks"

**Expected:**
- Concise summary of relevant capsules
- Key points highlighted
- Sources listed

**Best Practices:**
- Use "summarize", "overview", "key points"
- Reference specific topics
- Use appropriate scope

### Pattern 4: Follow-up Questions

**Query 1:** "What is backpropagation?"
**Query 2:** "How does it relate to gradient descent?"

**Expected:**
- Second query builds on first
- Answers reference related concepts
- Citations may overlap or expand

**Best Practices:**
- Build on previous answers
- Reference earlier responses
- Ask progressive questions

## Scope-Specific Examples

### My Capsules Scope

**Use Case:** Personal knowledge queries

**Query:** "What have I learned about deep learning?"

**Expected:**
- Only your capsules are searched
- Answers reflect your content
- Personal perspective

### All Public Scope

**Use Case:** General knowledge queries

**Query:** "What are best practices for neural network training?"

**Expected:**
- Higher quality, curated content
- Answers from multiple sources
- Score threshold ensures quality

### Collection: Inbox Scope

**Use Case:** Recent work queries

**Query:** "What have I been working on this week?"

**Expected:**
- Only last 30 days of capsules
- Recent content prioritized
- Timeline-focused answers

### Tag-Based Scope

**Use Case:** Topic-specific queries

**Tags Selected:** `neural-networks`, `training`
**Query:** "Explain training techniques"

**Expected:**
- Only capsules with selected tags
- Focused, relevant answers
- Precise topic coverage

## Example Workflow

### Scenario: Research Project

1. **Upload Multiple Documents**
   - "Introduction to Neural Networks"
   - "Backpropagation Explained"
   - "CNN Architectures"

2. **Query with My Capsules**
   \`\`\`
   Query: "What are the key concepts in neural network training?"
   \`\`\`
   - Should reference all three documents
   - Answer covers training, backpropagation, architectures

3. **Follow-up Query**
   \`\`\`
   Query: "How do CNNs differ from standard neural networks?"
   \`\`\`
   - Focuses on CNN document
   - Compares architectures

4. **Tag-Based Query**
   - Select tags: `neural-networks`, `training`
   - Query: "What training methods are most effective?"
   - Filters to relevant content

## Understanding Responses

### Good Response Indicators

- **Multiple Citations**: 2+ distinct capsule IDs
- **High Metrics**: 
  - Retrieval recall ≥ 0.85
  - Faithfulness ≥ 0.95
  - Citation share ≥ 0.70
- **Relevant Answer**: Directly addresses query
- **Source Coverage**: References multiple aspects

### Fallback Response

If you see: `"idk+dig_deep"`

**Possible Causes:**
- Insufficient capsules (< 2)
- No relevant content for query
- Scope too restrictive
- Content not included in RAG

**Solutions:**
- Upload more related content
- Try different scope
- Broaden query
- Check capsule `include_in_rag` status

## Advanced Techniques

### Multi-Step Queries

1. Start broad: "What is machine learning?"
2. Narrow down: "What are the main types?"
3. Deep dive: "Explain supervised learning in detail"

### Scope Switching

1. Query with "My Capsules" for personal content
2. Switch to "All Public" for general knowledge
3. Use tags for specific topics

### Query Refinement

**Initial:** "Tell me about AI"
**Refined:** "What are the key differences between machine learning and deep learning?"

Refined queries get better results by being specific.

## Common Mistakes

**Too Vague:**
- ❌ "Stuff about computers"
- ✅ "What are the applications of neural networks?"

**Too Broad:**
- ❌ "Everything about AI"
- ✅ "What are the main types of machine learning?"

**Wrong Scope:**
- ❌ Using "All Public" for personal notes
- ✅ Use "My Capsules" for your content

**Insufficient Content:**
- ❌ Only 1 capsule uploaded
- ✅ Upload 3+ related capsules for best results

## Tips for Success

1. **Be Specific**: Clear, focused questions work best
2. **Use Context**: Reference topics from your capsules
3. **Choose Right Scope**: Match scope to query intent
4. **Build Knowledge**: Upload related content over time
5. **Review Citations**: Check source capsules to verify answers
6. **Iterate**: Refine queries based on results

## Example Queries by Domain

### Technical Documentation

- "How does the authentication system work?"
- "What are the API endpoints for user management?"
- "Explain the database schema"

### Research Papers

- "What are the main findings?"
- "How does this compare to previous work?"
- "What methodology was used?"

### Meeting Notes

- "What decisions were made?"
- "What are the action items?"
- "Who is responsible for what?"

### Learning Materials

- "Explain the key concepts"
- "What are the practical applications?"
- "How does this relate to [other topic]?"
