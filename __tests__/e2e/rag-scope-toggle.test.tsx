/**
 * End-to-End Tests: RAG-Scope Toggle Interactions
 * Tests RAG-Scope profile selection and tag filtering
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RagScopeToggle } from '@/components/rag-scope-toggle';

// Mock the state hook
const {
  mockSetScopeType,
  mockToggleTag,
  mockSetScope,
  mockGetScopeForAPI,
  mockUseRagScope,
} = vi.hoisted(() => {
  const mockSetScopeType = vi.fn();
  const mockToggleTag = vi.fn();
  const mockSetScope = vi.fn();
  const mockGetScopeForAPI = vi.fn(() => ['my']);
  const mockUseRagScope = vi.fn(() => ({
    scopeType: 'my',
    scope: [] as string[],
    setScopeType: mockSetScopeType,
    toggleTag: mockToggleTag,
    setScope: mockSetScope,
    getScopeForAPI: mockGetScopeForAPI,
  }));

  return {
    mockSetScopeType,
    mockToggleTag,
    mockSetScope,
    mockGetScopeForAPI,
    mockUseRagScope,
  };
});

vi.mock('@/lib/state', () => ({
  useRagScope: mockUseRagScope,
}));

describe('RAG-Scope Toggle E2E', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetScopeForAPI.mockReturnValue(['my']);
    mockUseRagScope.mockReturnValue({
      scopeType: 'my',
      scope: [] as string[],
      setScopeType: mockSetScopeType,
      toggleTag: mockToggleTag,
      setScope: mockSetScope,
      getScopeForAPI: mockGetScopeForAPI,
    });
  });

  it('should render all scope type options', () => {
    render(<RagScopeToggle availableTags={['tag1', 'tag2']} />);
    
    expect(screen.getByText(/my capsules/i)).toBeInTheDocument();
    expect(screen.getByText(/all public/i)).toBeInTheDocument();
    expect(screen.getByText(/collection: inbox/i)).toBeInTheDocument();
    expect(screen.getByText(/tags/i)).toBeInTheDocument();
  });

  it('should switch scope type when clicking options', async () => {
    const user = userEvent.setup();
    render(<RagScopeToggle availableTags={[]} />);
    
    const publicButton = screen.getByText(/all public/i);
    await user.click(publicButton);
    
    expect(mockSetScopeType).toHaveBeenCalledWith('public');
  });

  it('should show tag selection when tags scope is selected', async () => {
    mockGetScopeForAPI.mockReturnValue(['tag1']);
    mockUseRagScope.mockReturnValue({
      scopeType: 'tags',
      scope: ['tag1'] as string[],
      setScopeType: mockSetScopeType,
      toggleTag: mockToggleTag,
      setScope: mockSetScope,
      getScopeForAPI: mockGetScopeForAPI,
    });

    render(<RagScopeToggle availableTags={['tag1', 'tag2', 'tag3']} />);
    
    // Tag buttons should be visible
    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
  });

  it('should toggle tags when clicking tag buttons', async () => {
    mockGetScopeForAPI.mockReturnValue(['tag1']);
    mockUseRagScope.mockReturnValue({
      scopeType: 'tags',
      scope: ['tag1'] as string[],
      setScopeType: mockSetScopeType,
      toggleTag: mockToggleTag,
      setScope: mockSetScope,
      getScopeForAPI: mockGetScopeForAPI,
    });

    const user = userEvent.setup();
    render(<RagScopeToggle availableTags={['tag1', 'tag2']} />);
    
    const tag2Button = screen.getByText('tag2');
    await user.click(tag2Button);
    
    expect(mockToggleTag).toHaveBeenCalledWith('tag2');
  });
});
