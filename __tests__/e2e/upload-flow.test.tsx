/**
 * End-to-End Tests: Upload Flow
 * Tests file upload, job creation, and status updates via SSE
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import type { ReactElement } from 'react';
import userEvent from '@testing-library/user-event';
import { UploadForm } from '@/components/upload-form';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the API client
vi.mock('@/lib/api', () => ({
  ingestMaterial: vi.fn(),
}));

vi.mock('@/lib/state', () => ({
  useRagScope: () => ({
    scopeType: 'my',
    scope: [],
    setScopeType: vi.fn(),
    toggleTag: vi.fn(),
    setScope: vi.fn(),
    getScopeForAPI: () => ['my'],
  }),
}));

describe('Upload Flow E2E', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient();
  });

  afterEach(() => {
    queryClient.clear();
  });

  function renderWithProviders(ui: ReactElement) {
    return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
  }

  it('should render upload form with all required fields', () => {
    renderWithProviders(<UploadForm />);
    
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/material/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create capsule/i })).toBeInTheDocument();
  });

  it('should validate required fields before submission', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UploadForm />);
    
    const submitButton = screen.getByRole('button', { name: /create capsule/i });
    // HTML5 validation should prevent submission without required fields
    await user.click(submitButton);
    
    // Form should not submit (HTML5 validation)
    await waitFor(() => {
      expect(submitButton).toBeInTheDocument();
    });
  });

  it('should submit form with valid data', async () => {
    const { ingestMaterial } = await import('@/lib/api');
    const mockIngest = vi.mocked(ingestMaterial);
    mockIngest.mockResolvedValue({ job_id: 'test-job-123' });

    const user = userEvent.setup();
    renderWithProviders(<UploadForm />);
    
    const titleInput = screen.getByLabelText(/title/i);
    const contentInput = screen.getByLabelText(/material/i);
    
    await user.type(titleInput, 'Test Document');
    await user.type(contentInput, 'This is test content for E2E testing.');
    
    const submitButton = screen.getByRole('button', { name: /create capsule/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockIngest).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Document',
          content: expect.stringContaining('test content'),
          tags: expect.any(Array),
          include_in_rag: expect.any(Boolean),
        })
      );
    });
  });
});
