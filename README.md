# SWENG 861: Capstone Project
This is the repository containing my capstone project for a Campus Library. Students are more busy than ever, and many have to travel across campus to get to the library only to find the book they’re looking for has already been checked out. By using ‘Lion Books’, a student can not only check to see its availability, but schedule to have the book picked out and ready for pickup the next time they are in the area.

## Student Information

- Thomas Zimmerman (tpz5005)

- Course - SWENG861

## How to Clone

- git clone git@github.com:psu-edu/sweng861-capstone-tpz5005.git

## How to Build

```bash
# cd into the repository
cd sweng861-capstone-tpz5005/

# Setup environment
source build.sh
```

## How to Run

- From the root directory of the project

```bash
# Launch the Docker Container
docker-compose up
```
- To open the project, hold the 'Ctrl' key and click the 'https://localhost:3000/' link


## To run Unit Tests

- From the root directory of the project

```bash
# cd into the frontend directory of the project
cd frontend/

# To run the frontend test scripts
npm run test-frontend

# To run the backend test scripts
npm run test-backend

# To run all test scripts
npm run test-all
```
