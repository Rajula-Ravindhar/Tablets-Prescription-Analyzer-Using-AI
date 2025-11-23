import sqlite3
import pandas as pd

# function for establishing the connection with database
def get_db_connection():
    return sqlite3.connect('MediGrid.db')

#fuction for saving the data with dynamic table creation.
def save_to_db(patient_info,prescription_list):

    patient_name=patient_info.get("Name").replace(' ','_')

    connection=get_db_connection()
    c=connection.cursor()

    patient_table=f"""
    CREATE TABLE IF NOT EXISTS Prescription (
    PATIENT_NAME text,
    MEDICATION_NAME text,
    DOSAGE text,
    FREQUENCY text,
    DURATION text,
    MAP_LINK text,
    Data_Saved DATETIME DEFAULT CURRENT_TIMESTAMP
    )"""

    c.execute(patient_table)

    for item in prescription_list:

        inserting_details=f"""
        INSERT INTO Prescription (PATIENT_NAME,MEDICATION_NAME,DOSAGE,FREQUENCY,DURATION,MAP_LINK)
        VALUES(?,?,?,?,?,?)"""

        c.execute(inserting_details,(patient_name,item.get("medications", "Not provided"),
            item.get("Dosage", "Not provided"),
            item.get("Frequency", "Not provided"),
            item.get("duration", "Not provided"),
            item.get("Map_link", "Not provided")
        ))
    connection.commit()
    connection.close()
    return 'Saved_Successfully'


# this fuction will displays the entire table
def display_table():
    connection=get_db_connection()
    c=connection.cursor()
    try:
        data=pd.read_sql_query('SELECT * FROM Prescription ORDER BY Data_Saved DESC',connection)
        display_rows=[]
        previous_timeStamp=None
        for index,row in data.iterrows():
            current_timeStamp=row['Data_Saved']

            if previous_timeStamp is not None and current_timeStamp!= previous_timeStamp:
                empty_row= {col: '' for col in data.columns}
                display_rows.append(empty_row)
            
            display_rows.append(row.to_dict())
            previous_timeStamp=current_timeStamp
        
        final_display_df=pd.DataFrame(display_rows)
        return final_display_df


    finally:
        connection.close()
        

    