from discord.ext import commands
import discord


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
        view = FlightSelectionView(ctx.author)
        
        # Send the message with buttons
        await ctx.send(embed=embed, view=view)


class FlightSelectionView(discord.ui.View):
    """View with buttons for selecting Qantas or Jetstar"""
    
    def __init__(self, author):
        super().__init__(timeout=60)  # 60 second timeout
        self.author = author
    
    @discord.ui.button(label="Qantas", style=discord.ButtonStyle.red, emoji="🦘")
    async def qantas_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the person clicking is the person who ran the command
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Create response embed for Qantas
        embed = discord.Embed(
            title="🦘 Qantas Flight Selected",
            description="You've selected **Qantas** for your flight planning!",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Next Steps", 
            value="Please provide your flight details or let me know how I can assist you further.",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @discord.ui.button(label="Jetstar", style=discord.ButtonStyle.green, emoji="⭐")
    async def jetstar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the person clicking is the person who ran the command
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Create response embed for Jetstar
        embed = discord.Embed(
            title="⭐ Jetstar Flight Selected",
            description="You've selected **Jetstar** for your flight planning!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Next Steps", 
            value="Please provide your flight details or let me know how I can assist you further.",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    async def on_timeout(self):
        """Called when the view times out (60 seconds of no interaction)"""
        # Disable all buttons when timeout occurs
        for item in self.children:
            item.disabled = True


async def setup(bot):
    await bot.add_cog(FlightPlanner(bot))
