from discord.ext import commands
import discord
import aiohttp
from datetime import datetime
import pytz


class FlightPlanner(commands.Cog):
    """
    A plugin to help plan flights with Qantas or Jetstar.
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="plan")
    async def plan_flight(self, ctx):
        """Start planning a flight - choose between Qantas or Jetstar"""
        
        # Create an embed with the question
        embed = discord.Embed(
            title="✈️ Flight Planning",
            description="Which airline are you planning to fly with?",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Click a button below to select your airline")
        
        # Create buttons for Qantas and Jetstar
        view = FlightSelectionView(ctx.author, self.bot)
        
        # Send the message with buttons
        await ctx.send(embed=embed, view=view)


class FlightSelectionView(discord.ui.View):
    """View with buttons for selecting Qantas or Jetstar"""
    
    def __init__(self, author, bot):
        super().__init__(timeout=120)
        self.author = author
        self.bot = bot
    
    @discord.ui.button(label="Qantas", style=discord.ButtonStyle.red, emoji="🦘")
    async def qantas_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🦘 Qantas Flight Selected",
            description="Please select which aircraft will be operating your flight:",
            color=discord.Color.red()
        )
        
        aircraft_view = AircraftSelectionView(self.author, "Qantas", self.bot)
        await interaction.response.edit_message(embed=embed, view=aircraft_view)
        self.stop()
    
    @discord.ui.button(label="Jetstar", style=discord.ButtonStyle.green, emoji="⭐")
    async def jetstar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="⭐ Jetstar Flight Selected",
            description="Please select which aircraft will be operating your flight:",
            color=discord.Color.green()
        )
        
        aircraft_view = AircraftSelectionView(self.author, "Jetstar", self.bot)
        await interaction.response.edit_message(embed=embed, view=aircraft_view)
        self.stop()
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class AircraftSelectionView(discord.ui.View):
    """View with dropdown menu for selecting aircraft"""
    
    def __init__(self, author, airline, bot):
        super().__init__(timeout=120)
        self.author = author
        self.airline = airline
        self.bot = bot
        
        if airline == "Jetstar":
            self.add_item(JetstarAircraftDropdown(author, airline, bot))
        else:
            self.add_item(QantasAircraftDropdown(author, airline, bot))


class JetstarAircraftDropdown(discord.ui.Select):
    """Dropdown menu for Jetstar aircraft"""
    
    def __init__(self, author, airline, bot):
        self.author = author
        self.airline = airline
        self.bot = bot
        
        options = [
            discord.SelectOption(label="Airbus A320", emoji="✈️"),
            discord.SelectOption(label="Airbus A320neo", emoji="✈️"),
            discord.SelectOption(label="Airbus A321", emoji="✈️"),
            discord.SelectOption(label="Airbus A321neo", emoji="✈️"),
            discord.SelectOption(label="Boeing 787-8", emoji="✈️"),
        ]
        
        super().__init__(
            placeholder="Select an aircraft...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        selected_aircraft = self.values[0]
        
        # Ask for departure airport
        embed = discord.Embed(
            title="🛫 Departure Airport",
            description="Please enter the **3-letter IATA code** of your departure airport.\n\nExample: `SYD` for Sydney, `MEL` for Melbourne",
            color=discord.Color.green()
        )
        embed.add_field(name="Airline", value=f"⭐ {self.airline}", inline=True)
        embed.add_field(name="Aircraft", value=f"✈️ {selected_aircraft}", inline=True)
        embed.set_footer(text="Type the 3-letter airport code in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Store the flight data and wait for IATA code
        flight_data = {
            "airline": self.airline,
            "aircraft": selected_aircraft,
            "author": self.author,
            "channel": interaction.channel,
            "stage": "departure_iata"
        }
        
        # Register the wait for message
        self.bot.dispatch("flight_awaiting_input", flight_data)


class QantasAircraftDropdown(discord.ui.Select):
    """Dropdown menu for Qantas aircraft"""
    
    def __init__(self, author, airline, bot):
        self.author = author
        self.airline = airline
        self.bot = bot
        
        options = [
            discord.SelectOption(label="Bombardier Dash 8 Q400", emoji="✈️"),
            discord.SelectOption(label="Boeing 737-800", emoji="✈️"),
            discord.SelectOption(label="Airbus A330-200", emoji="✈️"),
            discord.SelectOption(label="Airbus A330-300", emoji="✈️"),
            discord.SelectOption(label="Boeing 787-9", emoji="✈️"),
            discord.SelectOption(label="Airbus A380", emoji="✈️"),
        ]
        
        super().__init__(
            placeholder="Select an aircraft...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        selected_aircraft = self.values[0]
        
        # Ask for departure airport
        embed = discord.Embed(
            title="🛫 Departure Airport",
            description="Please enter the **3-letter IATA code** of your departure airport.\n\nExample: `SYD` for Sydney, `MEL` for Melbourne",
            color=discord.Color.red()
        )
        embed.add_field(name="Airline", value=f"🦘 {self.airline}", inline=True)
        embed.add_field(name="Aircraft", value=f"✈️ {selected_aircraft}", inline=True)
        embed.set_footer(text="Type the 3-letter airport code in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Store the flight data and wait for IATA code
        flight_data = {
            "airline": self.airline,
            "aircraft": selected_aircraft,
            "author": self.author,
            "channel": interaction.channel,
            "stage": "departure_iata"
        }
        
        # Register the wait for message
        self.bot.dispatch("flight_awaiting_input", flight_data)


class FlightDataHandler:
    """Handles storing flight planning data temporarily"""
    
    def __init__(self):
        self.active_sessions = {}
    
    def start_session(self, user_id, data):
        self.active_sessions[user_id] = data
    
    def get_session(self, user_id):
        return self.active_sessions.get(user_id)
    
    def update_session(self, user_id, key, value):
        if user_id in self.active_sessions:
            self.active_sessions[user_id][key] = value
    
    def end_session(self, user_id):
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]


# Initialize handler
flight_handler = FlightDataHandler()


class FlightPlannerCog(commands.Cog):
    """Main cog that includes message listener"""
    
    def __init__(self, bot):
        self.bot = bot
        self.flight_planner = FlightPlanner(bot)
    
    @commands.Cog.listener()
    async def on_flight_awaiting_input(self, flight_data):
        """Handle when we're waiting for user input"""
        flight_handler.start_session(flight_data["author"].id, flight_data)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for user input"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if this user has an active flight planning session
        session = flight_handler.get_session(message.author.id)
        if not session:
            return
        
        # Check if message is in the correct channel
        if message.channel.id != session["channel"].id:
            return
        
        # Handle based on current stage
        stage = session.get("stage")
        
        if stage == "departure_iata":
            await self.handle_departure_iata(message, session)
        elif stage == "arrival_iata":
            await self.handle_arrival_iata(message, session)
        elif stage == "departure_time":
            await self.handle_departure_time(message, session)
    
    async def handle_departure_iata(self, message, session):
        """Handle departure IATA code input"""
        iata_code = message.content.strip().upper()
        
        # Validate it's 3 letters
        if len(iata_code) != 3 or not iata_code.isalpha():
            embed = discord.Embed(
                description="❌ Please enter a valid 3-letter IATA airport code (e.g., SYD, MEL, BNE)",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=10)
            return
        
        # Search for airport information
        await message.channel.trigger_typing()
        
        airport_info = await self.lookup_airport(iata_code)
        
        if not airport_info:
            embed = discord.Embed(
                description=f"❌ Could not find an airport with code **{iata_code}**. Please try again.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
        
        # Ask for confirmation
        embed = discord.Embed(
            title="✅ Departure Airport Found!",
            description=f"Is this the correct departure airport?\n\n**{airport_info['name']}**\n`{airport_info['code']}`",
            color=discord.Color.blue()
        )
        
        if airport_info.get('city'):
            embed.add_field(name="City", value=airport_info['city'], inline=True)
        if airport_info.get('country'):
            embed.add_field(name="Country", value=airport_info['country'], inline=True)
        
        embed.set_footer(text="Confirm below")
        
        # Create confirmation view
        view = DepartureAirportConfirmationView(message.author, session, iata_code, airport_info)
        await message.channel.send(embed=embed, view=view)
    
    async def handle_arrival_iata(self, message, session):
        """Handle arrival IATA code input"""
        iata_code = message.content.strip().upper()
        
        # Validate it's 3 letters
        if len(iata_code) != 3 or not iata_code.isalpha():
            embed = discord.Embed(
                description="❌ Please enter a valid 3-letter IATA airport code (e.g., SYD, MEL, BNE)",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=10)
            return
        
        # Search for airport information
        await message.channel.trigger_typing()
        
        airport_info = await self.lookup_airport(iata_code)
        
        if not airport_info:
            embed = discord.Embed(
                description=f"❌ Could not find an airport with code **{iata_code}**. Please try again.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
        
        # Ask for confirmation
        embed = discord.Embed(
            title="✅ Arrival Airport Found!",
            description=f"Is this the correct arrival airport?\n\n**{airport_info['name']}**\n`{airport_info['code']}`",
            color=discord.Color.blue()
        )
        
        if airport_info.get('city'):
            embed.add_field(name="City", value=airport_info['city'], inline=True)
        if airport_info.get('country'):
            embed.add_field(name="Country", value=airport_info['country'], inline=True)
        
        embed.set_footer(text="Confirm below")
        
        # Create confirmation view
        view = ArrivalAirportConfirmationView(message.author, session, iata_code, airport_info)
        await message.channel.send(embed=embed, view=view)
    
    async def handle_departure_time(self, message, session):
        """Handle departure time input"""
        time_input = message.content.strip()
        
        # Try to parse the time - accept formats like "14:30", "2:30 PM", "1430"
        sydney_tz = pytz.timezone('Australia/Sydney')
        
        try:
            # Get current Sydney time
            current_sydney = datetime.now(sydney_tz)
            
            # Try various time formats
            time_obj = None
            
            # Format: HH:MM or H:MM
            if ':' in time_input:
                time_parts = time_input.replace(' ', '').upper()
                
                # Handle AM/PM
                is_pm = 'PM' in time_parts
                is_am = 'AM' in time_parts
                time_parts = time_parts.replace('AM', '').replace('PM', '')
                
                if ':' in time_parts:
                    hours, minutes = time_parts.split(':')
                    hours = int(hours)
                    minutes = int(minutes)
                    
                    # Convert 12-hour to 24-hour
                    if is_pm and hours != 12:
                        hours += 12
                    elif is_am and hours == 12:
                        hours = 0
                    
                    time_obj = current_sydney.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            # Format: HHMM
            elif len(time_input) == 4 and time_input.isdigit():
                hours = int(time_input[:2])
                minutes = int(time_input[2:])
                time_obj = current_sydney.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            if not time_obj or time_obj.hour > 23 or time_obj.minute > 59:
                raise ValueError("Invalid time")
            
            # Create confirmation with Discord timestamp
            timestamp = int(time_obj.timestamp())
            
            embed = discord.Embed(
                title="🕐 Confirm Departure Time",
                description=f"Is this the correct departure time?\n\n**Sydney Time:** <t:{timestamp}:F>\n**Relative:** <t:{timestamp}:R>",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Confirm below")
            
            view = DepartureTimeConfirmationView(message.author, session, time_obj, timestamp)
            await message.channel.send(embed=embed, view=view)
            
        except (ValueError, IndexError):
            embed = discord.Embed(
                description="❌ Invalid time format. Please enter time in one of these formats:\n• `14:30` (24-hour)\n• `2:30 PM` (12-hour)\n• `1430` (24-hour, no colon)",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
    
    async def lookup_airport(self, iata_code):
        """Look up airport information by IATA code"""
        try:
            # Use AirLabs API (free tier available)
            url = f"https://airlabs.co/api/v9/airports?iata_code={iata_code}&api_key=demo"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('response') and len(data['response']) > 0:
                            airport = data['response'][0]
                            return {
                                'code': iata_code,
                                'name': airport.get('name', 'Unknown Airport'),
                                'city': airport.get('city', ''),
                                'country': airport.get('country_code', '')
                            }
            
            # Fallback: Use a basic hardcoded list for common airports
            common_airports = {
                'SYD': {'name': 'Sydney Kingsford Smith International Airport', 'city': 'Sydney', 'country': 'Australia'},
                'MEL': {'name': 'Melbourne Airport', 'city': 'Melbourne', 'country': 'Australia'},
                'BNE': {'name': 'Brisbane Airport', 'city': 'Brisbane', 'country': 'Australia'},
                'PER': {'name': 'Perth Airport', 'city': 'Perth', 'country': 'Australia'},
                'ADL': {'name': 'Adelaide Airport', 'city': 'Adelaide', 'country': 'Australia'},
                'CNS': {'name': 'Cairns Airport', 'city': 'Cairns', 'country': 'Australia'},
                'OOL': {'name': 'Gold Coast Airport', 'city': 'Gold Coast', 'country': 'Australia'},
                'CBR': {'name': 'Canberra Airport', 'city': 'Canberra', 'country': 'Australia'},
                'DRW': {'name': 'Darwin International Airport', 'city': 'Darwin', 'country': 'Australia'},
                'HBA': {'name': 'Hobart Airport', 'city': 'Hobart', 'country': 'Australia'},
                'LST': {'name': 'Launceston Airport', 'city': 'Launceston', 'country': 'Australia'},
                'ASP': {'name': 'Alice Springs Airport', 'city': 'Alice Springs', 'country': 'Australia'},
                'LHR': {'name': 'London Heathrow Airport', 'city': 'London', 'country': 'United Kingdom'},
                'LAX': {'name': 'Los Angeles International Airport', 'city': 'Los Angeles', 'country': 'United States'},
                'JFK': {'name': 'John F. Kennedy International Airport', 'city': 'New York', 'country': 'United States'},
                'SIN': {'name': 'Singapore Changi Airport', 'city': 'Singapore', 'country': 'Singapore'},
                'DXB': {'name': 'Dubai International Airport', 'city': 'Dubai', 'country': 'United Arab Emirates'},
                'HKG': {'name': 'Hong Kong International Airport', 'city': 'Hong Kong', 'country': 'Hong Kong'},
                'NRT': {'name': 'Narita International Airport', 'city': 'Tokyo', 'country': 'Japan'},
                'AKL': {'name': 'Auckland Airport', 'city': 'Auckland', 'country': 'New Zealand'},
                'CHC': {'name': 'Christchurch Airport', 'city': 'Christchurch', 'country': 'New Zealand'},
                'WLG': {'name': 'Wellington Airport', 'city': 'Wellington', 'country': 'New Zealand'},
            }
            
            if iata_code in common_airports:
                airport_data = common_airports[iata_code]
                return {
                    'code': iata_code,
                    'name': airport_data['name'],
                    'city': airport_data['city'],
                    'country': airport_data['country']
                }
            
            return None
            
        except Exception as e:
            print(f"Error looking up airport: {e}")
            return None
    
    @commands.command(name="plan")
    async def plan_flight(self, ctx):
        """Start planning a flight - choose between Qantas or Jetstar"""
        await self.flight_planner.plan_flight(ctx)


class DepartureAirportConfirmationView(discord.ui.View):
    """View for confirming the departure airport"""
    
    def __init__(self, author, session, iata_code, airport_info):
        super().__init__(timeout=60)
        self.author = author
        self.session = session
        self.iata_code = iata_code
        self.airport_info = airport_info
    
    @discord.ui.button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save departure airport and ask for arrival
        flight_handler.update_session(self.author.id, "departure_code", self.iata_code)
        flight_handler.update_session(self.author.id, "departure_name", self.airport_info['name'])
        flight_handler.update_session(self.author.id, "stage", "arrival_iata")
        
        embed = discord.Embed(
            title="🛬 Arrival Airport",
            description="Please enter the **3-letter IATA code** of your arrival airport.\n\nExample: `MEL` for Melbourne, `BNE` for Brisbane",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Type the 3-letter airport code in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @discord.ui.button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🛫 Departure Airport",
            description="Please enter the **3-letter IATA code** of your departure airport.\n\nExample: `SYD` for Sydney, `MEL` for Melbourne",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Type the 3-letter airport code in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class ArrivalAirportConfirmationView(discord.ui.View):
    """View for confirming the arrival airport"""
    
    def __init__(self, author, session, iata_code, airport_info):
        super().__init__(timeout=60)
        self.author = author
        self.session = session
        self.iata_code = iata_code
        self.airport_info = airport_info
    
    @discord.ui.button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save arrival airport and ask for departure time
        flight_handler.update_session(self.author.id, "arrival_code", self.iata_code)
        flight_handler.update_session(self.author.id, "arrival_name", self.airport_info['name'])
        flight_handler.update_session(self.author.id, "stage", "departure_time")
        
        # Get current Sydney time for reference
        sydney_tz = pytz.timezone('Australia/Sydney')
        current_sydney = datetime.now(sydney_tz)
        sydney_timestamp = int(current_sydney.timestamp())
        
        embed = discord.Embed(
            title="🕐 Departure Time",
            description=f"Please enter your departure time in **Sydney time** (AEDT).\n\n**Current Sydney time:** <t:{sydney_timestamp}:t>",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Accepted Formats",
            value="• `14:30` (24-hour)\n• `2:30 PM` (12-hour)\n• `1430` (no colon)",
            inline=False
        )
        embed.set_footer(text="Type the departure time in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


async def setup(bot):
    await bot.add_cog(FlightPlannerCog(bot))False
        )
        embed.set_footer(text="Type the departure time in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @discord.ui.button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🛬 Arrival Airport",
            description="Please enter the **3-letter IATA code** of your arrival airport.\n\nExample: `MEL` for Melbourne, `BNE` for Brisbane",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Type the 3-letter airport code in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class DepartureTimeConfirmationView(discord.ui.View):
    """View for confirming the departure time"""
    
    def __init__(self, author, session, time_obj, timestamp):
        super().__init__(timeout=60)
        self.author = author
        self.session = session
        self.time_obj = time_obj
        self.timestamp = timestamp
    
    @discord.ui.button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save departure time
        flight_handler.update_session(self.author.id, "departure_time", self.time_obj)
        flight_handler.update_session(self.author.id, "departure_timestamp", self.timestamp)
        
        # Get session data
        session = flight_handler.get_session(self.author.id)
        
        # Create final summary
        color = discord.Color.red() if session["airline"] == "Qantas" else discord.Color.green()
        emoji = "🦘" if session["airline"] == "Qantas" else "⭐"
        
        embed = discord.Embed(
            title="✅ Flight Plan Complete!",
            description="Your flight has been successfully planned!",
            color=color
        )
        embed.add_field(name="Airline", value=f"{emoji} {session['airline']}", inline=True)
        embed.add_field(name="Aircraft", value=f"✈️ {session['aircraft']}", inline=True)
        embed.add_field(name="‎", value="‎", inline=True)  # Spacer
        embed.add_field(
            name="Route", 
            value=f"🛫 {session['departure_code']} → 🛬 {session['arrival_code']}", 
            inline=False
        )
        embed.add_field(
            name="Departure", 
            value=f"{session['departure_name']}", 
            inline=False
        )
        embed.add_field(
            name="Arrival", 
            value=f"{session['arrival_name']}", 
            inline=False
        )
        embed.add_field(
            name="Departure Time (Sydney)", 
            value=f"<t:{self.timestamp}:F>\n<t:{self.timestamp}:R>", 
            inline=False
        )
        embed.set_footer(text="Flight planning session completed")
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # End the session
        flight_handler.end_session(self.author.id)
        self.stop()
    
    @discord.ui.button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Get current Sydney time for reference
        sydney_tz = pytz.timezone('Australia/Sydney')
        current_sydney = datetime.now(sydney_tz)
        sydney_timestamp = int(current_sydney.timestamp())
        
        embed = discord.Embed(
            title="🕐 Departure Time",
            description=f"Please enter your departure time in **Sydney time** (AEDT).\n\n**Current Sydney time:** <t:{sydney_timestamp}:t>",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Accepted Formats",
            value="• `14:30` (24-hour)\n• `2:30 PM` (12-hour)\n• `1430` (no colon)",
            inline=False
        )
        embed.set_footer(text="Type the departure time in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


async def setup(bot):
    await bot.add_cog(FlightPlannerCog(bot))
