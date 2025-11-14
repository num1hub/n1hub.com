## Description

<!-- Provide a clear and concise description of your changes -->

## Related Issues

<!-- Link related issues using keywords: Closes #123, Fixes #456, Relates to #789 -->

Closes #

## Type of Change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test additions or improvements

## Affected Components

<!-- Check all that apply -->

- [ ] Frontend (`app/`)
- [ ] Backend (`apps/engine`)
- [ ] Database schema (`infra/sql`)
- [ ] API endpoints
- [ ] Documentation
- [ ] CI/CD
- [ ] Configuration

## Changes Made

<!-- Provide a detailed list of changes -->

- 
- 
- 

## Testing

### Test Coverage

<!-- Describe the tests you added or updated -->

- [ ] Added unit tests
- [ ] Added integration tests
- [ ] Added E2E tests
- [ ] Updated existing tests
- [ ] No tests required (explain why)

### Test Results

<details>
<summary>Backend Tests</summary>

\`\`\`bash
# Paste pytest output
\`\`\`

</details>

<details>
<summary>Frontend Tests</summary>

\`\`\`bash
# Paste vitest output
\`\`\`

</details>

### Manual Testing

<!-- Describe how you manually tested your changes -->

- [ ] Tested locally with `npm run dev:stack:unix` + `npm run dev:interface`
- [ ] Tested on development deployment
- [ ] Tested edge cases
- [ ] Verified no regressions in related features

**Test Scenarios:**

1. 
2. 
3. 

## Screenshots / Demo

<!-- If applicable, add screenshots or a demo video -->

**Before:**


**After:**


## Documentation Updates

<!-- Check all that apply -->

- [ ] Updated README.md
- [ ] Updated docs/api-reference.md
- [ ] Updated docs/deployment.md
- [ ] Updated code comments
- [ ] Added JSDoc/docstrings
- [ ] No documentation updates required

## Breaking Changes

<!-- If this PR introduces breaking changes, describe them and migration steps -->

- [ ] No breaking changes
- [ ] Breaking changes (describe below)

**Migration Guide:**


## Performance Impact

<!-- Describe any performance implications -->

- [ ] No performance impact
- [ ] Improves performance (describe below)
- [ ] May impact performance (describe below)

## Security Considerations

<!-- Describe any security implications -->

- [ ] No security implications
- [ ] Enhances security (describe below)
- [ ] Potential security concerns (describe below)

## Deployment Notes

<!-- Any special deployment instructions or environment variable changes -->

- [ ] No deployment changes required
- [ ] Requires environment variable updates (list below)
- [ ] Requires database migration (migration file: `infra/sql/XXXX_*.sql`)
- [ ] Requires Redis cache flush
- [ ] Other deployment considerations (describe below)

**Environment Variables:**


## Checklist

<!-- Ensure all items are checked before requesting review -->

- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
- [ ] I have checked my code and corrected any misspellings
- [ ] I have run `npm run lint` and fixed all issues
- [ ] I have run `python scripts/validate_env.py` successfully
- [ ] I have updated CHANGELOG.md (if applicable)

## Additional Notes

<!-- Any additional information for reviewers -->

## Reviewer Guidance

<!-- Optional: Guide reviewers on what to focus on -->

**Focus Areas:**


**Known Limitations:**


---

**By submitting this pull request, I confirm that my contribution is made under the terms of the MIT License.**
