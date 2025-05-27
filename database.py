import psycopg2
import yaml
import os
from dotenv import load_dotenv


class Database:

    def __init__(self, config_path):
        self.config_path = config_path
        load_dotenv()
        self.conn = None
        self.cursor = None


    def connect(self): # -- done
        if self.conn and not self.conn.closed:
            print("Already connected")
            return True

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print("Database URL is missing from .env file.")
            return False

        try:
            self.conn = psycopg2.connect(db_url)
            self.conn.autocommit = True  # Autocommit changes
            self.cursor = self.conn.cursor()
            print("Database connection successful.")
            return True

        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            self.conn = None
            self.cursor = None
            return False

        except Exception as e:
            print(f"An unexpected error occurred during connection: {e}")
            self.conn = None
            self.cursor = None
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
            print("Database cursor closed.")
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None
            print("Database connection closed.")
        elif self.conn and self.conn.closed:
             print("Database connection already closed.")


    def create_tables(self):
        if not self.conn or self.conn.closed or not self.cursor:
            print("Not connected to the database. Cannot create tables.")
            if not self.connect():
                 return False

        if 'tables' not in self.config:
            print("No 'tables' section found in configuration. No tables created.")
            return False

        success = True
        print(self.config.get('tables', {}))
        for table_name, table_config in self.config.get('tables', {}).items():
            if 'fields' not in table_config:
                print(f"No 'fields' defined for table '{table_name}'. Skipping.")
                continue

            columns_sql = "id SERIAL PRIMARY KEY, " + ", ".join([f"{name} {type}" for name, type in table_config['fields'].items()])
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});"

            try:
                print(f"Creating table '{table_name}'...")
                self.cursor.execute(create_table_sql)
                print(f"Table '{table_name}' checked/created successfully.")
                
            except psycopg2.Error as e:
                print(f"Error creating table '{table_name}': {e}")
                # self.conn.rollback() # Rollback if not using autocommit
                success = False

            except Exception as e:
                 print(f"An unexpected error occurred creating table '{table_name}': {e}")
                 success = False

        return success


    def insert_data(self, table_name, data):
        """
        Inserts data into the specified table.

        Args:
            table_name (str): The name of the table to insert data into.
            data (dict): A dictionary where keys are column names and values are the data to insert.
                         Assumes 'id' and 'timestamp' are handled by the database if not provided.
        """
        if not self.conn or self.conn.closed or not self.cursor:
            print("Not connected to the database. Cannot insert data.")
            if not self.connect(): # Try to reconnect
                 return False

        # if table_name not in self.config.get('tables', {}):
        #     print(f"Table '{table_name}' not defined in configuration.")
        #     return False

        # Filter out keys not meant for direct insertion (like auto-generated ones)
        # Or better, get column names from config excluding auto-generated ones if possible
        # For simplicity here, we just use the keys from the input dict
        columns = data.keys()
        values = [data[col] for col in columns]

        # Construct parameterized query
        columns_sql = ", ".join(columns)
        placeholders_sql = ", ".join(["%s"] * len(values))
        insert_sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders_sql});"

        try:
            print(f"Executing SQL: {insert_sql} with values: {values}")
            self.cursor.execute(insert_sql, values)
            # self.conn.commit() # Not needed if autocommit=True
            print(f"Data inserted into '{table_name}' successfully.")
            return True
        except psycopg2.Error as e:
            print(f"Error inserting data into '{table_name}': {e}")
            # self.conn.rollback() # Rollback if not using autocommit
            return False
        except Exception as e:
            print(f"An unexpected error occurred during insertion into '{table_name}': {e}")
            return False
