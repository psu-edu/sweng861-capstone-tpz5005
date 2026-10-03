import React from 'react';
import {useEffect, useState} from 'react';
import { styles } from '../styles';
import { apiClient } from '../apiClient';

import { AppBar, Toolbar, Typography, Drawer, Box, TextField,Button, Table, TableBody, TableCell, TableContainer,
         TableHead, TableRow, Paper, Chip, Select, MenuItem, FormControl, InputLabel, Dialog, DialogTitle,
         DialogContent, DialogActions, Snackbar, Alert, List, ListItemButton, ListItemIcon, ListItemText
} from '@mui/material';

import { MenuBook, Laptop, CalendarMonth, Search } from '@mui/icons-material';

import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';

const drawerWidth = 220;

const sampleEquipment = [
    { id: 1, name: 'Laptop', type: 'Technology', copies: 3, available_copies: 2 },
    { id: 2, name: 'Projector', type: 'Technology', copies: 3, available_copies: 0 },
    { id: 3, name: 'Tablet', type: 'Technology', copies: 4, available_copies: 2 },
    { id: 4, name: 'Camera', type: 'Photography', copies: 3, available_copies: 3 },
    { id: 5, name: 'Microphone', type: 'Audio', copies: 2, available_copies: 1 },
];

/***********************************************/
export default function EquipmentPage({ user, 
                                        setUser, 
                                        reservationInfo, 
                                        setReservationInfo}) {
/***********************************************/
    //User login data
    const [userData, setUserData] = useState(null);
    const [equipment, setEquipment] = useState([]);
    const [search, setSearch] = useState('');
    const [type, setType] = useState('All');
    const [selectedEquipment, setSelectedEquipment] = useState(null);
    const [reserveStart, setReserveStart] = useState(dayjs().add(1, 'hour'));
    const [reserveEnd, setReserveEnd] = useState(dayjs().add(3, 'hour'));
    const [notification, setNotification] = useState('');

    const types = ['All', ...new Set(equipment.map(item => item.type))];

    // // Initiate user login
    // //------------------------------------------/
    // useEffect(() => { 
    // //------------------------------------------/
    //     // If there is no user, do not alloow them to acess library
    //     if(!user) return;

    //     const fetchLibraryEquipment = async () => {
    //         try {
    //             //Get the equipment from the databse
    //             const response = await apiClient('/api/psu/equipment', {
    //                 method: 'GET'
    //             });
                
    //             //Set them into the Library Page
    //             setEquipment(response.available_equipment);

    //         } catch (error) {
    //             console.error('Error fetching equipment:', error);
    //         }   
    //     }

    //     fetchLibraryEquipment();
    // }, [user]);


    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        setEquipment(sampleEquipment);
    }, [user]);   
    
    //------------------------------------------/
    const filteredEquipment = equipment.filter(item => {
    //------------------------------------------/
        const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase());
        const matchesType = type === 'All' || item.type === type;
        return matchesSearch && matchesType;
    });


    //------------------------------------------/
    const handleReserve = async (evnt) => {
    //------------------------------------------/
        // In order to reserve a book we must have all 3
        if (!selectedEquipment || !reserveStart || !reserveEnd) return;

        // Validate the time window requested
        if (!reserveStart.isValid() || !reserveEnd.isValid() ||
            !reserveEnd.isAfter(reserveStart)) {
            setNotification('Please select a valid reservation window.');
            return;
        }

        // Collect all the information we need to make a reservation
        const payload = {
            equipment_id: selectedEquipment.id,
            reservation_id: user.user,
            reserve_Start: reserveStart.toISOString(),
            reserve_End: reserveEnd.toISOString()
        };

        try {
            // Request the reservation from the backend
            const data = await apiClient(`/api/psu/equipment/reserve`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });

            console.log("data", data);

            // If the reservation was successful, add the reservation to the list of 
            // all reservations the student has made
            if(data.status === "success") {
                // Collect all the releveant information
                const newReservation = { "equipment_title": selectedEquipment.name,
                                         "reserve_start": reserveStart.toISOString(),
                                         "reserve_end": reserveEnd.toISOString() };
                
                // Kick it up to the App.jsx , so we can pass it to the checkout page
                setReservationInfo( prevReservations => [
                    ...prevReservations,
                    newReservation
                ]);
            }

            // Update the UI with the new list of equipment
            setEquipment(data.updated_available_equipment);


        } catch (error) {
            console.error('Failed to read item:', error);
            setErrorMsg(error.message);
        }

        // console.log("user:", user.user);
        // console.log("Reserving book:", selectedBook);
        // console.log("Reserve Start:", reserveStart);
        // console.log("Reserve End:", reserveEnd);

        // Demo only: this does not yet create a database reservation.
        setNotification(`Reservation request for ${selectedEquipment.name} is ready.`);
        setSelectedEquipment(null);
    };

    /////////////////////////////////////////////////////////////////

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Box sx={{ display: 'flex', minHeight: '80vh' }}>
                {/* Main content */}
                <Box component="main" sx={{ flexGrow: 1, p: 3, mt: '64px', minWidth: 0 }}>
                    <Typography variant="h4" sx={{ mb: 1 }}>
                        Equipment Catalog
                    </Typography>

                    <Typography color="text.secondary" sx={{ mb: 3 }}>
                        Browse available equipment and reserve a copy.
                    </Typography>

                    {/* Filter Elements */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                        {/* Book Search */}
                        {/*-----------------------------------------------------------*/}
                        <TextField
                            label="Search equipment"
                            placeholder="Enter a name..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            size="small"
                            sx={{ flexGrow: 1, minWidth: 180 }}
                            slotProps={{
                                input: {
                                    startAdornment: <Search sx={{ mr: 1, color: 'action.active' }} />
                                }
                            }}
                        /> 
                        {/*-----------------------------------------------------------*/}


                        {/* Genre Filter */}
                        {/*-----------------------------------------------------------*/}
                        <FormControl size="small" sx={{ minWidth: 160 }}>
                            <InputLabel>Type</InputLabel>
                            <Select
                                value={type}
                                label="Type"
                                onChange={e => setType(e.target.value)}
                            >
                                {types.map(t => (
                                    <MenuItem key={t} value={t}>{t}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        {/*-----------------------------------------------------------*/}
                    </Box>


                    {/* Book Inventory Area */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <TableContainer component={Paper} variant="outlined">
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                        <Table>
                            {/* Table Headers */}
                            {/*-------------------------------------------------------*/}
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell align="center">Total Copies</TableCell>
                                    <TableCell align="center">Available</TableCell>
                                    <TableCell align="right">Action</TableCell>
                                </TableRow>
                            </TableHead>
                            {/*-------------------------------------------------------*/}
                            

                            {/* Table Rows */}
                            {/*-------------------------------------------------------*/}
                            <TableBody>
                                {filteredEquipment.map(equipment => (
                                    <TableRow key={equipment.id} hover>
                                        <TableCell>{equipment.name}</TableCell>
                                        <TableCell>{equipment.type}</TableCell>
                                        <TableCell align="center">{equipment.copies}</TableCell>
                                        <TableCell align="center">
                                            <Chip
                                                label={equipment.available_copies > 0
                                                    ? `${equipment.available_copies} available`
                                                    : 'Unavailable'}
                                                color={equipment.available_copies > 0
                                                    ? 'success' : 'default'}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell align="right">
                                            <Button
                                                variant="outlined"
                                                size="small"
                                                disabled={equipment.available_copies < 1}
                                                onClick={() => {
                                                    setSelectedEquipment(equipment);
                                                    setReserveStart(dayjs().add(1, 'hour'));
                                                    setReserveEnd(dayjs().add(3, 'hour'));
                                                }}
                                            >
                                                Reserve
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {filteredEquipment.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={5} align="center">
                                            No equipment found.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                            {/*-------------------------------------------------------*/}
                        </Table>
                    </TableContainer>


                    {/* Reservation dialog */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Dialog
                        open={Boolean(selectedEquipment)}
                        onClose={() => setSelectedEquipment(null)}
                        fullWidth
                        maxWidth="sm"
                    >
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                        <DialogTitle>
                            Reserve {selectedEquipment?.name}
                        </DialogTitle>
                        <DialogContent>
                            <Typography sx={{ mb: 2 }} color="text.secondary">
                                Select the start and end of your reservation.
                            </Typography>

                            {/* Start Time */}
                            {/*-------------------------------------------------------*/}
                            <DateTimePicker
                                label="Reservation start"
                                value={reserveStart}
                                onChange={setReserveStart}
                                disablePast
                                sx={{ width: '100%', mb: 2, mt: 1 }}
                            />
                            {/*-------------------------------------------------------*/}


                            {/* End Time */}
                            {/*-------------------------------------------------------*/}
                            <DateTimePicker
                                label="Reservation end"
                                value={reserveEnd}
                                onChange={setReserveEnd}
                                minDateTime={reserveStart || dayjs()}
                                sx={{ width: '100%' }}
                            />
                            {/*-------------------------------------------------------*/}
                        </DialogContent>
                        <DialogActions>

                            {/* Cancel Button */}
                            {/*-------------------------------------------------------*/}
                            <Button onClick={() => setSelectedEquipment(null)}>
                                Cancel
                            </Button>
                            {/*-------------------------------------------------------*/}


                            {/* Confirm Button */}
                            {/*-------------------------------------------------------*/}
                            <Button
                                variant="contained"
                                onClick={handleReserve}
                                disabled={
                                    !reserveStart || !reserveEnd ||
                                    !reserveEnd.isAfter(reserveStart)
                                }
                            >
                                Confirm Reservation
                            </Button>
                            {/*-------------------------------------------------------*/}
                        </DialogActions>
                    </Dialog>
                    
                    {/* Reservation Notification */}
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                    <Snackbar
                        open={Boolean(notification)}
                        autoHideDuration={4000}
                        onClose={() => setNotification('')}
                    >
                    {/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/}
                        <Alert
                            severity="info"
                            onClose={() => setNotification('')}
                        >
                            {notification}
                        </Alert>
                    </Snackbar>
                    
                </Box>
            </Box>
        </LocalizationProvider>
    );
}