import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import LoginPage from './Pages/LoginPage';
import LibraryPage from './Pages/LibraryPage';
import EquipmentPage from './Pages/EquipmentPage';

import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';

/***********************************************/
export default function App() {
/***********************************************/
    // for the welcome banner
    const [user, setUser] = useState(null);
    //For keeping track of tabs
    const [tabIndex, setTabIndex] = useState(0);

    const [reservationInfo, setReservationInfo] = useState([]);

    const [sessionMessage, setSessionMessage] = useState(null)

    function allyProps(index) {
        return{
            id: `simple-tab-${index}`,
            'aria-controls': `simple-tabPanel-${index}`
        }     
    }

    // DEBUG
    //------------------------------------------/
    useEffect(() => {
    //------------------------------------------/
        console.log("Reserved info updated in App.jsx:", reservationInfo);
    }, [reservationInfo]);
  


    //------------------------------------------/
    useEffect(() => {
    //------------------------------------------/
        // Handler for expired/unauthorized requests
        const handleUnauthorized = () => {
            localStorage.removeItem('token');
            setUser(null); // Clear stale user state
            setTabIndex(0); // Redirect to Login tab
            setSessionMessage("Session expired or unauthorized. Please log in again.");
        };

        window.addEventListener('auth:unauthorized', handleUnauthorized);
        return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
    }, []);

    /////////////////////////////////////////////////////////////////

    return (
        <Box sx = {{flexGrow: 1, display: 'flex', height: '100vh'}}>
            {/* --- LEFT SIDEBAR CONTAINER --- */}
            <Box sx={{ 
                borderRight: 1, 
                borderColor: 'divider', 
                minWidth: '200px', 
                display: 'flex', 
                flexDirection: 'column',
                bgcolor: 'background.paper'
            }}>

                {/* Title */}
                <Box sx={{ 
                    p: 2, 
                    borderBottom: 1, 
                    borderColor: 'divider',
                    textAlign: 'center' 
                }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                        PSU Library
                    </Typography>
                </Box>

                {/* Vertical Tab Navigoation */}
                <Tabs
                orientation="vertical"
                variant="scrollable"
                value={tabIndex}
                onChange={(_, i) => setTabIndex(i)} 
                aria-label="vertical tab"
                sx={{borderRight: 1, borderColor: 'divider', minWidth: '200px'}}
                >
                    {/* Login Tab */}
                    <Tab
                    label ={
                        <Typography>
                            {'Login Page'}
                        </Typography>
                    }
                    {...allyProps(0)}
                    />
                    {/* Library Tab */}
                    <Tab
                    label ={
                        <Typography>
                            {'Library'}
                        </Typography>
                    }
                    {...allyProps(1)}
                    />
                    {/* Equipment Tab */}
                    <Tab
                    label ={
                        <Typography>
                            {'Equipment'}
                        </Typography>
                    }
                    {...allyProps(2)}
                    />
                </Tabs>
                {/* Username display*/}
                <Box sx={{ 
                    mt: 'auto', //Pin it to the bottom, otherwise it will look terrible
                    p: 2, 
                    borderTop: 1, 
                    borderColor: 'divider' 
                }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {user?.user ? `Welcome, ${user.user}!` : 'Welcome, Guest!'}
                    </Typography>
                </Box>
            </Box>

            <Box sx={{ flexGrow: 1, minWidth: 0, overflowY: 'auto', height: '100vh' }}>

                {/* Experimental Alert Banner -- This might be overkill */}
                {sessionMessage && (
                    <Alert 
                        severity="warning" 
                        onClose={() => setSessionMessage(null)}
                        sx={{ mb: 2 }}
                    >
                        {sessionMessage}
                    </Alert>
                )}

                <div hidden= {tabIndex !== 0}>
                    <LoginPage
                        user={user}
                        setUser={setUser}
                        onLoginSuccess={() => setTabIndex(1)}/* Redirect to Library Page */
                    />
                </div>
                <div hidden= {tabIndex !== 1}>
                    <LibraryPage
                        user={user}
                        setUser={setUser}
                        reservationInfo={reservationInfo}
                        setReservationInfo={setReservationInfo}
                    />
                </div>
                <div hidden= {tabIndex !== 2}>
                    <EquipmentPage
                        user={user}
                        setUser={setUser}
                        reservationInfo={reservationInfo}
                        setReservationInfo={setReservationInfo}
                    />
                </div>
            </Box>
        </Box>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);