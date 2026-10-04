import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import LibraryPage from './LibraryPage';
import { apiClient } from '../apiClient';

jest.mock('../apiClient', () => ({
  apiClient: jest.fn()
}));



// =================================================================/
// Set up UI test
// =================================================================/
describe('LibraryPage', () => {
  const mockUser = { user: 'student@example.com' };
  const mockSetUser = jest.fn();
  const mockSetReservationInfo = jest.fn();

  const mockBooks = [
    {
      id: 1,
      title: 'The Hobbit',
      genre: 'Fantasy',
      copies: 3,
      available_copies: 2
    },
    {
      id: 2,
      title: 'Dune',
      genre: 'Sci-Fi',
      copies: 2,
      available_copies: 1
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });


  // =============================================================/
  // 1) Get book information
  // =============================================================/
  //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
  test('fetches and displays books from the backend', async () => {
  //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    apiClient.mockResolvedValueOnce({
      available_books: mockBooks
    });

    //Render the page
    render(
      <LibraryPage
        user={mockUser}
        setUser={mockSetUser}
        reservationInfo={[]}
        setReservationInfo={mockSetReservationInfo}
      />
    );

    // If the information has been fetched from the back, we should see 'the hobbit' in
    // the top row
    expect(
      await screen.findByText('The Hobbit')
    ).toBeInTheDocument();

    expect(screen.getByText('Dune')).toBeInTheDocument();
    expect(screen.getByText('2 available')).toBeInTheDocument();
    expect(apiClient).toHaveBeenCalledWith(
      '/api/psu/bookstore/books',
      { method: 'GET' }
    );
  });


  // =============================================================/
  // 2) Get Price and IDs when user is valid
  // =============================================================/
  //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
  test('successfully reserves a book and adds it to reservation info', async () => {
  //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    apiClient
      .mockResolvedValueOnce({
        available_books: mockBooks
      })
      .mockResolvedValueOnce({
        status: 'success',
        reservation_id: 42,
        updated_available_books: [
          { ...mockBooks[0], available_copies: 1 },
          mockBooks[1]
        ]
      });
    
    //Render the page
    render(
      <LibraryPage
        user={mockUser}
        setUser={mockSetUser}
        reservationInfo={[]}
        setReservationInfo={mockSetReservationInfo}
      />
    );

    // Wait for the books to load, then open the reservation dialog.
    const reserveButtons = await screen.findAllByRole('button', {
      name: 'Reserve'
    });
    fireEvent.click(reserveButtons[0]);
    
    expect(
      screen.getByText('Reserve The Hobbit')
    ).toBeInTheDocument();

    // Confirm using the component's default valid start/end times.
    fireEvent.click(
      screen.getByRole('button', { name: 'Confirm Reservation' })
    );

    await waitFor(() => {
      expect(apiClient).toHaveBeenCalledWith(
        '/api/psu/bookstore/reserve_book',
        expect.objectContaining({ method: 'PUT' })
      );
      expect(mockSetReservationInfo).toHaveBeenCalledTimes(1);
    });

    // Execute the functional state update and inspect the resulting list.
    const updateReservations = mockSetReservationInfo.mock.calls[0][0];
    const updatedReservations = updateReservations([]);
    
    expect(updatedReservations).toHaveLength(1);
    expect(updatedReservations[0]).toEqual(
      expect.objectContaining({
        item_type: 'book',
        item: 'The Hobbit',
        reservation_id: 42
      })
    );
  });
});