# backend.py

import psycopg2
from psycopg2 import sql

class DatabaseManager:
    def __init__(self, dbname, user, password, host, port):
        self.conn = None
        self.cursor = None
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print("Database connection successful.")
        except psycopg2.OperationalError as e:
            print(f"Error connecting to database: {e}")
            self.conn = None
            self.cursor = None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except psycopg2.DatabaseError as e:
            self.conn.rollback()
            print(f"Database error: {e}")
            return False

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.DatabaseError as e:
            print(f"Database error: {e}")
            return None

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except psycopg2.DatabaseError as e:
            print(f"Database error: {e}")
            return None

    # Employee Profile CRUD
    def create_employee(self, name, email, job_role):
        query = "INSERT INTO employees (name, email, job_role) VALUES (%s, %s, %s) RETURNING employee_id;"
        self.cursor.execute(query, (name, email, job_role))
        self.conn.commit()
        return self.cursor.fetchone()[0]

    def read_employees(self):
        query = "SELECT employee_id, name, email, job_role FROM employees;"
        return self.fetch_all(query)
    
    def read_employee_by_id(self, employee_id):
        query = "SELECT employee_id, name, email, job_role FROM employees WHERE employee_id = %s;"
        return self.fetch_one(query, (employee_id,))

    def update_employee(self, employee_id, name, email, job_role):
        query = "UPDATE employees SET name = %s, email = %s, job_role = %s WHERE employee_id = %s;"
        return self.execute_query(query, (name, email, job_role, employee_id))

    def delete_employee(self, employee_id):
        query = "DELETE FROM employees WHERE employee_id = %s;"
        return self.execute_query(query, (employee_id,))
    
    # Task Tracking CRUD
    def create_task(self, employee_id, task_date, duration, description, priority, status, outcome):
        query = """
        INSERT INTO tasks (employee_id, task_date, duration_hours, description, priority, status, outcome) 
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        return self.execute_query(query, (employee_id, task_date, duration, description, priority, status, outcome))

    def read_tasks_by_employee(self, employee_id):
        query = "SELECT * FROM tasks WHERE employee_id = %s ORDER BY task_date DESC;"
        return self.fetch_all(query, (employee_id,))

    def update_task(self, task_id, task_date, duration, description, priority, status, outcome):
        query = """
        UPDATE tasks 
        SET task_date = %s, duration_hours = %s, description = %s, priority = %s, status = %s, outcome = %s 
        WHERE task_id = %s;
        """
        return self.execute_query(query, (task_date, duration, description, priority, status, outcome, task_id))

    def delete_task(self, task_id):
        query = "DELETE FROM tasks WHERE task_id = %s;"
        return self.execute_query(query, (task_id,))

    # Goal Setting CRUD
    def create_goal(self, employee_id, description, goal_type, target_value, start_date, end_date, status):
        query = """
        INSERT INTO goals (employee_id, goal_description, goal_type, target_value, start_date, end_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        return self.execute_query(query, (employee_id, description, goal_type, target_value, start_date, end_date, status))

    def read_goals_by_employee(self, employee_id):
        query = "SELECT * FROM goals WHERE employee_id = %s ORDER BY end_date DESC;"
        return self.fetch_all(query, (employee_id,))
    
    def update_goal(self, goal_id, description, goal_type, target_value, start_date, end_date, status):
        query = """
        UPDATE goals SET goal_description = %s, goal_type = %s, target_value = %s, start_date = %s, end_date = %s, status = %s
        WHERE goal_id = %s;
        """
        return self.execute_query(query, (description, goal_type, target_value, start_date, end_date, status, goal_id))

    def delete_goal(self, goal_id):
        query = "DELETE FROM goals WHERE goal_id = %s;"
        return self.execute_query(query, (goal_id,))

    # Leaderboard and Team Collaboration
    def add_colleague_to_network(self, employee_id, colleague_id):
        query = "INSERT INTO performance_network (employee_id, colleague_id) VALUES (%s, %s);"
        return self.execute_query(query, (employee_id, colleague_id))
    
    def remove_colleague_from_network(self, employee_id, colleague_id):
        query = "DELETE FROM performance_network WHERE employee_id = %s AND colleague_id = %s;"
        return self.execute_query(query, (employee_id, colleague_id))

    def get_leaderboard_data(self):
        query = """
        SELECT
            e.name,
            COUNT(t.task_id) AS total_tasks,
            SUM(t.duration_hours) AS total_hours,
            AVG(t.duration_hours) AS avg_duration
        FROM employees e
        JOIN tasks t ON e.employee_id = t.employee_id
        GROUP BY e.name
        ORDER BY total_tasks DESC;
        """
        return self.fetch_all(query)
    
    # Business Insights
    def get_business_insights(self):
        query = """
        SELECT
            e.name,
            COUNT(t.task_id) AS num_tasks_completed,
            SUM(t.duration_hours) AS total_hours_worked,
            AVG(t.duration_hours) AS avg_completion_time
        FROM employees e
        JOIN tasks t ON e.employee_id = t.employee_id
        WHERE t.status = 'Completed' -- Assuming a 'Completed' status
        GROUP BY e.name;
        """
        results = self.fetch_all(query)
        
        query_min_max = """
        SELECT
            MIN(duration_hours) AS min_duration,
            MAX(duration_hours) AS max_duration
        FROM tasks
        WHERE status = 'Completed';
        """
        min_max_results = self.fetch_one(query_min_max)
        
        return results, min_max_results