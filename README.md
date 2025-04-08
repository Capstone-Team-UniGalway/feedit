## Table of Contents

- [Merging Strategy](#merging-strategy)
- [Running the Project Locally](#running-the-project-locally)

## IMPORTANT!
- Always pull before starting work and before pushing!
   ```sh
   git pull
   ```
- Always install requirements after pulling
   ```sh
   pip install -r requirements.txt
   ```
- Always migrate after pulling (there could be new migrations created)
   ```sh
   python manage.py migrate
   ```

## Merging Strategy

To ensure a smooth and organized workflow, follow the merging strategy outlined below:

1. **Create a new branch for each change:**
   - Branch names should be in line with the board work item. For example, if you are working on issue #42, name your branch `42-description`.

   ```sh
   git checkout -b 42-description
   ```

2. **Make your changes and commit them:**
   - Ensure your commit messages are clear and descriptive. Reference the issue number in your commit message.

   ```sh
   git add .
   git commit -m "Detailed description of the changes made"
   ```

3. **Push the new branch to the remote repository:**

   ```sh
   git push origin 42-description
   ```

4. **Create a Pull Request (PR) into the `main` branch:**
   - Once the new branch is pushed, create a PR into the `main` branch.
   - In the PR description, include "Closes #issue number" to connect with the board work item.

   ```markdown
   Closes #42: Detailed description of the changes made
   ```

5. **Review and merge the PR:**
   - Ensure that the PR is reviewed by at least one other team member before merging.
   - Once approved, merge the PR into the `main` branch.

6. **Delete the branch after merging:**
   - delete the branch upon approving the PR, to keep the repository clean.

By following this strategy, we can maintain a clean and organized codebase while ensuring that all changes are properly tracked and reviewed.


## Running the Project Locally

To run the project locally, follow these steps:

1. **Clone the repository (if not already cloned):**
   ```sh
   mkdir feedit
   cd feedit
   git clone https://github.com/Capstone-Team-UniGalway/feedit.git .
   ```

   **Or pull the latest changes if already cloned:**
   ```sh
   git pull origin main
   ```

2. **Create a virtual environment (if running for the first time):**
   ```sh
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     - Command Prompt:
       ```sh
       venv\Scripts\activate
       ```
     - Git Bash:
       ```sh
       source venv/Scripts/activate
       ```
   - On macOS and Linux:
     ```sh
     source venv/bin/activate
     ```

4. **Install the required packages:**
   ```sh
   pip install -r requirements.txt
   ```
5. **Navigate into the `feedit_app` directory:**
   ```sh
   cd feedit_app
   ```

6. **Create a `.env` file from `.env.example` and set the necessary environment variables:**
   ```sh
   cp .env.example .env
   ```

   Edit the `.env` file to set the necessary environment variables. At a minimum, you should set:
   Note: You can use https://randomkeygen.com/ to generate a secure secret key.
   ```
   DJANGO_ENV=development
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=127.0.0.1,localhost
   ```

6. **Run Django commands for the first run:**
   - Apply database migrations:
     ```sh
     python manage.py migrate
     ```

   - Create a superuser:
     ```sh
     python manage.py createsuperuser
     ```

   - Run the development server:
     ```sh
     python manage.py runserver
     ```

You should now be able to access the project locally at `http://localhost:8000`.
