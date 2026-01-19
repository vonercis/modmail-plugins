from discord.ext import commands
import discord
import aiohttp
import pytz
from datetime import datetime
from confirmations import (
    DepartureAirportConfirmationView,
    ArrivalAirportConfirmationView,
    DepartureTimeConfirmationView,
    DepartureDateConfirmationView
)


class FlightPlannerCog(commands.Cog):
    """Main cog that includes message listener"""
    
    def __init__(self, bot, flight_handler):
        self.bot = bot
        self.flight_handler = flight_handler
    
    @commands.Cog.listener()
    async def on_flight_awaiting_input(self, flight_data):
        """Handle when we're waiting for user input"""
        self.flight_handler.start_session(flight_data["author"].id, flight_data)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for user input"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore messages that start with common command prefixes
        if message.content.startswith(('.', '?', '!', '/', '$')):
        
        # Handle based on current stage
        stage = session.get("stage")
        
        if stage == "departure_iata":
            await self.handle_departure_iata(message, session)
        elif stage == "arrival_iata":
            await self.handle_arrival_iata(message, session)
        elif stage == "departure_time":
            await self.handle_departure_time(message, session)
        elif stage == "departure_date":
            await self.handle_departure_date(message, session)
    
    async def handle_departure_iata(self, message, session):
        """Handle departure IATA code input"""
        iata_code = message.content.strip().upper()
        
        print(f"DEBUG: Received IATA code: '{iata_code}', length: {len(iata_code)}, is alpha: {iata_code.isalpha()}")
        
        # Validate it's 3 letters
        if len(iata_code) != 3 or not iata_code.isalpha():
            embed = discord.Embed(
                description="❌ Please enter a valid 3-letter IATA airport code (e.g., SYD, MEL, BNE)",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=10)
            return
        
        # Search for airport information
        async with message.channel.typing():
            airport_info = await self.lookup_airport(iata_code)
        
        if not airport_info:
            embed = discord.Embed(
                description=f"❌ Could not find an airport with code **{iata_code}**. Please try again.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
    
    async def handle_departure_date(self, message, session):
        """Handle departure date input"""
        date_input = message.content.strip().lower()
        
        sydney_tz = pytz.timezone('Australia/Sydney')
        current_sydney = datetime.now(sydney_tz)
        
        try:
            date_obj = None
            
            # Handle "today" or "tomorrow"
            if date_input == "today":
                date_obj = current_sydney.date()
            elif date_input == "tomorrow":
                date_obj = (current_sydney + pytz.timezone('Australia/Sydney').localize(datetime.now()).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0) - current_sydney.replace(tzinfo=None) + datetime.timedelta(days=1)).date()
                # Simpler approach
                from datetime import timedelta
                date_obj = (current_sydney + timedelta(days=1)).date()
            else:
                # Try various date formats
                # Format: DD/MM/YYYY or DD-MM-YYYY
                for separator in ['/', '-', ' ']:
                    if separator in date_input:
                        parts = date_input.split(separator)
                        if len(parts) == 3:
                            try:
                                day = int(parts[0])
                                month = int(parts[1])
                                year = int(parts[2])
                                
                                # Handle 2-digit years
                                if year < 100:
                                    year += 2000
                                
                                date_obj = datetime(year, month, day, tzinfo=sydney_tz).date()
                                break
                            except (ValueError, IndexError):
                                continue
                
                # Format: DD Mon YYYY (e.g., 25 Jan 2026)
                if not date_obj:
                    try:
                        date_obj = datetime.strptime(date_input.title(), "%d %b %Y").date()
                    except ValueError:
                        pass
            
            if not date_obj:
                raise ValueError("Invalid date format")
            
            # Validate date is not in the past
            if date_obj < current_sydney.date():
                embed = discord.Embed(
                    description="❌ The departure date cannot be in the past. Please enter a valid future date.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                return
            
            # Get the saved time from session
            time_obj = session.get("departure_time")
            
            # Combine date and time
            combined_datetime = sydney_tz.localize(datetime.combine(
                date_obj,
                time_obj.time()
            ))
            combined_timestamp = int(combined_datetime.timestamp())
            
            # Show confirmation
            embed = discord.Embed(
                title="📅 Confirm Departure Date",
                description=f"Is this the correct departure date and time?\n\n**Full Date & Time:** <t:{combined_timestamp}:F>\n**Relative:** <t:{combined_timestamp}:R>",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Confirm below")
            
            view = DepartureDateConfirmationView(message.author, self.flight_handler, date_obj, combined_timestamp)
            await message.channel.send(embed=embed, view=view)
            
        except (ValueError, AttributeError) as e:
            embed = discord.Embed(
                description="❌ Invalid date format. Please enter date in one of these formats:\n• `25/01/2026` (DD/MM/YYYY)\n• `25-01-2026` (DD-MM-YYYY)\n• `25 Jan 2026`\n• `today` or `tomorrow`",
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
        view = DepartureAirportConfirmationView(message.author, self.flight_handler, iata_code, airport_info)
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
        async with message.channel.typing():
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
        view = ArrivalAirportConfirmationView(message.author, self.flight_handler, iata_code, airport_info)
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
            
            view = DepartureTimeConfirmationView(message.author, self.flight_handler, time_obj, timestamp)
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
)):
            return
        
        # Check if this user has an active flight planning session
        session = self.flight_handler.get_session(message.author.id)
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
        elif stage == "departure_date":
            await self.handle_departure_date(message, session)
    
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
        async with message.channel.typing():
            airport_info = await self.lookup_airport(iata_code)
        
        if not airport_info:
            embed = discord.Embed(
                description=f"❌ Could not find an airport with code **{iata_code}**. Please try again.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
    
    async def handle_departure_date(self, message, session):
        """Handle departure date input"""
        date_input = message.content.strip().lower()
        
        sydney_tz = pytz.timezone('Australia/Sydney')
        current_sydney = datetime.now(sydney_tz)
        
        try:
            date_obj = None
            
            # Handle "today" or "tomorrow"
            if date_input == "today":
                date_obj = current_sydney.date()
            elif date_input == "tomorrow":
                date_obj = (current_sydney + pytz.timezone('Australia/Sydney').localize(datetime.now()).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0) - current_sydney.replace(tzinfo=None) + datetime.timedelta(days=1)).date()
                # Simpler approach
                from datetime import timedelta
                date_obj = (current_sydney + timedelta(days=1)).date()
            else:
                # Try various date formats
                # Format: DD/MM/YYYY or DD-MM-YYYY
                for separator in ['/', '-', ' ']:
                    if separator in date_input:
                        parts = date_input.split(separator)
                        if len(parts) == 3:
                            try:
                                day = int(parts[0])
                                month = int(parts[1])
                                year = int(parts[2])
                                
                                # Handle 2-digit years
                                if year < 100:
                                    year += 2000
                                
                                date_obj = datetime(year, month, day, tzinfo=sydney_tz).date()
                                break
                            except (ValueError, IndexError):
                                continue
                
                # Format: DD Mon YYYY (e.g., 25 Jan 2026)
                if not date_obj:
                    try:
                        date_obj = datetime.strptime(date_input.title(), "%d %b %Y").date()
                    except ValueError:
                        pass
            
            if not date_obj:
                raise ValueError("Invalid date format")
            
            # Validate date is not in the past
            if date_obj < current_sydney.date():
                embed = discord.Embed(
                    description="❌ The departure date cannot be in the past. Please enter a valid future date.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                return
            
            # Get the saved time from session
            time_obj = session.get("departure_time")
            
            # Combine date and time
            combined_datetime = sydney_tz.localize(datetime.combine(
                date_obj,
                time_obj.time()
            ))
            combined_timestamp = int(combined_datetime.timestamp())
            
            # Show confirmation
            embed = discord.Embed(
                title="📅 Confirm Departure Date",
                description=f"Is this the correct departure date and time?\n\n**Full Date & Time:** <t:{combined_timestamp}:F>\n**Relative:** <t:{combined_timestamp}:R>",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Confirm below")
            
            view = DepartureDateConfirmationView(message.author, self.flight_handler, date_obj, combined_timestamp)
            await message.channel.send(embed=embed, view=view)
            
        except (ValueError, AttributeError) as e:
            embed = discord.Embed(
                description="❌ Invalid date format. Please enter date in one of these formats:\n• `25/01/2026` (DD/MM/YYYY)\n• `25-01-2026` (DD-MM-YYYY)\n• `25 Jan 2026`\n• `today` or `tomorrow`",
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
        view = DepartureAirportConfirmationView(message.author, self.flight_handler, iata_code, airport_info)
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
        async with message.channel.typing():
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
        view = ArrivalAirportConfirmationView(message.author, self.flight_handler, iata_code, airport_info)
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
            
            view = DepartureTimeConfirmationView(message.author, self.flight_handler, time_obj, timestamp)
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
