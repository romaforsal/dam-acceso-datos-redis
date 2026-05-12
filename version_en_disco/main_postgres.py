import psycopg2
import time
import random
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

class PostgresBiometricManager:
    """Handles connection and operations with the PostgreSQL database."""
    
    def __init__(self):
        try:
            self.connection = psycopg2.connect(
                host="localhost",
                database="biometric_logs",
                user="admin",
                password="adminpassword",
                port="5432"
            )
            self.cursor = self.connection.cursor()
            self.connection.autocommit = True
            
            # Initialize the database schema if it doesn't exist
            self._create_table()
            console.print("[bold green]Successfully connected to PostgreSQL Docker container.[/bold green]")
        except psycopg2.OperationalError as e:
            console.print(f"[bold red]Could not connect to PostgreSQL: {e}[/bold red]")
            exit(1)

    def _create_table(self):
        """Creates the biometric logs table."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS camera_access_logs (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            access_time TIMESTAMP NOT NULL
        );
        """
        self.cursor.execute(create_table_query)

    def register_camera_access(self, user_id):
        """Inserts a user's biometric camera access into the database."""
        current_time = datetime.now()
        insert_query = "INSERT INTO camera_access_logs (user_id, access_time) VALUES (%s, %s);"
        
        try:
            self.cursor.execute(insert_query, (user_id, current_time))
            console.print(f"[cyan][+][/cyan] Registered user [bold white]{user_id}[/bold white] in Postgres DB.")
        except psycopg2.Error as e:
            console.print(f"[bold red][ERROR][/bold red] Failed to save data for user {user_id}: {e}")

    def get_all_sessions(self):
        """Retrieves and displays the persistent logs from the database."""
        select_query = "SELECT user_id, access_time FROM camera_access_logs ORDER BY access_time DESC LIMIT 10;"
        self.cursor.execute(select_query)
        records = self.cursor.fetchall()
        
        table = Table(title=f"Persistent Biometric Logs (PostgreSQL) - {datetime.now().strftime('%H:%M:%S')}", header_style="bold blue")
        table.add_column("User ID", style="cyan")
        table.add_column("Access Time", style="white")
        table.add_column("Status", style="red")

        if not records:
            table.add_row("No records", "-", "-")
        else:
            for record in records:
                # In Postgres, the data stays here forever unless we manually run a DELETE query
                table.add_row(str(record[0]), record[1].strftime('%H:%M:%S'), "Stored on Disk")
            
        console.print(table)

if __name__ == "__main__":
    manager = PostgresBiometricManager()
    
    console.print("\n[bold yellow]Starting PostgreSQL biometric simulation...[/bold yellow]\n")
    
    user_counter = 5000
    
    # We simulate a few connections
    for _ in range(5):
        time.sleep(random.uniform(0.5, 1.5))
        user_counter += 1
        manager.register_camera_access(user_counter)
        
    console.print("\n[bold yellow]Simulation finished. Fetching persistent data...[/bold yellow]\n")
    manager.get_all_sessions()