/**
 * Card Component Tests
 * Unit tests for the Card UI component
 * 
 * Tests:
 * - Render compound components
 * - Props forwarding
 * - Custom className
 * - Content rendering
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../card';

describe('Card Component', () => {
  it('should render card with all compound components', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card Description</CardDescription>
        </CardHeader>
        <CardContent>Card Content</CardContent>
        <CardFooter>Card Footer</CardFooter>
      </Card>
    );
    
    expect(screen.getByText(/card title/i)).toBeInTheDocument();
    expect(screen.getByText(/card description/i)).toBeInTheDocument();
    expect(screen.getByText(/card content/i)).toBeInTheDocument();
    expect(screen.getByText(/card footer/i)).toBeInTheDocument();
  });

  it('should render card with only title and content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Simple Card</CardTitle>
        </CardHeader>
        <CardContent>Simple content</CardContent>
      </Card>
    );
    
    expect(screen.getByText(/simple card/i)).toBeInTheDocument();
    expect(screen.getByText(/simple content/i)).toBeInTheDocument();
  });

  it('should accept custom className on Card', () => {
    render(
      <Card className="custom-card">
        <CardContent>Content</CardContent>
      </Card>
    );
    
    const card = screen.getByText(/content/i).parentElement;
    expect(card).toHaveClass('custom-card');
  });

  it('should accept custom className on CardHeader', () => {
    render(
      <Card>
        <CardHeader className="custom-header">
          <CardTitle>Title</CardTitle>
        </CardHeader>
      </Card>
    );
    
    const header = screen.getByText(/title/i).parentElement;
    expect(header).toHaveClass('custom-header');
  });

  it('should accept custom className on CardContent', () => {
    render(
      <Card>
        <CardContent className="custom-content">Content</CardContent>
      </Card>
    );
    
    const content = screen.getByText(/content/i);
    expect(content).toHaveClass('custom-content');
  });

  it('should accept custom className on CardFooter', () => {
    render(
      <Card>
        <CardFooter className="custom-footer">Footer</CardFooter>
      </Card>
    );
    
    const footer = screen.getByText(/footer/i);
    expect(footer).toHaveClass('custom-footer');
  });

  it('should render without header', () => {
    render(
      <Card>
        <CardContent>Direct content</CardContent>
        <CardFooter>Direct footer</CardFooter>
      </Card>
    );
    
    expect(screen.getByText(/direct content/i)).toBeInTheDocument();
    expect(screen.getByText(/direct footer/i)).toBeInTheDocument();
  });

  it('should render complex content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>User Profile</CardTitle>
          <CardDescription>Manage your profile information</CardDescription>
        </CardHeader>
        <CardContent>
          <div data-testid="form">
            <input type="text" placeholder="Name" />
            <input type="email" placeholder="Email" />
          </div>
        </CardContent>
        <CardFooter>
          <button>Save Changes</button>
        </CardFooter>
      </Card>
    );
    
    expect(screen.getByText(/user profile/i)).toBeInTheDocument();
    expect(screen.getByTestId('form')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/name/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
  });

  it('should render CardTitle with correct heading level', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
        </CardHeader>
      </Card>
    );
    
    // CardTitle renders as h3 by default
    const title = screen.getByText(/title/i);
    expect(title.tagName).toBe('H3');
  });

  it('should render CardDescription with correct text styling', () => {
    render(
      <Card>
        <CardHeader>
          <CardDescription>Description text</CardDescription>
        </CardHeader>
      </Card>
    );
    
    const description = screen.getByText(/description text/i);
    expect(description).toHaveClass('text-sm', 'text-muted-foreground');
  });
});

