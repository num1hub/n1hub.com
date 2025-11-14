# Demo Dataset Example Queries

Example queries to test after loading the demo dataset, with expected behaviors.

## Setup

After loading the demo dataset, you should have capsules covering:
- Machine Learning Fundamentals
- Neural Networks
- Web Development
- (And more from other documents)

## Example Queries

### Query 1: Basic Concept

**Query:** "What is machine learning?"

**Expected:**
- Answer explains machine learning concepts
- Citations include ML Fundamentals capsule
- May include Neural Networks capsule if related
- Good retrieval and faithfulness metrics

**Scope:** My Capsules (default)

### Query 2: Comparison

**Query:** "What are the differences between supervised and unsupervised learning?"

**Expected:**
- Answer compares both approaches
- Citations from ML Fundamentals capsule
- Multiple distinct sources if available
- High citation share

**Scope:** My Capsules

### Query 3: Specific Topic

**Query:** "How do neural networks work?"

**Expected:**
- Answer explains neural network architecture
- Citations from Neural Networks capsule
- May reference ML Fundamentals for context
- Technical details included

**Scope:** My Capsules

### Query 4: Cross-Domain

**Query:** "What are the best practices for building web applications?"

**Expected:**
- Answer covers web development practices
- Citations from Web Development capsule
- Covers frontend, backend, and DevOps
- Practical recommendations

**Scope:** My Capsules

### Query 5: Tag-Based

**Tags:** `machine-learning`, `neural-networks`
**Query:** "Explain the relationship between machine learning and neural networks"

**Expected:**
- Answer connects both concepts
- Citations from both ML and Neural Networks capsules
- Explains how neural networks fit into ML
- High relevance

**Scope:** Tags

### Query 6: Recent Content

**Query:** "What have I learned recently?"

**Expected:**
- Answer summarizes recent capsules
- Only capsules from last 30 days
- May be empty if no recent content
- Time-filtered results

**Scope:** Collection: Inbox

## Testing Checklist

After loading demo dataset:

- [ ] Can query basic concepts
- [ ] Comparisons work with multiple capsules
- [ ] Tag-based filtering works
- [ ] Scope switching works
- [ ] Citations appear correctly
- [ ] Metrics are reasonable
- [ ] Answers are relevant

## Troubleshooting

**No Answers:**
- Ensure capsules have `include_in_rag=true`
- Check you have ≥2 capsules for quality answers
- Verify scope has matching content

**Poor Answers:**
- Upload more related content
- Use more specific queries
- Check tag consistency
- Try different scopes
