/**
 * End-to-End Tests: Chat Panel
 * Tests chat interactions with different RAG-Scope profiles
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatPanel } from '@/components/chat-panel';

// Mock the API client
vi.mock('@/lib/api', () => ({
  runChat: vi.fn(),
}));

const mockGetScopeForAPI = vi.fn(() => ['my']);

vi.mock('@/lib/state', () => ({
  useRagScope: () => ({
    scopeType: 'my',
    scope: [],
    setScopeType: vi.fn(),
    toggleTag: vi.fn(),
    setScope: vi.fn(),
    getScopeForAPI: mockGetScopeForAPI,
  }),
}));

describe('Chat Panel E2E', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetScopeForAPI.mockReturnValue(['my']);
  });

  it('should render chat input and send button', () => {
    render(<ChatPanel />);
    
    expect(screen.getByPlaceholderText(/ask grounded questions/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ask/i })).toBeInTheDocument();
  });

  it('should send chat query with correct scope', async () => {
    const { runChat } = await import('../../lib/api');
    const mockRunChat = vi.mocked(runChat);
    mockRunChat.mockResolvedValue({
      answer: 'Test answer',
      sources: ['capsule-1', 'capsule-2'],
      metrics: { retrieval_recall: 0.9 },
    });

    const user = userEvent.setup();
    render(<ChatPanel />);
    
    const input = screen.getByPlaceholderText(/ask grounded questions/i);
    const sendButton = screen.getByRole('button', { name: /ask/i });
    
    await user.type(input, 'What is machine learning?');
    await user.click(sendButton);
    
    await waitFor(() => {
      expect(mockRunChat).toHaveBeenCalledWith({
        query: 'What is machine learning?',
        scope: ['my'],
      });
    });
  });

  it('should display chat messages after sending', async () => {
    const { runChat } = await import('../../lib/api');
    const mockRunChat = vi.mocked(runChat);
    mockRunChat.mockResolvedValue({
      answer: 'Machine learning is a subset of AI.',
      sources: ['capsule-1'],
      metrics: { retrieval_recall: 0.85 },
    });

    const user = userEvent.setup();
    render(<ChatPanel />);
    
    const input = screen.getByPlaceholderText(/ask grounded questions/i);
    const sendButton = screen.getByRole('button', { name: /ask/i });
    
    await user.type(input, 'What is machine learning?');
    await user.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText(/machine learning is a subset/i)).toBeInTheDocument();
    });
  });

  it('should display sources and metrics when available', async () => {
    const { runChat } = await import('../../lib/api');
    const mockRunChat = vi.mocked(runChat);
    mockRunChat.mockResolvedValue({
      answer: 'Test answer',
      sources: ['capsule-1', 'capsule-2'],
      metrics: {
        retrieval_recall: 0.9,
        faithfulness: 0.95,
        citation_share: 0.8,
      },
    });

    const user = userEvent.setup();
    render(<ChatPanel />);
    
    const input = screen.getByPlaceholderText(/ask grounded questions/i);
    const sendButton = screen.getByRole('button', { name: /ask/i });
    
    await user.type(input, 'Test query');
    await user.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText(/sources:/i)).toBeInTheDocument();
      expect(screen.getByText(/capsule-1/i)).toBeInTheDocument();
    });
  });

  it('should handle errors gracefully', async () => {
    const { runChat } = await import('../../lib/api');
    const mockRunChat = vi.mocked(runChat);
    mockRunChat.mockRejectedValue(new Error('Network error'));

    const user = userEvent.setup();
    render(<ChatPanel />);
    
    const input = screen.getByPlaceholderText(/ask grounded questions/i);
    const sendButton = screen.getByRole('button', { name: /ask/i });
    
    await user.type(input, 'Test query');
    await user.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText(/chat error/i)).toBeInTheDocument();
    });
  });
});
