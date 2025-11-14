import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

import HomePage from "@/app/page";

function renderHome() {
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <HomePage />
    </QueryClientProvider>
  );
}

describe("HomePage", () => {
  it("renders the hero copy", () => {
    renderHome();
    expect(screen.getByText(/Anything -> Capsules -> Graph -> Chat/i)).toBeInTheDocument();
  });

  it("shows the upload form inputs", () => {
    renderHome();
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Material/i)).toBeInTheDocument();
  });
});
