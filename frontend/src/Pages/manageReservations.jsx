import React, { useEffect, useState } from 'react';
import { styles } from '../styles';
import { apiClient } from '../apiClient';

import { 
    Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, TextField, Paper, Snackbar, Alert , Dialog, DialogActions, DialogContent, DialogTitle
} from '@mui/material';

import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';

/***********************************************/
export default function ManageReservationsPage({ user, 
                                                 setUser, 
                                                 role}) {
/***********************************************/
    // User login data & Notification states
    const [userData, setUserData] = useState(null);
    const [errorMsg, setErrorMsg] = useState('');
    const [notification, setNotification] = useState('');

    const [reservations, setReservations] = useState(null)
                                                
    //For checkout popup
    const [popupOpen, setPopupOpen] = useState(false);
    const [popupMessage, setPopupMessage] = useState('');

    // Initiate upon launch
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        // If there is no user, do not alloow them to access library
        if(!user) return;

        const fetchReservations = async () => {
            try {
                //Get the reservations from the database
                const response = await apiClient('/api/psu/bookstore/reservations', {
                    method: 'GET'
                });
                
                console.log("reserv resp: ", response);
                //Set the reservations into the table
                setReservations(response.reservations);

            } catch (error) {
                console.error('Error fetching reservations:', error);
                setErrorMsg(`Error fetching reservations: ${error.message}`);
            }   
        }

        fetchReservations();
    }, [user]);


    //------------------------------------------/
    const handleRevoke = async (evnt) => {
    //------------------------------------------/
        // Make sure we cant open a popup window if there
        // is no reserved items
        if(reservations.length > 0) {
            const message = "Are you certain you want to revoke reservations?"
            setPopupMessage(message);
            setPopupOpen(true);
        }
    };

    //------------------------------------------/
    const handlePopupClose = async (evnt) => {
    //------------------------------------------/
        //Close the popup
        setPopupOpen(false)

        // Now that we have checked out, clear the table
        setReservations([]);
    };

    /////////////////////////////////////////////////////////////////

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Box sx={{ display: 'flex', minHeight: '80vh' }}>
                <Box component="main" sx={{ flexGrow: 1, p: 3, mt: '64px', minWidth: 0 }}>
                    {/* Main Title */}   
                    {/*-----------------------------------------------------------*/} 
                    <Typography variant="h4" sx={{ mb: 1 }}>
                        Current Reservations
                    </Typography>
                    {/*-----------------------------------------------------------*/}

                    <Typography color="text.secondary" sx={{ mb: 3 }}>
                        All current reservations.
                    </Typography>

                    {/* Reservation Inventory Table */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                        <Table>
                            {/* Table Headers */}
                            {/*-------------------------------------------------------*/}
                            <TableHead>
                                <TableRow>
                                    <TableCell>Reservation ID</TableCell>
                                    <TableCell>Book ID</TableCell>
                                    <TableCell>Reserved By</TableCell>
                                    <TableCell>Start Time</TableCell>
                                    <TableCell>End Time</TableCell>
                                </TableRow>
                            </TableHead>
                            {/*-------------------------------------------------------*/}

                            {/* Table Rows */}
                            {/*-------------------------------------------------------*/}
                            <TableBody>
                                {/* Check if there are items to display */}
                                {(!reservations || reservations.length === 0) ? (
                                    <TableRow>
                                        <TableCell colSpan={5} align="center">
                                            There are currently no book reservations.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    /* Map over the reservationInfo array */
                                    reservations.map((row, index) => (
                                        <TableRow key={row.reservation_id || index} hover>
                                            <TableCell sx={{ textTransform: 'capitalize' }}>
                                                {row.id}
                                            </TableCell>
                                            <TableCell>{row.book_id}</TableCell>
                                            <TableCell>{row.reserved_by}</TableCell>
                                            <TableCell>
                                                {dayjs(row.reserve_start).format('MMM D, YYYY h:mm A')}
                                            </TableCell>
                                            <TableCell>
                                                {dayjs(row.reserve_end).format('MMM D, YYYY h:mm A')}
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                            {/*-------------------------------------------------------*/}
                        </Table>
                    </TableContainer>

                    {/* Revoke Button Area */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        
                        {/* Revoke Button */}
                        {/*-----------------------------------------------------------*/}
                        <Button 
                            variant="contained" 
                            size="large"
                            onClick={handleRevoke}
                            disabled={!reservations || reservations.length === 0}
                        >
                            Revoke Reservations
                        </Button>
                        {/*-----------------------------------------------------------*/}
                    </Box>

                    {/* Success Notification */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Snackbar
                        open={Boolean(notification)}
                        autoHideDuration={4000}
                        onClose={() => setNotification('')}
                    >
                        <Alert severity="success" onClose={() => setNotification('')}>
                            {notification}
                        </Alert>
                    </Snackbar>
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}


                    {/* Error Notification */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Snackbar
                        open={Boolean(errorMsg)}
                        autoHideDuration={4000}
                        onClose={() => setErrorMsg('')}
                    >
                        <Alert severity="error" onClose={() => setErrorMsg('')}>
                            {errorMsg}
                        </Alert>
                    </Snackbar>
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                </Box>

                {/* Checkout Popup window */}
                {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                <Dialog
                    open={popupOpen}
                    onClose={() => setPopupOpen(false)}
                >
                    {/* Popup title */}
                    {/*---------------------------------------------------------------*/}
                    <DialogTitle>
                        You are about to revoke Reservations!
                    </DialogTitle>
                    {/*---------------------------------------------------------------*/}

                    <DialogContent>
                        {/* Message */}
                        {/*-----------------------------------------------------------*/}
                        <Typography>
                            {popupMessage}
                        </Typography>
                        {/*-----------------------------------------------------------*/}
                    </DialogContent>

                    <DialogActions>
                        {/* Button Action */}
                        {/*-----------------------------------------------------------*/}
                        <Button onClick={() => handlePopupClose()}>
                            OK
                        </Button>
                        {/*-----------------------------------------------------------*/}
                    </DialogActions>
                </Dialog>
                {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
            </Box>
        </LocalizationProvider>
    );
}