from discord.ext import commands
import discord
import sys
import os

# Add the plugin directory to the path
plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# Import other modules
from views import FlightSelectionView
from handler import FlightDataHandler
from cog import FlightPlannerCog

# Initialize handler
flight_handler = FlightDataHandler()


class FlightPlannerCommands(commands.Cog):
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


async def setup(bot):
    # Register both cogs with different names
    await bot.add_cog(FlightPlannerCommands(bot))
    await bot.add_cog(FlightPlannerCog(bot, flight_handler))
