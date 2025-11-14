# Example: Managing Capsules

This guide demonstrates how to manage your capsules: updating tags, changing status, toggling RAG inclusion, and organizing your knowledge base.

## Overview

Capsule management allows you to:
- Update tags for better organization
- Change status (draft, active, archived)
- Toggle RAG inclusion
- Organize your knowledge base

## Updating Tags

### Why Update Tags?

- Improve organization
- Fix typos or inconsistencies
- Add missing tags
- Remove irrelevant tags
- Standardize tagging conventions

### How to Update Tags

**Via API:**
\`\`\`bash
curl -X PATCH http://localhost:8000/capsules/01HZ... \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["updated", "tags", "here"]
  }'
\`\`\`

**Via UI:**
1. Go to `/capsules`
2. Click on a capsule
3. Use the edit interface (if available)
4. Update tags
5. Save changes

### Tag Validation Rules

- **Minimum**: 3 tags required
- **Maximum**: 10 tags allowed
- **Format**: Lowercase, no spaces (use hyphens)
- **PII**: No personal identifiers allowed
- **Examples**: 
  - ✅ `machine-learning`, `neural-networks`, `ai`
  - ❌ `Machine Learning` (spaces), `john@email.com` (PII)

### Example: Tagging Workflow

**Initial Upload:**
- Tags: `ml`, `ai`, `basics`

**Refined Tags:**
- Tags: `machine-learning`, `artificial-intelligence`, `fundamentals`, `supervised-learning`

**Benefits:**
- More descriptive
- Consistent naming
- Better searchability
- Easier filtering

## Changing Status

### Status Options

- **Draft**: Being created or needs review
- **Active**: Ready and included in searches
- **Archived**: Hidden but preserved

### When to Change Status

**To Draft:**
- Content needs review
- Incomplete information
- Waiting for updates

**To Active:**
- Content is complete
- Ready for use
- Should appear in searches

**To Archived:**
- No longer relevant
- Superseded by newer content
- Want to hide but keep

### How to Change Status

**Via API:**
\`\`\`bash
curl -X PATCH http://localhost:8000/capsules/01HZ... \
  -H "Content-Type: application/json" \
  -d '{
    "status": "archived"
  }'
\`\`\`

**Status Change Effects:**
- **Active** → **Archived**: Hidden from normal views, excluded from searches
- **Archived** → **Active**: Restored to normal views, included in searches
- **Draft** → **Active**: Made available for use

### Example: Status Workflow

1. **Upload** → Status: "draft" (if validation issues)
2. **Review** → Check capsule quality
3. **Activate** → Change to "active" when ready
4. **Archive** → Change to "archived" when outdated

## Toggling RAG Inclusion

### What is RAG Inclusion?

Controls whether a capsule is used when answering chat queries.

- **Include in RAG** (`true`): Capsule is searched and can be cited
- **Exclude from RAG** (`false`): Capsule is hidden from chat queries

### When to Toggle

**Exclude from RAG:**
- Private notes
- Test content
- Incomplete drafts
- Personal information

**Include in RAG:**
- Complete, relevant content
- Knowledge you want to query
- Public or shared information
- Well-tagged content

### How to Toggle

**Via API:**
\`\`\`bash
curl -X PATCH http://localhost:8000/capsules/01HZ... \
  -H "Content-Type: application/json" \
  -d '{
    "include_in_rag": false
  }'
\`\`\`

**Effects:**
- Excluded capsules won't appear in chat answers
- Still visible in `/capsules` list
- Can be re-included later
- Changes are logged in audit trail

### Example: RAG Toggle Workflow

1. **Upload Test Content** → `include_in_rag: false`
2. **Verify Processing** → Check capsule structure
3. **Enable for Use** → `include_in_rag: true`
4. **Test in Chat** → Verify it appears in answers

## Combined Updates

You can update multiple properties at once:

**Via API:**
\`\`\`bash
curl -X PATCH http://localhost:8000/capsules/01HZ... \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["final", "tags", "set"],
    "status": "active",
    "include_in_rag": true
  }'
\`\`\`

**Use Cases:**
- Bulk organization
- Complete capsule setup
- Status transitions
- Quality improvements

## Organization Strategies

### Strategy 1: Tag-Based Organization

**Approach:**
- Use consistent tag conventions
- Group related content with same tags
- Use hierarchical tags (e.g., `ml-basics`, `ml-advanced`)

**Example:**
- All ML content: `machine-learning`
- Basics: `machine-learning`, `basics`
- Advanced: `machine-learning`, `advanced`

### Strategy 2: Status-Based Workflow

**Approach:**
- Upload → Draft
- Review → Active
- Outdated → Archived

**Benefits:**
- Clear lifecycle
- Quality control
- Easy cleanup

### Strategy 3: RAG-Based Organization

**Approach:**
- Public knowledge → Include in RAG
- Private notes → Exclude from RAG
- Test content → Exclude from RAG

**Benefits:**
- Privacy control
- Quality filtering
- Focused queries

## Audit Trail

All changes are logged:

- **RAG Toggles**: When `include_in_rag` changes
- **Status Changes**: When status updates
- **Tag Updates**: When tags are modified

**Audit Log Includes:**
- Timestamp
- Action type
- Old value
- New value
- Actor (user/system)

**Access:**
- Via database query (if implemented)
- For compliance and tracking
- Debugging changes

## Best Practices

### Tag Management

1. **Consistency**: Use same tag names across capsules
2. **Descriptive**: Tags should clearly describe content
3. **Appropriate Count**: 3-10 tags per capsule
4. **No PII**: Never include personal information
5. **Lowercase**: Use lowercase with hyphens

### Status Management

1. **Review Drafts**: Check draft capsules regularly
2. **Activate Quality**: Only activate complete, quality content
3. **Archive Old**: Archive outdated content
4. **Monitor Status**: Track capsule lifecycle

### RAG Inclusion

1. **Include Quality**: Only include complete, relevant content
2. **Exclude Private**: Keep personal notes excluded
3. **Test First**: Test with RAG excluded, then enable
4. **Review Regularly**: Periodically review inclusion status

### Organization

1. **Start Simple**: Begin with basic organization
2. **Iterate**: Refine organization over time
3. **Be Consistent**: Use consistent patterns
4. **Document**: Document your organization strategy

## Example Workflows

### Workflow 1: Content Review

1. Upload content → Status: "draft"
2. Review capsule → Check summary, keywords, tags
3. Fix issues → Update tags if needed
4. Activate → Change status to "active"
5. Enable RAG → Set `include_in_rag: true`

### Workflow 2: Tag Standardization

1. Review existing tags → Identify inconsistencies
2. Define standards → Create tag conventions
3. Update capsules → Batch update tags
4. Verify → Check tag consistency
5. Maintain → Use standards for new content

### Workflow 3: Content Cleanup

1. Identify outdated → Find old/irrelevant content
2. Archive → Change status to "archived"
3. Exclude RAG → Set `include_in_rag: false`
4. Document → Note why archived
5. Review → Periodically review archived content

## Troubleshooting

### Tags Not Updating

**Problem:** Tag update fails

**Solutions:**
- Check tag count (3-10 required)
- Verify no PII in tags
- Ensure tags are lowercase
- Check for validation errors

### Status Not Changing

**Problem:** Status update doesn't work

**Solutions:**
- Verify valid status value
- Check capsule exists
- Review error messages
- Try individual update

### RAG Toggle Not Working

**Problem:** RAG inclusion not updating

**Solutions:**
- Verify boolean value
- Check capsule exists
- Review audit logs
- Test with simple update

## Summary

Effective capsule management involves:
1. **Consistent Tagging**: Use standardized tag conventions
2. **Status Workflow**: Draft → Active → Archived
3. **RAG Control**: Include quality, exclude private
4. **Regular Review**: Periodically organize and clean up
5. **Audit Awareness**: Track changes for compliance

Organize your capsules to maximize the value of your knowledge base!
