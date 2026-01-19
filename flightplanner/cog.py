from discord.ext import commands
import discord
import aiohttp
import pytz
from datetime import datetime
from confirmations import (
    DepartureAirportConfirmationView,
    ArrivalAirportConfirmationView,
    DepartureTimeConfirmationView
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
