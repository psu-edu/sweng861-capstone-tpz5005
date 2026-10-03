import React from 'react';
import {useEffect, useState} from 'react';
import { styles } from '../styles';
import { apiClient } from '../apiClient';

/***********************************************/
export default function LoginPage({user, setUser, onLoginSuccess}) {
/***********************************************/
    //User login data
    const [userData, setUserData] = useState(null);

    //Login User data error message
    const [errorMsg, setErrorMsg] = useState(null);
    
    // Custom Log in
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [formErrors, setFormErrors] = useState({ username: '', password: '' });

    // Initiate user login
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        apiClient('/api/user')
            .then(data => {
                setUserData(data);
                // If the data is good
                if(data && data.authenticated)
                {   
                    //Kick it up to the Tabs
                    setUser(previousState =>{
                        return {
                            ...previousState,
                            user: data.user.username
                        };
                    });
                }
            })
            .catch(error => {
                console.error('Failed to get authentication data:', error);
                setErrorMsg(error.message);
            });
    }, []);

    //------------------------------------------/
    useEffect(() => {
    //------------------------------------------/
        console.log("clearing token");
        // Clear previous custom tokens
        localStorage.removeItem('token');
    }, []);

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/
    const handleCustomLogin = async (e) => {
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~/   
        e.preventDefault(); // Prevent page reload
        
        // 1. Inline Validation
        let errors = { username: '', password: '' };
        let isValid = true;

        if (!username.trim()) {
            errors.username = "Username/Email is required";
            isValid = false;
        }
        if (!password.trim()) {
            errors.password = "Password is required";
            isValid = false;
        }

        setFormErrors(errors);
        if (!isValid) return;

        try {
            const data = await apiClient('/auth/custom', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });

            // if it is authenticated
            if(data.authenticated && data.access_token) {
                localStorage.setItem('token', data.access_token);
                setUserData(data);

                //Kick it up to the Tabs
                setUser(previousState =>{
                    return {
                        ...previousState,
                        user: data.user.username
                    };
                });
            }
      
            setErrorMsg(null); // Clear errors

        } catch (error) {
            setErrorMsg(error.message);
        }
    };

    /////////////////////////////////////////////////////////////////

    return (
        <div style = {{  padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h1 style = {styles.heading}> {('Test1')} </h1>

            {/* Login interface */}
            <div style={styles.card}>  
                {userData?.authenticated ? (

                    /* Rendered when the user has successfully logged in via OAuth */
                    <div>
                        <p><strong> Hello, {userData.user.name || userData.user.username}! </strong></p>
                        {userData.user.avatar_url && (
                            <img 
                                src={userData.user.avatar_url} 
                                alt="User Avatar" 
                                width="60" 
                                style={{ borderRadius: '50%', marginBottom: '10px' }} 
                            />
                        )}
                        <br />
                        {/* Logout Button */}
                        <a href={'https://localhost:8000/auth/logout'} style={styles.logoutButton}>
                            {('Log Out')}
                        </a>
                    </div>
                ) : (

                    /* Rendered when the user is unauthenticated */
                    <div>
                        <h2 style={styles.subHeading}> {('Login with Email')} </h2>
                        
                        {/* Custom Login Form */}
                        <form onSubmit={handleCustomLogin} style={{ display: 'flex', flexWrap: 'wrap', flexDirection: 'column', gap: '15px', marginBottom: '20px' }}>
                            {/* Username input box */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '5px' }}> {('PSU Email')} </label>
                                <input 
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                                    placeholder = {('abc1234@psu.edu')}
                                    title= {('Valid test email: psu1855@psu.edu')}
                                />
                                {/* Inline Error */}
                                {formErrors.username && <span style={{ color: 'red', fontSize: '12px' }}>{formErrors.username}</span>}
                            </div>

                            {/* Passwrod input box */}
                            <div>
                                <label style={{ display: 'block', marginBottom: '5px' }}> {('Password')} </label>
                                <input 
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                                    placeholder = {('Passwords are case sensitive')}
                                    title= {('Valid test password: PennState1855')}
                                />
                                {/* Inline Error */}
                                {formErrors.password && <span style={{ color: 'red', fontSize: '12px' }}>{formErrors.password}</span>}
                            </div>

                            {/* Custom login button */}
                            <button type="submit" style={{ padding: '10px', backgroundColor: '#1976d2', color: 'white', 
                                                           border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                {('Log In')} 
                            </button>
                        </form>

                        <div style={{ textAlign: 'center', margin: '15px 0', color: '#666' }}>— {('OR')} —</div>

                        {/* GitHub Login Button */}
                        <div style={{ textAlign: 'center' }}>
                            <a href={'https://localhost:8000/auth/login'} style={{...styles.loginButton, display: 'block', textAlign: 'center'}}>
                                {('Log In with GitHub')} 
                            </a>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}