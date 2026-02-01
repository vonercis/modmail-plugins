"""
Qantas Frequent Flyer Plugin for Modmail

A comprehensive plugin for managing Qantas Frequent Flyer memberships with MongoDB
and Roblox integration. Compatible with modmail-dev/Modmail bot.

Author: Custom Plugin
Version: 1.0.0
"""

import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import random
from typing import Optional


class QantasFrequentFlyer(commands.Cog):
    """Qantas Frequent Flyer membership management system"""
    
    # Tier configuration matching real Qantas system
    TIERS = {
        'BRONZE': {
            'name': 'Bronze',
            'credits_required': 0,
            'oneworld': 'None',
            'color': 0xCD7F32,
            'benefits': [
                'Earn Qantas Points',
                'Bonus Points on Qantas flights',
                'Access to Qantas Frequent Flyer partners'
            ]
        },
        'SILVER': {
            'name': 'Silver',
            'credits_required': 300,
            'oneworld': 'Ruby',
            'color': 0xC0C0C0,
            'benefits': [
                'Priority check-in',
                'Priority boarding',
                'Extra baggage allowance',
                'Oneworld Ruby benefits',
                'Lounge access when flying internationally'
            ]
        },
        'GOLD': {
            'name': 'Gold',
            'credits_required': 700,
            'oneworld': 'Sapphire',
            'color': 0xFFD700,
            'benefits': [
                'Qantas Club lounge access',
                'Priority boarding and baggage handling',
                'Increased baggage allowance',
                'Oneworld Sapphire benefits',
                'Complimentary upgrades (subject to availability)'
            ]
        },
        'PLATINUM': {
            'name': 'Platinum',
            'credits_required': 1400,
            'oneworld': 'Emerald',
            'color': 0xE5E4E2,
            'benefits': [
                'Qantas First Lounge access',
                'Premium boarding',
                'Extra baggage allowance',
                'Oneworld Emerald benefits',
                'Complimentary Qantas Club membership',
                'Priority waitlist and standby'
            ]
        },
        'PLATINUM_ONE': {
            'name': 'Platinum One',
            'credits_required': 3600,
            'oneworld': 'Emerald',
            'color': 0x1C1C1C,
            'benefits': [
                'All Platinum benefits',
                'Dedicated concierge service',
                'Enhanced upgrade priority',
                'Access to invitation-only events',
                'Platinum One status gift',
                'Extended status credits validity'
            ]
        }
    }
    
    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.bot.loop.create_task(self._setup_database())
    
    async def _setup_database(self):
        """Initialize MongoDB connection"""
        # Wait for bot to be ready
        await self.bot.wait_until_ready()
        
        # Use the bot's existing MongoDB connection
        if hasattr(self.bot, 'db'):
            self.db = self.bot.db.db  # Get the actual database object
            self.bot.logger.info("Qantas FF: Using bot's MongoDB connection")
        else:
            # Fallback: create own connection
            mongo_uri = self.bot.config.get('qantas_mongo_uri') or self.bot.config.get('connection_uri')
            if mongo_uri:
                client = AsyncIOMotorClient(mongo_uri)
                self.db = client.modmail_qantas
                self.bot.logger.info("Qantas FF: Created separate MongoDB connection")
            else:
                self.bot.logger.error("Qantas FF: No MongoDB connection available!")
    
    @staticmethod
    def generate_membership_number():
        """Generate a Qantas-style membership number"""
        timestamp = str(int(datetime.utcnow().timestamp()))[-8:]
        random_part = f"{random.randint(0, 9999):04d}"
        return f"QF{timestamp}{random_part}"
    
    @staticmethod
    def calculate_tier(status_credits: int) -> dict:
        """Calculate tier based on status credits"""
        tiers = QantasFrequentFlyer.TIERS
        
        if status_credits >= tiers['PLATINUM_ONE']['credits_required']:
            return {
                'tier': tiers['PLATINUM_ONE']['name'],
                'oneworld': tiers['PLATINUM_ONE']['oneworld']
            }
        elif status_credits >= tiers['PLATINUM']['credits_required']:
            return {
                'tier': tiers['PLATINUM']['name'],
                'oneworld': tiers['PLATINUM']['oneworld']
            }
        elif status_credits >= tiers['GOLD']['credits_required']:
            return {
                'tier': tiers['GOLD']['name'],
                'oneworld': tiers['GOLD']['oneworld']
            }
        elif status_credits >= tiers['SILVER']['credits_required']:
            return {
                'tier': tiers['SILVER']['name'],
                'oneworld': tiers['SILVER']['oneworld']
            }
        
        return {
            'tier': tiers['BRONZE']['name'],
            'oneworld': tiers['BRONZE']['oneworld']
        }
    
    @staticmethod
    def get_next_tier_info(current_credits: int) -> Optional[dict]:
        """Get information about the next tier"""
        tiers = QantasFrequentFlyer.TIERS
        tier_order = ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'PLATINUM_ONE']
        
        for tier_key in tier_order:
            tier = tiers[tier_key]
            if current_credits < tier['credits_required']:
                return {
                    'name': tier['name'],
                    'credits_needed': tier['credits_required'] - current_credits,
                    'total_required': tier['credits_required']
                }
        
        return None
    
    def get_tier_color(self, tier_name: str) -> int:
        """Get the color for a specific tier"""
        for tier in self.TIERS.values():
            if tier['name'] == tier_name:
                return tier['color']
        return self.TIERS['BRONZE']['color']
    
    def get_tier_benefits(self, tier_name: str) -> list:
        """Get benefits for a specific tier"""
        for tier in self.TIERS.values():
            if tier['name'] == tier_name:
                return tier['benefits']
        return self.TIERS['BRONZE']['benefits']
    
    async def get_member(self, discord_id: str) -> Optional[dict]:
        """Retrieve a member from the database"""
        if not self.db:
            return None
        return await self.db.frequent_flyers.find_one({'discord_id': str(discord_id)})
    
    async def create_member(self, member_data: dict) -> dict:
        """Create a new frequent flyer member"""
        if not self.db:
            raise Exception("Database not initialized")
        
        await self.db.frequent_flyers.insert_one(member_data)
        return member_data
    
    async def update_member(self, discord_id: str, update_data: dict):
        """Update a member's data"""
        if not self.db:
            raise Exception("Database not initialized")
        
        update_data['updated_at'] = datetime.utcnow()
        await self.db.frequent_flyers.update_one(
            {'discord_id': str(discord_id)},
            {'$set': update_data}
        )
    
    @commands.group(name='qff', invoke_without_command=True)
    async def qff(self, ctx):
        """Qantas Frequent Flyer commands"""
        await ctx.send_help(ctx.command)
    
    @qff.command(name='signup', aliases=['register', 'join'])
    async def qff_signup(self, ctx, first_name: str, last_name: str, email: str):
        """
        Sign up for the Qantas Frequent Flyer program
        
        **Usage:**
            {prefix}qff signup John Smith john@example.com
        """
        # Check if user already exists
        existing = await self.get_member(ctx.author.id)
        if existing:
            return await ctx.send('❌ You are already registered for Qantas Frequent Flyer!')
        
        # Create new member
        membership_number = self.generate_membership_number()
        member_data = {
            'discord_id': str(ctx.author.id),
            'roblox_id': None,
            'first_name': first_name,
            'last_name': last_name,
            'email': email.lower(),
            'membership_number': membership_number,
            'join_date': datetime.utcnow(),
            'membership_year_start': datetime.utcnow(),
            'qantas_points': 0,
            'status_credits': 0,
            'current_tier': 'Bronze',
            'oneworld_status': 'None',
            'flights': [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            await self.create_member(member_data)
            
            embed = discord.Embed(
                color=self.TIERS['BRONZE']['color'],
                title='🎉 Welcome to Qantas Frequent Flyer!',
                description=f'Congratulations {first_name} {last_name}!'
            )
            embed.add_field(name='Membership Number', value=membership_number, inline=True)
            embed.add_field(name='Current Tier', value='Bronze', inline=True)
            embed.add_field(name='Status Credits', value='0', inline=True)
            embed.add_field(name='Qantas Points', value='0', inline=True)
            embed.add_field(
                name='Join Date',
                value=datetime.utcnow().strftime('%Y-%m-%d'),
                inline=True
            )
            embed.add_field(name='\u200B', value='\u200B', inline=True)
            embed.add_field(
                name='Next Tier - Silver',
                value='Earn 300 Status Credits to unlock Silver tier and oneworld Ruby status!',
                inline=False
            )
            embed.set_footer(text=f'Use {ctx.prefix}qff status to check your account anytime')
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Qantas FF signup error: {e}")
            await ctx.send(f'❌ An error occurred during signup. Please try again.')
    
    @qff.command(name='status', aliases=['info', 'profile'])
    async def qff_status(self, ctx, member: Optional[discord.Member] = None):
        """
        Check your Qantas Frequent Flyer status
        
        **Usage:**
            {prefix}qff status
            {prefix}qff status @user
        """
        target = member or ctx.author
        member_data = await self.get_member(target.id)
        
        if not member_data:
            return await ctx.send(f'❌ {"You are" if not member else f"{member.mention} is"} not registered. Use `{ctx.prefix}qff signup` to join!')
        
        tier_color = self.get_tier_color(member_data['current_tier'])
        benefits = self.get_tier_benefits(member_data['current_tier'])
        next_tier = self.get_next_tier_info(member_data['status_credits'])
        
        embed = discord.Embed(
            color=tier_color,
            title=f"✈️ {member_data['first_name']} {member_data['last_name']} - Qantas Frequent Flyer"
        )
        
        embed.add_field(
            name='Membership Number',
            value=member_data['membership_number'],
            inline=True
        )
        embed.add_field(
            name='Current Tier',
            value=member_data['current_tier'],
            inline=True
        )
        embed.add_field(
            name='oneworld Status',
            value=member_data['oneworld_status'],
            inline=True
        )
        embed.add_field(
            name='Status Credits',
            value=str(member_data['status_credits']),
            inline=True
        )
        embed.add_field(
            name='Qantas Points',
            value=f"{member_data['qantas_points']:,}",
            inline=True
        )
        embed.add_field(
            name='Flights Taken',
            value=str(len(member_data.get('flights', []))),
            inline=True
        )
        
        if next_tier:
            embed.add_field(
                name=f"📈 Progress to {next_tier['name']}",
                value=f"{next_tier['credits_needed']} more Status Credits needed "
                      f"({member_data['status_credits']}/{next_tier['total_required']})",
                inline=False
            )
        else:
            embed.add_field(
                name='🏆 Top Tier Achieved!',
                value='You have reached Platinum One - the highest tier!',
                inline=False
            )
        
        embed.add_field(
            name='🎁 Your Benefits',
            value='\n'.join(f'• {b}' for b in benefits),
            inline=False
        )
        
        if member_data.get('roblox_id'):
            embed.add_field(
                name='🎮 Linked Accounts',
                value=f"Roblox ID: {member_data['roblox_id']}",
                inline=False
            )
        
        join_date = member_data['join_date'].strftime('%Y-%m-%d')
        year_start = member_data['membership_year_start'].strftime('%Y-%m-%d')
        embed.set_footer(
            text=f"Member since {join_date} | Membership Year: {year_start}"
        )
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    @qff.command(name='link', aliases=['linkroblox', 'roblox'])
    async def qff_link_roblox(self, ctx, roblox_id: str):
        """
        Link your Roblox account
        
        **Usage:**
            {prefix}qff link 123456789
        """
        member_data = await self.get_member(ctx.author.id)
        
        if not member_data:
            return await ctx.send(f'❌ You are not registered. Use `{ctx.prefix}qff signup` to join first!')
        
        await self.update_member(ctx.author.id, {'roblox_id': roblox_id})
        await ctx.send(f'✅ Successfully linked Roblox ID: {roblox_id} to your account!')
    
    @qff.command(name='addflight', aliases=['flight'])
    @commands.has_permissions(administrator=True)
    async def qff_add_flight(
        self, ctx,
        member: discord.Member,
        flight_number: str,
        from_airport: str,
        to_airport: str,
        status_credits: int,
        points: int,
        cabin: str
    ):
        """
        Add a flight to a member's account (Admin only)
        
        **Usage:**
            {prefix}qff addflight @user QF7 SYD LAX 140 12840 Business
        
        **Cabin classes:** Economy, Premium Economy, Business, First
        """
        valid_cabins = ['Economy', 'Premium Economy', 'Business', 'First']
        if cabin not in valid_cabins:
            return await ctx.send(f'❌ Invalid cabin class. Choose from: {", ".join(valid_cabins)}')
        
        member_data = await self.get_member(member.id)
        
        if not member_data:
            return await ctx.send(f'❌ {member.mention} is not registered.')
        
        old_tier = member_data['current_tier']
        old_credits = member_data['status_credits']
        
        # Create flight record
        flight = {
            'flight_number': flight_number.upper(),
            'from': from_airport.upper(),
            'to': to_airport.upper(),
            'date': datetime.utcnow(),
            'status_credits_earned': status_credits,
            'qantas_points_earned': points,
            'cabin_class': cabin
        }
        
        # Update member data
        new_credits = old_credits + status_credits
        new_points = member_data['qantas_points'] + points
        new_tier_info = self.calculate_tier(new_credits)
        
        flights = member_data.get('flights', [])
        flights.append(flight)
        
        await self.update_member(member.id, {
            'flights': flights,
            'status_credits': new_credits,
            'qantas_points': new_points,
            'current_tier': new_tier_info['tier'],
            'oneworld_status': new_tier_info['oneworld']
        })
        
        embed = discord.Embed(
            color=0x00FF00,
            title='✅ Flight Added Successfully'
        )
        embed.add_field(
            name='Member',
            value=f"{member_data['first_name']} {member_data['last_name']}",
            inline=True
        )
        embed.add_field(
            name='Flight',
            value=f"{flight_number.upper()} ({from_airport.upper()} → {to_airport.upper()})",
            inline=True
        )
        embed.add_field(name='Cabin', value=cabin, inline=True)
        embed.add_field(
            name='Status Credits Earned',
            value=str(status_credits),
            inline=True
        )
        embed.add_field(
            name='Points Earned',
            value=f"{points:,}",
            inline=True
        )
        embed.add_field(name='\u200B', value='\u200B', inline=True)
        embed.add_field(
            name='Total Status Credits',
            value=f"{old_credits} → {new_credits}",
            inline=True
        )
        embed.add_field(
            name='Total Points',
            value=f"{new_points:,}",
            inline=True
        )
        embed.add_field(
            name='Current Tier',
            value=new_tier_info['tier'],
            inline=True
        )
        
        if old_tier != new_tier_info['tier']:
            embed.color = self.get_tier_color(new_tier_info['tier'])
            embed.add_field(
                name='🎉 TIER UPGRADE!',
                value=f"Congratulations! {member_data['first_name']} has been upgraded "
                      f"from {old_tier} to **{new_tier_info['tier']}**!",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @qff.command(name='flights', aliases=['history'])
    async def qff_flights(self, ctx):
        """
        View your flight history
        
        **Usage:**
            {prefix}qff flights
        """
        member_data = await self.get_member(ctx.author.id)
        
        if not member_data:
            return await ctx.send(f'❌ You are not registered. Use `{ctx.prefix}qff signup` to join!')
        
        flights = member_data.get('flights', [])
        
        if not flights:
            return await ctx.send('✈️ You haven\'t taken any flights yet!')
        
        # Show most recent 10 flights
        recent_flights = flights[-10:]
        recent_flights.reverse()
        
        embed = discord.Embed(
            color=self.get_tier_color(member_data['current_tier']),
            title=f"✈️ Flight History - {member_data['first_name']} {member_data['last_name']}",
            description=f"Showing {len(recent_flights)} most recent flight(s)"
        )
        
        for flight in recent_flights:
            flight_date = flight['date'].strftime('%Y-%m-%d')
            embed.add_field(
                name=f"{flight['flight_number']} - {flight['from']} → {flight['to']}",
                value=f"Date: {flight_date}\n"
                      f"Cabin: {flight['cabin_class']}\n"
                      f"Status Credits: {flight['status_credits_earned']} | "
                      f"Points: {flight['qantas_points_earned']:,}",
                inline=False
            )
        
        embed.set_footer(text=f"Total Flights: {len(flights)}")
        
        await ctx.send(embed=embed)
    
    @qff.command(name='leaderboard', aliases=['lb', 'top'])
    async def qff_leaderboard(self, ctx, sort_by: str = 'credits'):
        """
        View the frequent flyer leaderboard
        
        **Usage:**
            {prefix}qff leaderboard
            {prefix}qff leaderboard points
        """
        if not self.db:
            return await ctx.send('❌ Database not available')
        
        valid_sorts = ['credits', 'points']
        if sort_by.lower() not in valid_sorts:
            sort_by = 'credits'
        
        sort_field = 'qantas_points' if sort_by.lower() == 'points' else 'status_credits'
        
        members = await self.db.frequent_flyers.find().sort(sort_field, -1).limit(10).to_list(10)
        
        if not members:
            return await ctx.send('📊 No members registered yet!')
        
        embed = discord.Embed(
            color=0xE80000,  # Qantas red
            title='🏆 Qantas Frequent Flyer Leaderboard',
            description=f"Top 10 members by {'Qantas Points' if sort_by == 'points' else 'Status Credits'}"
        )
        
        medals = ['🥇', '🥈', '🥉']
        
        for index, member in enumerate(members):
            medal = medals[index] if index < 3 else f"{index + 1}."
            value = (f"{member['qantas_points']:,} points" if sort_by == 'points' 
                    else f"{member['status_credits']} status credits")
            
            embed.add_field(
                name=f"{medal} {member['first_name']} {member['last_name']}",
                value=f"{member['current_tier']} | {value}",
                inline=False
            )
        
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function for plugin loading"""
    await bot.add_cog(QantasFrequentFlyer(bot))
