import psycopg2
import yaml
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Database:

    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self.conn = None
        self.cursor = None
        if not self.config:
            raise ValueError("Failed to load database configuration.")

    def _load_config(self):
        """Loads database configuration from the YAML file."""
        if not os.path.exists(self.config_path):
            logging.error(f"Configuration file not found: {self.config_path}")
            return None
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML configuration: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading configuration file: {e}")
            return None

    def connect(self):
        """Establishes a connection to the database."""
        if self.conn and not self.conn.closed:
            logging.info("Already connected to the database.")
            return True

        if not self.config or 'database' not in self.config:
            logging.error("Database configuration is missing or incomplete.")
            return False

        db_config = self.config['database']
        required_keys = ['host', 'port', 'user', 'password', 'dbname']
        if not all(key in db_config for key in required_keys):
            logging.error("Database configuration is missing required keys (host, port, user, password, dbname).")
            return False

        try:
            logging.info(f"Connecting to database '{db_config['dbname']}' on {db_config['host']}:{db_config['port']}...")
            self.conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                dbname=db_config['dbname']
            )
            self.conn.autocommit = True # Autocommit changes
            self.cursor = self.conn.cursor()
            logging.info("Database connection successful.")
            return True
        except psycopg2.OperationalError as e:
            logging.error(f"Database connection failed: {e}")
            self.conn = None
            self.cursor = None
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during connection: {e}")
            self.conn = None
            self.cursor = None
            return False

    def disconnect(self):
        """Closes the database connection and cursor."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
            logging.info("Database cursor closed.")
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None
            logging.info("Database connection closed.")
        elif self.conn and self.conn.closed:
             logging.info("Database connection already closed.")


    def create_tables(self):
        if not self.conn or self.conn.closed or not self.cursor:
            logging.error("Not connected to the database. Cannot create tables.")
            if not self.connect(): # Try to reconnect
                 return False

        if 'tables' not in self.config:
            logging.warning("No 'tables' section found in configuration. No tables created.")
            return True # Not an error, just nothing to do

        success = True
        for table_name, table_config in self.config.get('tables', {}).items():
            if 'columns' not in table_config:
                logging.warning(f"No 'columns' defined for table '{table_name}'. Skipping.")
                continue

            columns_sql = ", ".join(table_config['columns'])
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});"

            try:
                logging.info(f"Creating table '{table_name}'...")
                self.cursor.execute(create_table_sql)
                logging.info(f"Table '{table_name}' checked/created successfully.")
            except psycopg2.Error as e:
                logging.error(f"Error creating table '{table_name}': {e}")
                # self.conn.rollback() # Rollback if not using autocommit
                success = False
            except Exception as e:
                 logging.error(f"An unexpected error occurred creating table '{table_name}': {e}")
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
            logging.error("Not connected to the database. Cannot insert data.")
            if not self.connect(): # Try to reconnect
                 return False

        if table_name not in self.config.get('tables', {}):
            logging.error(f"Table '{table_name}' not defined in configuration.")
            return False

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
            logging.debug(f"Executing SQL: {insert_sql} with values: {values}")
            self.cursor.execute(insert_sql, values)
            # self.conn.commit() # Not needed if autocommit=True
            logging.info(f"Data inserted into '{table_name}' successfully.")
            return True
        except psycopg2.Error as e:
            logging.error(f"Error inserting data into '{table_name}': {e}")
            # self.conn.rollback() # Rollback if not using autocommit
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during insertion into '{table_name}': {e}")
            return False

# Example usage (optional, for testing)
if __name__ == '__main__':
    try:
        db = Database(config_path='../config.yaml') # Adjust path if running from different directory

        if db.connect():
            if db.create_tables():
                # Example insertion
                sample_data = {'temperature': 25.5, 'humidity': 60.2}
                if db.insert_data('sensor_data', sample_data):
                    print("Sample data inserted.")

                # Example insertion with more columns if needed (adjust config.yaml accordingly)
                # sample_data_full = {'timestamp': '2023-10-27 10:00:00+00', 'temperature': 26.1, 'humidity': 59.8}
                # db.insert_data('sensor_data', sample_data_full)

            db.disconnect()
    except ValueError as e:
        print(f"Initialization Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
