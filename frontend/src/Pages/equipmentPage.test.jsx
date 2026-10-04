
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import EquipmentPage from './EquipmentPage';
import { apiClient } from '../apiClient';

jest.mock('../apiClient', () => ({
  apiClient: jest.fn()
}));

describe('EquipmentPage', () => {
  const mockUser = { user: 'student@example.com' };
  const mockSetUser = jest.fn();
  const mockSetReservationInfo = jest.fn();

  const mockEquipment = [
    {
      id: 1,
      name: 'Canon Camera',
      type: 'Camera',
      manufacturer: 'Canon',
      model: 'EOS R50',
      copies: 3,
      available_copies: 2
    },
    {
      id: 2,
      name: 'Dell Laptop',
      type: 'Laptop',
      manufacturer: 'Dell',
      model: 'Latitude 5450',
      copies: 2,
      available_copies: 1
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });


  // =============================================================/
  // 1) Populate the table with equipment
  // =============================================================/
  test('fetches and displays equipment from the backend', async () => {
    apiClient.mockResolvedValueOnce({
      available_equipment: mockEquipment
    });

    render(
      <EquipmentPage
        user={mockUser}
        setUser={mockSetUser}
        reservationInfo={[]}
        setReservationInfo={mockSetReservationInfo}
      />
    );

    expect(
      await screen.findByText('Canon Camera')
    ).toBeInTheDocument();

    expect(screen.getByText('Dell Laptop')).toBeInTheDocument();
    expect(screen.getByText('Camera')).toBeInTheDocument();
    expect(screen.getByText('2 available')).toBeInTheDocument();

    expect(apiClient).toHaveBeenCalledWith(
      '/api/psu/bookstore/equipment',
      { method: 'GET' }
    );
  });


  // =============================================================/
  // 2) Reserve some equipment
  // =============================================================/
  test('successfully reserves equipment and adds it to reservation info', async () => {
    apiClient
      .mockResolvedValueOnce({
        available_equipment: mockEquipment
      })
      .mockResolvedValueOnce({
        status: 'success',
        reservation_id: 42,
        updated_available_equipment: [
          { ...mockEquipment[0], available_copies: 1 },
          mockEquipment[1]
        ]
      });

    render(
      <EquipmentPage
        user={mockUser}
        setUser={mockSetUser}
        reservationInfo={[]}
        setReservationInfo={mockSetReservationInfo}
      />
    );

    // Wait for the equipment to load.
    const reserveButtons = await screen.findAllByRole('button', {
      name: 'Reserve'
    });

    // Open the reservation dialog for the first item.
    fireEvent.click(reserveButtons[0]);

    expect(
      screen.getByText('Reserve Canon Camera')
    ).toBeInTheDocument();

    // Confirm using the default valid reservation times.
    fireEvent.click(
      screen.getByRole('button', { name: 'Confirm Reservation' })
    );

    await waitFor(() => {
      expect(apiClient).toHaveBeenCalledWith(
        '/api/psu/bookstore/reserve_equipment',
        expect.objectContaining({
          method: 'PUT',
          body: expect.any(String)
        })
      );

      expect(mockSetReservationInfo).toHaveBeenCalledTimes(1);
    });

    // Verify the data sent to the backend.
    const reservationCall = apiClient.mock.calls[1];
    const payload = JSON.parse(reservationCall[1].body);

    expect(payload.equipment_id).toBe(1);
    expect(payload.reservation_id).toBe('student@example.com');
    expect(payload.reserve_Start).toBeTruthy();
    expect(payload.reserve_End).toBeTruthy();

    // Evaluate the functional state update to inspect the new reservation.
    const updateReservations = mockSetReservationInfo.mock.calls[0][0];
    const updatedReservations = updateReservations([]);

    expect(updatedReservations).toHaveLength(1);
    expect(updatedReservations[0]).toEqual(
      expect.objectContaining({
        item_type: 'Canon Camera',
        item: 'EOS R50',
        reservation_id: 42
      })
    );

    expect(
      await screen.findByText(
        'Reservation request for Canon Camera is ready.'
      )
    ).toBeInTheDocument();
  });
});