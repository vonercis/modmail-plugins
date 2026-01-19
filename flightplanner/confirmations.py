import discord
from discord.ui import View, button
import pytz
from datetime import datetime


class DepartureAirportConfirmationView(View):
    """View for confirming the departure airport"""
    
    def __init__(self, author, handler, iata_code, airport_info):
        super().__init__(timeout=60)
        self.author = author
        self.handler = handler
        self.iata_code = iata_code
        self.airport_info = airport_info
    
    @button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save departure airport and ask for arrival
        self.handler.update_session(self.author.id, "departure_code", self.iata_code)
        self.handler.update_session(self.author.id, "departure_name", self.airport_info['name'])
        self.handler.update_session(self.author.id, "stage", "arrival_iata")
        
        embed = discord.Embed(
            title="🛬 Arrival Airport",
            description="Please enter the **3-letter IATA code** of your arrival airport.\n\nExample: `MEL` for Melbourne, `BNE` for Brisbane",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Type the 3-letter airport code in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
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


class ArrivalAirportConfirmationView(View):
    """View for confirming the arrival airport"""
    
    def __init__(self, author, handler, iata_code, airport_info):
        super().__init__(timeout=60)
        self.author = author
        self.handler = handler
        self.iata_code = iata_code
        self.airport_info = airport_info
    
    @button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save arrival airport and ask for departure time
        self.handler.update_session(self.author.id, "arrival_code", self.iata_code)
        self.handler.update_session(self.author.id, "arrival_name", self.airport_info['name'])
        self.handler.update_session(self.author.id, "stage", "departure_time")
        
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
    
    @button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
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


class DepartureTimeConfirmationView(View):
    """View for confirming the departure time"""
    
    def __init__(self, author, handler, time_obj, timestamp):
        super().__init__(timeout=60)
        self.author = author
        self.handler = handler
        self.time_obj = time_obj
        self.timestamp = timestamp
    
    @button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save departure time and move to date selection
        self.handler.update_session(self.author.id, "departure_time", self.time_obj)
        self.handler.update_session(self.author.id, "departure_timestamp", self.timestamp)
        self.handler.update_session(self.author.id, "stage", "departure_date")
        
        # Get current Sydney time for reference
        sydney_tz = pytz.timezone('Australia/Sydney')
        current_sydney = datetime.now(sydney_tz)
        
        embed = discord.Embed(
            title="📅 Departure Date",
            description="Please enter your departure date.\n\n**Current date:** " + current_sydney.strftime("%d/%m/%Y"),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Accepted Formats",
            value="• `25/01/2026` (DD/MM/YYYY)\n• `25-01-2026` (DD-MM-YYYY)\n• `25 Jan 2026`\n• `today` or `tomorrow`",
            inline=False
        )
        embed.set_footer(text="Type the departure date in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class DepartureDateConfirmationView(View):
    """View for confirming the departure date"""
    
    def __init__(self, author, handler, date_obj, combined_timestamp):
        super().__init__(timeout=60)
        self.author = author
        self.handler = handler
        self.date_obj = date_obj
        self.combined_timestamp = combined_timestamp
    
    @button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save departure date
        self.handler.update_session(self.author.id, "departure_date", self.date_obj)
        self.handler.update_session(self.author.id, "combined_timestamp", self.combined_timestamp)
        
        # Get session data
        session = self.handler.get_session(self.author.id)
        
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
            name="Departure Date & Time (Sydney)", 
            value=f"<t:{self.combined_timestamp}:F>\n<t:{self.combined_timestamp}:R>", 
            inline=False
        )
        embed.set_footer(text="Flight planning session completed")
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # End the session
        self.handler.end_session(self.author.id)
        self.stop()
    
    @button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
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
        
        embed = discord.Embed(
            title="📅 Departure Date",
            description="Please enter your departure date.\n\n**Current date:** " + current_sydney.strftime("%d/%m/%Y"),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Accepted Formats",
            value="• `25/01/2026` (DD/MM/YYYY)\n• `25-01-2026` (DD-MM-YYYY)\n• `25 Jan 2026`\n• `today` or `tomorrow`",
            inline=False
        )
        embed.set_footer(text="Type the departure date in chat")
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
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
