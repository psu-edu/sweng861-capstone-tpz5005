
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CheckoutPage from './CheckoutPage';

describe('CheckoutPage', () => {
  const mockSetUser = jest.fn();
  const mockSetReservationInfo = jest.fn();

  const mockReservations = [
    {
      item: 'The Hobbit',
      item_type: 'book',
      reservation_id: 42,
      reserve_start: '2026-10-04T14:00:00.000Z',
      reserve_end: '2026-10-04T16:00:00.000Z'
    },
    {
      item: 'Canon EOS R50',
      item_type: 'Canon Camera',
      reservation_id: 43,
      reserve_start: '2026-10-05T10:00:00.000Z',
      reserve_end: '2026-10-05T12:00:00.000Z'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // =============================================================/
  // 1) Check the reservation etails table
  // =============================================================/
  test('displays reservation details in the checkout table', () => {
    render(
      <CheckoutPage
        user={{ user: 'student@example.com' }}
        setUser={mockSetUser}
        reservationInfo={mockReservations}
        setReservationInfo={mockSetReservationInfo}
      />
    );

    expect(screen.getByText('Checkout Cart')).toBeInTheDocument();
    expect(screen.getByText('The Hobbit')).toBeInTheDocument();
    expect(screen.getByText('Canon EOS R50')).toBeInTheDocument();

    expect(screen.getByText('book')).toBeInTheDocument();
    expect(screen.getByText('Canon Camera')).toBeInTheDocument();

    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('43')).toBeInTheDocument();

    expect(screen.getByText('Oct 4, 2026 10:00 AM')).toBeInTheDocument();
    expect(screen.getByText('Oct 4, 2026 12:00 PM')).toBeInTheDocument();

    expect(
      screen.getByRole('button', { name: 'Checkout Items' })
    ).toBeEnabled();
  });


  // =============================================================/
  // 2) Click checkout button and clear table on OK
  // =============================================================/
  test('opens checkout confirmation and clears reservations on OK', async () => {
    render(
      <CheckoutPage
        user={{ user: 'student@example.com' }}
        setUser={mockSetUser}
        reservationInfo={mockReservations}
        setReservationInfo={mockSetReservationInfo}
      />
    );

    // Open the checkout confirmation dialog.
    fireEvent.click(
      screen.getByRole('button', { name: 'Checkout Items' })
    );

    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(
      screen.getByText('Items successfully checked out!')
    ).toBeInTheDocument();

    // Confirm checkout.
    fireEvent.click(screen.getByRole('button', { name: 'OK' }));

    await waitFor(() => {
      expect(mockSetReservationInfo).toHaveBeenCalledWith([]);
    });
  });
});