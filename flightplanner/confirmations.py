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


class SendConfirmationView(View):
    """View for confirming whether to send the flight plan"""
    
    def __init__(self, author, handler, flight_embed, airline, flight_number):
        super().__init__(timeout=60)
        self.author = author
        self.handler = handler
        self.flight_embed = flight_embed
        self.airline = airline
        self.flight_number = flight_number
    
    @button(label="Send Flight Plan", style=discord.ButtonStyle.green, emoji="📤")
    async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Get the target channel
        target_channel_id = 1400766110306926652
        target_channel = interaction.client.get_channel(target_channel_id)
        
        if not target_channel:
            await interaction.response.send_message(
                "❌ Could not find the destination channel.",
                ephemeral=True
            )
            return
        
        try:
            # Send the flight plan to the target channel WITH BUTTONS
            flight_view = FlightPlanActionsView(self.airline, self.flight_number)
            await target_channel.send(embed=self.flight_embed, view=flight_view)
            
            # Confirm to user
            success_embed = discord.Embed(
                title="✅ Flight Plan Sent!",
                description=f"Your flight plan has been successfully sent to <#{target_channel_id}>!",
                color=discord.Color.green()
            )
            
            await interaction.response.edit_message(embed=success_embed, view=None)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to send flight plan: {str(e)}",
                ephemeral=True
            )
        
        # End the session
        self.handler.end_session(self.author.id)
        self.stop()


