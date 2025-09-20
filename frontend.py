# frontend.py

import streamlit as st
import pandas as pd
from backend import DatabaseManager # Make sure backend.py is in the same directory

# --- PostgreSQL Connection ---
# REMEMBER TO REPLACE THESE WITH YOUR ACTUAL DETAILS
db = DatabaseManager(
    dbname="pms_db",
    user="postgres",
    password="suhani..",
    host="localhost",
    port="5432"
)

st.set_page_config(layout="wide")

# --- Streamlit UI ---
st.title("👨‍💼 Performance Management System")
st.markdown("---")

menu = ["Employee Profile", "Task Tracking", "Goal Setting", "Leaderboard", "Business Insights"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- Employee Profile Section ---
if choice == "Employee Profile":
    st.header("👤 Employee Profile Management")
    st.subheader("Add New Employee")
    with st.form("add_employee_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        job_role = st.text_input("Job Role")
        submit_add = st.form_submit_button("Add Employee")
        if submit_add:
            if db.create_employee(name, email, job_role):
                st.success(f"Employee '{name}' added successfully!")
            else:
                st.error("Could not add employee. Email might already exist.")
    
    st.subheader("All Employees")
    employees_data = db.read_employees()
    if employees_data:
        df_employees = pd.DataFrame(employees_data, columns=["ID", "Name", "Email", "Job Role"])
        st.dataframe(df_employees)

    st.subheader("Update/Delete Employee")
    employee_ids = [emp[0] for emp in employees_data] if employees_data else []
    selected_id = st.selectbox("Select Employee by ID", employee_ids)
    if selected_id:
        selected_emp = db.read_employee_by_id(selected_id)
        if selected_emp:
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("New Name", value=selected_emp[1])
                new_email = st.text_input("New Email", value=selected_emp[2])
            with col2:
                new_job_role = st.text_input("New Job Role", value=selected_emp[3])
            
            update_btn = st.button("Update Employee")
            delete_btn = st.button("Delete Employee")

            if update_btn:
                if db.update_employee(selected_id, new_name, new_email, new_job_role):
                    st.success("Employee updated successfully!")
                else:
                    st.error("Failed to update employee.")
            if delete_btn:
                if db.delete_employee(selected_id):
                    st.success("Employee deleted successfully!")
                else:
                    st.error("Failed to delete employee.")

# --- Task Tracking Section ---
elif choice == "Task Tracking":
    st.header("📝 Task and Progress Tracking")
    employees_data = db.read_employees()
    employees_dict = {emp[0]: emp[1] for emp in employees_data} if employees_data else {}
    
    selected_employee_id = st.selectbox("Select Employee", list(employees_dict.keys()), format_func=lambda x: employees_dict[x])
    
    if selected_employee_id:
        st.subheader(f"Add a New Task for {employees_dict[selected_employee_id]}")
        with st.form("add_task_form"):
            task_date = st.date_input("Date")
            duration = st.number_input("Duration (hours)", min_value=0.0, format="%f")
            description = st.text_area("Task Description")
            col1, col2, col3 = st.columns(3)
            with col1:
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            with col2:
                status = st.selectbox("Status", ["In Progress", "Completed", "Pending"])
            with col3:
                outcome = st.text_input("Outcome")
            submit_task = st.form_submit_button("Log Task")
            
            if submit_task:
                if db.create_task(selected_employee_id, task_date, duration, description, priority, status, outcome):
                    st.success("Task logged successfully!")
                else:
                    st.error("Failed to log task.")
        
        st.subheader(f"Task History for {employees_dict[selected_employee_id]}")
        tasks = db.read_tasks_by_employee(selected_employee_id)
        if tasks:
            df_tasks = pd.DataFrame(tasks, columns=["ID", "Employee ID", "Date", "Duration", "Description", "Priority", "Status", "Outcome"])
            st.dataframe(df_tasks)
            # Visualize performance trends
            st.line_chart(df_tasks.set_index("Date")["Duration"])
        else:
            st.info("No tasks logged for this employee.")

# --- Goal Setting Section ---
elif choice == "Goal Setting":
    st.header("🎯 Goal Setting")
    employees_data = db.read_employees()
    employees_dict = {emp[0]: emp[1] for emp in employees_data} if employees_data else {}
    selected_employee_id = st.selectbox("Select Employee", list(employees_dict.keys()), format_func=lambda x: employees_dict[x])

    if selected_employee_id:
        st.subheader(f"Set a New Goal for {employees_dict[selected_employee_id]}")
        with st.form("add_goal_form"):
            goal_description = st.text_area("Goal Description")
            goal_type = st.selectbox("Goal Type", ["Professional", "Personal"])
            target_value = st.number_input("Target Value (e.g., # of reports)", min_value=1)
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            status = st.selectbox("Status", ["In Progress", "Achieved", "Not Started"])
            submit_goal = st.form_submit_button("Set Goal")
            
            if submit_goal:
                if db.create_goal(selected_employee_id, goal_description, goal_type, target_value, start_date, end_date, status):
                    st.success("Goal set successfully!")
                else:
                    st.error("Failed to set goal.")

        st.subheader("Current Goals")
        goals = db.read_goals_by_employee(selected_employee_id)
        if goals:
            df_goals = pd.DataFrame(goals, columns=["ID", "Employee ID", "Description", "Type", "Target", "Start Date", "End Date", "Status"])
            st.dataframe(df_goals)
        else:
            st.info("No goals set for this employee.")

# --- Leaderboard Section ---
elif choice == "Leaderboard":
    st.header("🏆 Leaderboard and Team Collaboration")
    st.subheader("Employee Rankings")
    leaderboard_data = db.get_leaderboard_data()
    if leaderboard_data:
        df_leaderboard = pd.DataFrame(leaderboard_data, columns=["Name", "Total Tasks", "Total Hours", "Avg Duration"])
        df_leaderboard.index = range(1, len(df_leaderboard) + 1)
        st.dataframe(df_leaderboard.sort_values(by="Total Tasks", ascending=False))
        st.bar_chart(df_leaderboard.set_index("Name")[["Total Tasks", "Total Hours"]])
    else:
        st.info("No data available to create a leaderboard.")

    st.subheader("Performance Network")
    employees_data = db.read_employees()
    employees_dict = {emp[0]: emp[1] for emp in employees_data} if employees_data else {}
    
    col1, col2 = st.columns(2)
    with col1:
        if employees_dict:
            selected_employee_id = st.selectbox("Select Your Profile", list(employees_dict.keys()), format_func=lambda x: employees_dict[x], key="profile_select")
    with col2:
        if employees_dict:
            colleague_options = {k: v for k, v in employees_dict.items() if k != selected_employee_id}
            selected_colleague_id = st.selectbox("Select Colleague to Add/Remove", list(colleague_options.keys()), format_func=lambda x: employees_dict[x], key="colleague_select")

    if selected_employee_id and selected_colleague_id:
        add_btn = st.button("Add to Network")
        remove_btn = st.button("Remove from Network")
        if add_btn:
            if db.add_colleague_to_network(selected_employee_id, selected_colleague_id):
                st.success(f"Added {employees_dict[selected_colleague_id]} to your network.")
            else:
                st.error("Failed to add colleague. They might already be in your network.")
        if remove_btn:
            if db.remove_colleague_from_network(selected_employee_id, selected_colleague_id):
                st.success(f"Removed {employees_dict[selected_colleague_id]} from your network.")
            else:
                st.error("Failed to remove colleague.")

# --- Business Insights Section ---
elif choice == "Business Insights":
    st.header("📊 Business Insights")
    st.write("Actionable insights from your task data.")
    
    results, min_max = db.get_business_insights()
    
    if results:
        df_insights = pd.DataFrame(results, columns=["Employee Name", "Tasks Completed (COUNT)", "Total Hours Worked (SUM)", "Avg Completion Time (AVG)"])
        st.subheader("Task and Time Insights by Employee")
        st.dataframe(df_insights.set_index("Employee Name"))

        st.subheader("Task Count per Employee")
        st.bar_chart(df_insights.set_index("Employee Name")["Tasks Completed (COUNT)"])

        st.subheader("Total Hours Worked per Employee")
        st.bar_chart(df_insights.set_index("Employee Name")["Total Hours Worked (SUM)"])
    else:
        st.info("No completed task data to display insights.")

    if min_max:
        st.subheader("Task Completion Duration (All Employees)")
        min_duration, max_duration = min_max
        if min_duration is not None and max_duration is not None:
            st.metric(label="Shortest Task Duration (MIN)", value=f"{min_duration:.2f} hours")
            st.metric(label="Longest Task Duration (MAX)", value=f"{max_duration:.2f} hours")
        else:
            st.info("No completed task data to calculate min/max duration.")
    
    st.markdown("---")
    st.write("These insights are derived using COUNT, SUM, AVG, MIN, and MAX aggregate functions.")

# --- Run the App ---
if __name__ == '__main__':
    st.info("To run the application, save this file as frontend.py and the backend code as backend.py in the same directory. Then run `streamlit run frontend.py` in your terminal.")