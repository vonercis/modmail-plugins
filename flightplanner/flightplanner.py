from discord.ext import commands
import discord
from .views import FlightSelectionView
from .handler import FlightDataHandler
from .cog import FlightPlannerCog as FPC

# Initialize handler
flight_handler = FlightDataHandler()


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


async def setup(bot):
    # Register both the command cog and the listener cog
    await bot.add_cog(FlightPlanner(bot))
    await bot.add_cog(FPC(bot, flight_handler))
