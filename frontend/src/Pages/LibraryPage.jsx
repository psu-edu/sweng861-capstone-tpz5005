import React from 'react';
import {useEffect, useState} from 'react';
import { styles } from '../styles';
import { apiClient } from '../apiClient';

/***********************************************/
export default function LibraryPage({user, setUser}) {
/***********************************************/
    //User login data
    const [userData, setUserData] = useState(null);

    // Initiate user login
    //------------------------------------------/
    useEffect(() => { 
    //------------------------------------------/
        console.log("Hello World!");
    }, []);

    /////////////////////////////////////////////////////////////////

    return (
        <div style = {{  padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h1 style = {styles.heading}> {'PSU Library'} </h1>
        </div>
    );
}