class FlightPlanActionsView(View):
    """Buttons that appear on the sent flight plan message"""
    
    def __init__(self, airline, flight_number):
        super().__init__(timeout=None)  # Buttons never expire
        self.airline = airline
        self.flight_number = flight_number
    
    @button(label="Check-In Closed", style=discord.ButtonStyle.red, emoji="🔒", custom_id="checkin_closed")
    async def checkin_closed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Create professional check-in closed embed
        if self.airline == "Qantas":
            checkin_embed = discord.Embed(
                title="",
                description="",
                color=0xE40000
            )
            checkin_embed.set_thumbnail(url="https://1000logos.net/wp-content/uploads/2017/05/Qantas-Logo-1536x966.png")
            
            checkin_embed.add_field(
                name="<:QFtail2:1401856972180947035> CHECK-IN STATUS",
                value=f"**Flight {self.flight_number}**",
                inline=False
            )
            
            checkin_embed.add_field(
                name="",
                value="━━━━━━━━━━━━━━━━━━━━━━",
                inline=False
            )
            
            checkin_embed.add_field(
                name="<:QFseatbelt:1401010857928032316> CHECK-IN CLOSED",
                value="Online check-in for this flight has now closed.\n\nPassengers are advised to proceed directly to the airport and complete check-in at the Qantas service counter.",
                inline=False
            )
            
            checkin_embed.add_field(
                name="<:Announcment:1399308384502808588> IMPORTANT INFORMATION",
                value="• Arrive at the airport at least **2 hours** before departure for domestic flights\n• Arrive at least **3 hours** before departure for international flights\n• Have your booking reference and identification ready",
                inline=False
            )
            
            checkin_embed.add_field(
                name="<:External:1399308477897244705> NEED ASSISTANCE?",
                value="Visit the Qantas service desk or contact our customer service team for support.",
                inline=False
            )
            
            checkin_embed.set_footer(
                text="Qantas Airways • The Spirit of Australia",
                icon_url="https://1000logos.net/wp-content/uploads/2017/05/Qantas-Logo-1536x966.png"
            )
            
        else:  # Jetstar
            checkin_embed = discord.Embed(
                title="",
                description="",
                color=0xFF6600
            )
            checkin_embed.set_thumbnail(url="https://logos-world.net/wp-content/uploads/2023/01/Jetstar-Logo-2003.png")
            
            checkin_embed.add_field(
                name="<:JQtail:1421704382608838776> CHECK-IN STATUS",
                value=f"**Flight {self.flight_number}**",
                inline=False
            )
            
            checkin_embed.add_field(
                name="",
                value="━━━━━━━━━━━━━━━━━━━━━━",
                inline=False
            )
            
            checkin_embed.add_field(
                name="<:JQplane:1421703070907105280> CHECK-IN CLOSED",
                value="Online check-in for this flight has now closed.\n\nPassengers are advised to proceed directly to the airport and complete check-in at the Jetstar service counter.",
                inline=False
            )
            
            checkin_embed.add_field(
                name="<:JQcall:1421702400162402304> IMPORTANT INFORMATION",
                value="• Arrive at the airport at least **2 hours** before departure for domestic flights\n• Arrive at least **3 hours** before departure for international flights\n• Have your booking reference and identification ready",
                inline=False
            )
            
            checkin_embed.add_field(
                name="<:JQtower:1421700708629086250> NEED ASSISTANCE?",
                value="Visit the Jetstar service desk or contact our customer service team for support.",
                inline=False
            )
            
            checkin_embed.set_footer(
                text="Jetstar Airways • All Day, Every Day, Low Fares",
                icon_url="https://logos-world.net/wp-content/uploads/2023/01/Jetstar-Logo-2003.png"
            )
        
        # Send check-in closed message
        await interaction.channel.send(embed=checkin_embed)
        
        # Acknowledge the button click
        await interaction.response.send_message("✅ Check-in closed message sent!", ephemeral=True)
    
    @button(label="Send Check-In Closed", style=discord.ButtonStyle.blurple, emoji="🔒")
    async def checkin_closed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Get the target channel
        target_channel_id = 1400766110306926652
        target_channel = interaction.client.get_channel(target_channel_id)
        
        if not target_channel:
            await interaction.response.send_message(
                "❌ Could not find the destination channel.",
                ephemeral=True
            )
            return
        
        try:
            # Create professional check-in closed embed
            if self.airline == "Qantas":
                checkin_embed = discord.Embed(
                    title="",
                    description="",
                    color=0xE40000
                )
                checkin_embed.set_thumbnail(url="https://1000logos.net/wp-content/uploads/2017/05/Qantas-Logo-1536x966.png")
                
                checkin_embed.add_field(
                    name="<:QFtail2:1401856972180947035> CHECK-IN STATUS",
                    value=f"**Flight {self.flight_number}**",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="",
                    value="━━━━━━━━━━━━━━━━━━━━━━",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="<:QFseatbelt:1401010857928032316> CHECK-IN CLOSED",
                    value="Online check-in for this flight has now closed.\n\nPassengers are advised to proceed directly to the airport and complete check-in at the Qantas service counter.",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="<:Announcment:1399308384502808588> IMPORTANT INFORMATION",
                    value="• Arrive at the airport at least **2 hours** before departure for domestic flights\n• Arrive at least **3 hours** before departure for international flights\n• Have your booking reference and identification ready",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="<:External:1399308477897244705> NEED ASSISTANCE?",
                    value="Visit the Qantas service desk or contact our customer service team for support.",
                    inline=False
                )
                
                checkin_embed.set_footer(
                    text="Qantas Airways • The Spirit of Australia",
                    icon_url="https://1000logos.net/wp-content/uploads/2017/05/Qantas-Logo-1536x966.png"
                )
                
            else:  # Jetstar
                checkin_embed = discord.Embed(
                    title="",
                    description="",
                    color=0xFF6600
                )
                checkin_embed.set_thumbnail(url="https://logos-world.net/wp-content/uploads/2023/01/Jetstar-Logo-2003.png")
                
                checkin_embed.add_field(
                    name="<:JQtail:1421704382608838776> CHECK-IN STATUS",
                    value=f"**Flight {self.flight_number}**",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="",
                    value="━━━━━━━━━━━━━━━━━━━━━━",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="<:JQplane:1421703070907105280> CHECK-IN CLOSED",
                    value="Online check-in for this flight has now closed.\n\nPassengers are advised to proceed directly to the airport and complete check-in at the Jetstar service counter.",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="<:JQcall:1421702400162402304> IMPORTANT INFORMATION",
                    value="• Arrive at the airport at least **2 hours** before departure for domestic flights\n• Arrive at least **3 hours** before departure for international flights\n• Have your booking reference and identification ready",
                    inline=False
                )
                
                checkin_embed.add_field(
                    name="<:JQtower:1421700708629086250> NEED ASSISTANCE?",
                    value="Visit the Jetstar service desk or contact our customer service team for support.",
                    inline=False
                )
                
                checkin_embed.set_footer(
                    text="Jetstar Airways • All Day, Every Day, Low Fares",
                    icon_url="https://logos-world.net/wp-content/uploads/2023/01/Jetstar-Logo-2003.png"
                )
            
            # Send check-in closed message
            await target_channel.send(embed=checkin_embed)
            
            # Confirm to user
            success_embed = discord.Embed(
                title="✅ Check-In Closed Message Sent!",
                description=f"The check-in closed notification has been sent to <#{target_channel_id}>!",
                color=discord.Color.green()
            )
            
            await interaction.response.edit_message(embed=success_embed, view=None)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to send message: {str(e)}",
                ephemeral=True
            )
        
        # End the session
        self.handler.end_session(self.author.id)
        self.stop()
    
    @button(label="Don't Send", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Cancel and end session
        cancel_embed = discord.Embed(
            title="❌ Flight Plan Cancelled",
            description="Your flight plan was not sent. Session closed.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=cancel_embed, view=None)
        
        # End the session
        self.handler.end_session(self.author.id)
        self.stop()


class FlightNumberConfirmationView(View):
    """View for confirming the flight number"""
    
    def __init__(self, author, handler, flight_number):
        super().__init__(timeout=60)
        self.author = author
        self.handler = handler
        self.flight_number = flight_number
    
    @button(label="Yes, Correct", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Save flight number
        self.handler.update_session(self.author.id, "flight_number", self.flight_number)
        
        # Get session data
        session = self.handler.get_session(self.author.id)
        
        # Create stylish final summary
        airline = session["airline"]
        
        if airline == "Qantas":
            # Qantas modern embed
            embed = discord.Embed(
                title="",
                description="",
                color=0xE40000  # Qantas red
            )
            
            # Set Qantas logo
            embed.set_thumbnail(url="https://1000logos.net/wp-content/uploads/2017/05/Qantas-Logo-1536x966.png")
            
            # Flight header
            embed.add_field(
                name="<:QFtail2:1401856972180947035> FLIGHT CONFIRMATION",
                value=f"**Flight {self.flight_number}** • {session['aircraft']}",
                inline=False
            )
            
            # Route with emojis
            embed.add_field(
                name="<:Departing:1399308427267801138> DEPARTURE",
                value=f"**{session['departure_code']}** {session['departure_name']}\n<t:{session['combined_timestamp']}:F>\n<t:{session['combined_timestamp']}:R>",
                inline=True
            )
            
            embed.add_field(
                name="<:Landing:1399308429801029692> ARRIVAL",
                value=f"**{session['arrival_code']}** {session['arrival_name']}",
                inline=True
            )
            
            # Spacer
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            # Flight details with custom emojis
            details = []
            details.append(f"<:Australia:1399308387866640508> **Route:** {session['departure_code']} → {session['arrival_code']}")
            details.append(f"<:QFseatbelt:1401010857928032316> **Aircraft:** {session['aircraft']}")
            details.append(f"<:Announcment:1399308384502808588> **Status:** Confirmed")
            
            embed.add_field(
                name="<:External:1399308477897244705> FLIGHT INFORMATION",
                value="\n".join(details),
                inline=False
            )
            
            # Amenities
            amenities = "<:QFwifi:1401010833831759922> Wi-Fi Available  •  <:QFmail:1399308493910966322> In-Flight Service  •  <:Link:1399308473342099507> Entertainment"
            embed.add_field(
                name="✈️ AMENITIES & SERVICES",
                value=amenities,
                inline=False
            )
            
            # Footer
            embed.set_footer(
                text="Qantas Airways • The Spirit of Australia",
                icon_url="https://1000logos.net/wp-content/uploads/2017/05/Qantas-Logo-1536x966.png"
            )
            
        else:
            # Jetstar modern embed
            embed = discord.Embed(
                title="",
                description="",
                color=0xFF6600  # Jetstar orange
            )
            
            # Set Jetstar logo
            embed.set_thumbnail(url="https://logos-world.net/wp-content/uploads/2023/01/Jetstar-Logo-2003.png")
            
            # Flight header
            embed.add_field(
                name="<:JQtail:1421704382608838776> FLIGHT CONFIRMATION",
                value=f"**Flight {self.flight_number}** • {session['aircraft']}",
                inline=False
            )
            
            # Route with emojis
            embed.add_field(
                name="<:JQplane:1421703070907105280> DEPARTURE",
                value=f"**{session['departure_code']}** {session['departure_name']}\n<t:{session['combined_timestamp']}:F>\n<t:{session['combined_timestamp']}:R>",
                inline=True
            )
            
            embed.add_field(
                name="<:JQtower:1421700708629086250> ARRIVAL",
                value=f"**{session['arrival_code']}** {session['arrival_name']}",
                inline=True
            )
            
            # Spacer
            embed.add_field(name="\u200b", value="\u200b", inline=False)
            
            # Flight details with custom emojis
            details = []
            details.append(f"<:JQwhite:1421704746355527801> **Route:** {session['departure_code']} → {session['arrival_code']}")
            details.append(f"<:JQplane:1421703070907105280> **Aircraft:** {session['aircraft']}")
            details.append(f"<:JQcall:1421702400162402304> **Status:** Confirmed")
            
            embed.add_field(
                name="<:JQwhite:1421704746355527801> FLIGHT INFORMATION",
                value="\n".join(details),
                inline=False
            )
            
            # Amenities
            amenities = "<:JQmusic:1421701618377687050> In-Flight Entertainment  •  <:JQcall:1421702400162402304> Customer Service"
            embed.add_field(
                name="✈️ SERVICES",
                value=amenities,
                inline=False
            )
            
            # Footer
            embed.set_footer(
                text="Jetstar Airways • All Day, Every Day, Low Fares",
                icon_url="https://logos-world.net/wp-content/uploads/2023/01/Jetstar-Logo-2003.png"
            )
        
        # Create buttons for sending confirmation AND check-in closed
        send_view = SendConfirmationView(self.author, self.handler, embed, session["airline"], self.flight_number)
        
        await interaction.response.edit_message(embed=embed, view=send_view)
        
        # Don't end session yet - wait for send confirmation
        self.stop()
    
    @button(label="No, Try Again", style=discord.ButtonStyle.red, emoji="❌")
    async def retry_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your flight planning session!", 
                ephemeral=True
            )
            return
        
        # Get airline from session
        session = self.handler.get_session(self.author.id)
        airline = session.get("airline", "")
        
        # Determine airline prefix
        prefix_hint = ""
        if airline == "Qantas":
            prefix_hint = "\n\n**Hint:** Qantas flights start with `QF` (e.g., QF94)"
        elif airline == "Jetstar":
            prefix_hint = "\n\n**Hint:** Jetstar flights start with `JQ` (e.g., JQ30)"
        
        embed = discord.Embed(
            title="✈️ Flight Number",
            description=f"Please enter your flight number.{prefix_hint}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Examples",
            value="• `QF94`\n• `JQ30`\n• `VA803`",
            inline=False
        )
        embed.set_footer(text="Type the flight number in chat")
        
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
        
        # Save departure date and move to flight number
        self.handler.update_session(self.author.id, "departure_date", self.date_obj)
        self.handler.update_session(self.author.id, "combined_timestamp", self.combined_timestamp)
        self.handler.update_session(self.author.id, "stage", "flight_number")
        
        # Get airline from session
        session = self.handler.get_session(self.author.id)
        airline = session.get("airline", "")
        
        # Determine airline prefix
        prefix_hint = ""
        if airline == "Qantas":
            prefix_hint = "\n\n**Hint:** Qantas flights start with `QF` (e.g., QF94)"
        elif airline == "Jetstar":
            prefix_hint = "\n\n**Hint:** Jetstar flights start with `JQ` (e.g., JQ30)"
        
        embed = discord.Embed(
            title="✈️ Flight Number",
            description=f"Please enter your flight number.{prefix_hint}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Examples",
            value="• `QF94`\n• `JQ30`\n• `VA803`",
            inline=False
        )
        embed.set_footer(text="Type the flight number in chat")
        
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
