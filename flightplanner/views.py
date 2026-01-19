import discord
from discord.ui import View, Select, button


class FlightSelectionView(View):
    """View with buttons for selecting Qantas or Jetstar"""
    
    def __init__(self, author, bot):
        super().__init__(timeout=120)
        self.author = author
        self.bot = bot
    
    @button(label="Qantas", style=discord.ButtonStyle.red, emoji="🦘")
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
    
    @button(label="Jetstar", style=discord.ButtonStyle.green, emoji="⭐")
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


class AircraftSelectionView(View):
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


class JetstarAircraftDropdown(Select):
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


class QantasAircraftDropdown(Select):
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
