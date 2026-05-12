import redis
import time
import random
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class BiometricCacheManager:
    # ... (Keep the exact same class from the previous step) ...
    def __init__(self, host='localhost', port=6379, ttl=300):
        self.ttl = ttl
        try:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            self.client.ping()
            console.print(Panel("[bold green]Successfully connected to Redis Docker container.[/bold green]", title="System Status", border_style="green"))
        except redis.ConnectionError:
            console.print(Panel("[bold red]Could not connect to Redis. Is the Docker container running?[/bold red]", title="System Error", border_style="red"))
            exit(1)

    def register_camera_access(self, user_id):
        session_key = f"biometry:session:{user_id}"
        current_time = datetime.now().strftime('%H:%M:%S')
        access_data = f"Camera active since {current_time}"
        
        try:
            self.client.setex(name=session_key, time=self.ttl, value=access_data)
        except redis.RedisError as e:
            console.print(f"[bold red][ERROR][/bold red] Failed to save data for user {user_id}: {e}")

    def get_active_sessions(self):
        """Retrieves, sorts by TTL, and displays all active sessions."""
        active_keys = self.client.keys("biometry:session:*")
        
        table = Table(title=f"Live Biometric Sessions - Updated at {datetime.now().strftime('%H:%M:%S')}", header_style="bold magenta")
        table.add_column("Session Key", style="cyan", no_wrap=True)
        table.add_column("Access Data", style="white")
        table.add_column("Time To Live (TTL)", justify="right", style="green")

        if not active_keys:
            table.add_row("No active users", "-", "-")
            console.print(table)
            return

        # 1. Create a temporary list to hold the data before displaying
        sessions_to_display = []

        for key in active_keys:
            session_data = self.client.get(key)
            remaining_ttl = self.client.ttl(key)
            
            # Avoid a race condition where a key expires exactly between keys() and get()
            if session_data is not None and remaining_ttl > 0:
                sessions_to_display.append({
                    "key": key,
                    "data": session_data,
                    "ttl": remaining_ttl
                })
        
        # 2. Sort the list of dictionaries by the "ttl" key
        # reverse=False means ascending order (lowest TTL / oldest connections at the top)
        sessions_to_display.sort(key=lambda item: item["ttl"], reverse=False)

        # 3. Populate the Rich table with the sorted data
        for session in sessions_to_display:
            ttl_color = "red" if session["ttl"] < 60 else "green"
            table.add_row(
                session["key"], 
                session["data"], 
                f"[{ttl_color}]{session['ttl']}s[/{ttl_color}]"
            )
            
        console.print(table)


if __name__ == "__main__":
    manager = BiometricCacheManager(ttl=60) # Set TTL to 60s for the video so it expires faster!
    
    console.print("\n[bold yellow]Starting CONTINUOUS biometric simulation... Press CTRL+C to stop.[/bold yellow]\n")
    time.sleep(2)
    
    try:
        user_counter = 1000
        # Continuous loop for video demonstration
        while True:
            # 1. Randomly decide if a new user connects (70% chance per cycle)
            if random.random() > 0.3:
                user_counter += 1
                manager.register_camera_access(user_counter)
                console.print(f"[cyan][+][/cyan] New user [bold white]{user_counter}[/bold white] connected to camera.")
            
            # 2. Show the updated table
            manager.get_active_sessions()
            
            # 3. Wait a few seconds before the next update
            time.sleep(4)
            
    except KeyboardInterrupt:
        console.print("\n[bold red]Simulation stopped by user.[/bold red]")