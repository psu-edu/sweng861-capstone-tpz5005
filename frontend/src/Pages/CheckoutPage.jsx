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
export default function CheckoutPage({ user, 
                                       setUser, 
                                       reservationInfo, 
                                       setReservationInfo }) {
/***********************************************/
    // User login data & Notification states
    const [userData, setUserData] = useState(null);
    const [errorMsg, setErrorMsg] = useState('');
    const [notification, setNotification] = useState('');

    //For checkout popup
    const [popupOpen, setPopupOpen] = useState(false);
    const [popupMessage, setPopupMessage] = useState('');

    //Email Reciept
    const [email, setEmail] = useState('');


    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        console.log("reservation Info: ", reservationInfo)
    }, [reservationInfo]);


    //------------------------------------------/
    const handleReserveItems = async (evnt) => {
    //------------------------------------------/
        // Make sure we cant open a popup window if there
        // is no reserved items
        if(reservationInfo.length > 0) {
            const message = "Please click 'Ok' to check out your items."
            setPopupMessage(message);
            setPopupOpen(true);

            
        }
    };

    //------------------------------------------/
    const handlePopupClose = async (evnt) => {
    //------------------------------------------/
        //Send a notification to user if email provided
        console.log("email: ", email);
        console.log("reservationinfo: ", reservationInfo);

        // If an email was provided, attempt to send a message
        if(email !== '') {
            //Assemble a payload of information
            const payload = { reservation_items: reservationInfo,
                              email_Addr: email };
            
            try {
                const data = await apiClient(`/api/psu/bookstore/email_receipt`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                });
                
                // Clear the email input for the next time the popup opens
                setEmail('');

            } catch (error) {
                setErrorMsg(`Could not email receipt: ${error}`);
            }                
        }

        //Close the popup
        setPopupOpen(false)

        // Now that we have checked out, clear the table
        setReservationInfo([]);
    };

    /////////////////////////////////////////////////////////////////

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Box sx={{ display: 'flex', minHeight: '80vh' }}>
                <Box component="main" sx={{ flexGrow: 1, p: 3, mt: '64px', minWidth: 0 }}>
                    {/* Main Title */}   
                    {/*-----------------------------------------------------------*/} 
                    <Typography variant="h4" sx={{ mb: 1 }}>
                        Checkout Cart
                    </Typography>
                    {/*-----------------------------------------------------------*/}

                    <Typography color="text.secondary" sx={{ mb: 3 }}>
                        Review your pending reservations before completing your checkout.
                    </Typography>

                    {/* Checkout Inventory Table */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                        <Table>
                            {/* Table Headers */}
                            {/*-------------------------------------------------------*/}
                            <TableHead>
                                <TableRow>
                                    <TableCell>Item Type</TableCell>
                                    <TableCell>Item Details</TableCell>
                                    <TableCell>Reservation ID</TableCell>
                                    <TableCell>Start Time</TableCell>
                                    <TableCell>End Time</TableCell>
                                </TableRow>
                            </TableHead>
                            {/*-------------------------------------------------------*/}

                            {/* Table Rows */}
                            {/*-------------------------------------------------------*/}
                            <TableBody>
                                {/* Check if there are items to display */}
                                {(!reservationInfo || reservationInfo.length === 0) ? (
                                    <TableRow>
                                        <TableCell colSpan={5} align="center">
                                            Your cart is empty. No items to checkout.
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    /* Map over the reservationInfo array */
                                    reservationInfo.map((row, index) => (
                                        <TableRow key={row.reservation_id || index} hover>
                                            <TableCell sx={{ textTransform: 'capitalize' }}>
                                                {row.item_type}
                                            </TableCell>
                                            <TableCell>{row.item}</TableCell>
                                            <TableCell>{row.reservation_id}</TableCell>
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

                    {/* Checkout Button Area */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        
                        {/* Checkout Button */}
                        {/*-----------------------------------------------------------*/}
                        <Button 
                            variant="contained" 
                            size="large"
                            onClick={handleReserveItems}
                            disabled={!reservationInfo || reservationInfo.length === 0}
                        >
                            Checkout Items
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
                        Your Items are ready!
                    </DialogTitle>
                    {/*---------------------------------------------------------------*/}

                    <DialogContent>
        
                        {/* Message */}
                        {/*-----------------------------------------------------------*/}
                        <Typography>
                            {popupMessage}
                        </Typography>
                        {/*-----------------------------------------------------------*/}
                        
                        {/* Email Feature */}
                        {/*-----------------------------------------------------------*/}
                        <Typography sx={{ mt: 3, mb: 1 }} color="text.secondary">
                            Email Receipt (Optional)
                        </Typography>
                        <TextField
                            label="Email Address"
                            type="email"
                            placeholder="student@psu.edu"
                            fullWidth
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            size="small"
                        />
                        {/*-----------------------------------------------------------*/}
                    </DialogContent>

                    <DialogActions>
                        <Button onClick={() => handlePopupClose()}>
                            OK
                        </Button>
                    </DialogActions>
                </Dialog>
                {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
            </Box>
        </LocalizationProvider>
    );
}