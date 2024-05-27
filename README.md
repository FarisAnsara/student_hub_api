# Student Hub API

This is a RESTful API developed to manage student-related information and operations. The API is built with Node.js and Express, and it provides endpoints for various CRUD operations.

## Features
- Manage student data (create, read, update, delete).
- Handle course enrollments and schedules.
- Authenticate and authorize users.
- Retrieve detailed reports and analytics.

## Installation
1. **Clone the repository:**
    ```bash
    git clone https://github.com/FarisAnsara/student_hub_api.git
    ```
2. **Navigate to the project directory:**
    ```bash
    cd student_hub_api
    ```
3. **Install dependencies:**
    ```bash
    npm install
    ```
4. **Set up environment variables:**
    Create a `.env` file in the root directory and add the necessary environment variables (refer to `.env.example` for guidance).

5. **Run the application:**
    ```bash
    npm start
    ```

## API Endpoints
### Students
- **GET /students**: Retrieve a list of all students.
- **POST /students**: Create a new student.
- **GET /students/:id**: Retrieve a specific student by ID.
- **PUT /students/:id**: Update a specific student by ID.
- **DELETE /students/:id**: Delete a specific student by ID.

### Courses
- **GET /courses**: Retrieve a list of all courses.
- **POST /courses**: Create a new course.
- **GET /courses/:id**: Retrieve a specific course by ID.
- **PUT /courses/:id**: Update a specific course by ID.
- **DELETE /courses/:id**: Delete a specific course by ID.

### Enrollments
- **POST /enrollments**: Enroll a student in a course.
- **GET /enrollments**: Retrieve a list of all enrollments.
- **DELETE /enrollments/:id**: Unenroll a student from a course.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact
For any inquiries, please contact [Faris Ansara](https://github.com/FarisAnsara).
