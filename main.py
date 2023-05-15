from twitchio.ext import commands
import json
import secrets
import asyncio
import random
import socket
import struct

#absolutes go here
JSON_PATH = '' # This should be pointed at the generated_codes.json file in your servers data folder
START_TIME = 20 * 60 # start time in seconds
END_TIME = 45 * 60 #end time in seconds
GIVEAWAYS = 1

#God help me, this is a static list so i'm loading it like this but god do i hate this
THE_LIST = [
] # This should be filled in with items you want to give away from the loadout store in the /datum/store_item format

AMOUNT_JSON_PATH = '' #replace with storage path as an absolute
BYOND_HOST = 'localhost' #replace with server ip
BYOND_PORT = '52724' #replace with server port

EVENT_LIST = [
] # we define our events here as types (this could honestly be a dict but i'm big lazy)

# list that mirrors above but with all their values
VALUES = [
]
# list that mirrors the above 2 but with the byond topic data
BYOND_DATA = [
]
#the Reference code we are using to talk to byond this should be kept secret to prevent people from blasting the SS with requests that will actually go through
BYOND_KEY = "changethisplease"

class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token='', prefix='?', initial_channels=[''])

    async def event_message(self, message) -> None:
        # checks if the message has a bit tag associated with it
        if 'bits' in message.tags:
            # variables the amount and author as its easier this way
            bit_amount = int(message.tags["bits"])
            author = message.author.name
            # pass the information to another proc that handles adding points to a users json
            await self.handle_bit_information(author, bit_amount)
            print(f"{message.author.name} tipped {bit_amount} bits in #{message.channel.name}: {message.content}")

        if message.echo:
            return
        
        await self.handle_commands(message)

    async def handle_bit_information(self, author, bit_amount):
         with open(AMOUNT_JSON_PATH, 'r+') as file:
              # We load the file
                JSON_DATA = json.load(file)
                
                # quick and dirty check to see if we exist in the json if not we add to json with just bit amount else we add the value of bit_amount and saved value
                if author in JSON_DATA:
                    JSON_DATA[author] = JSON_DATA[author] + bit_amount
                else:
                    JSON_DATA[author] = bit_amount
                 # Sets file's current position at offset.
                file.seek(0)
                # Save the file
                json.dump(JSON_DATA, file)

    @commands.command()
    async def balance(self, ctx: commands.Context):
         with open(AMOUNT_JSON_PATH, 'r+') as file:
                # We load the file
                JSON_DATA = json.load(file)
                
                author = ctx.author.name

                # quick and dirty check to see if we exist in the json if not we add to json with just bit amount else we add the value of bit_amount and saved value
                if author in JSON_DATA:
                    await ctx.send(f"{author} has {JSON_DATA[author]} points ready to spend.")
                else:
                    await ctx.send(f"{author} has 0 points ready to spend.")

    @commands.command()
    async def events(self, ctx: commands.Context):
        string = " ---------------------------------------------- ".join(EVENT_LIST)
        await ctx.send(f"{string}")


    @commands.command()
    async def buy(self, ctx: commands.Context, number = None):
         with open(AMOUNT_JSON_PATH, 'r+') as file:
            author = ctx.author.name
            if number == None:
                await ctx.send(f"{author}, please choose what one to buy in numbered order.")
                return
            converted = int(number)

            # We load the file
            JSON_DATA = json.load(file)

            amount = 0
            # quick and dirty check to see if we exist in the json if not we add to json with just bit amount else we add the value of bit_amount and saved value
            if author in JSON_DATA:
                  amount = JSON_DATA[author]
            else:
                await ctx.send(f"{author}, not enough points to complete this transaction.")
                return

            if amount < VALUES[converted - 1]:
                await ctx.send(f"{author}, not enough points to complete this transaction.")
                return

            JSON_DATA[author] = JSON_DATA[author] - VALUES[converted - 1]

            if JSON_DATA[author] == 0:
                JSON_DATA.pop(author)

            # Sets file's current position at offset.
            file.seek(0)
            # Save the file
            json.dump(JSON_DATA, file)
            file.truncate()

            created_string = f"TWITCH-API&{BYOND_KEY}&{BYOND_DATA[converted - 1]}"
            await self.byond_export(created_string)
            await ctx.send(f"{author}, you have successfully paid for the {EVENT_LIST[converted - 1]} event to trigger.")
        
    async def byond_export(self, string):
        # this is a battle field
        # thank god someone else did this for me
        # i would probably cry if i had to try and mess with http2byond

        host = BYOND_HOST
        port = BYOND_PORT

        packet_id = b'\x83'
        try:
            sock = socket.create_connection((host, port))
        except socket.error:
            return

        packet = struct.pack('>xcH5x', packet_id, len(string)+6) + bytes(string, encoding='ascii') + b'\x00'
        sock.send(packet)

        data = sock.recv(512)
        sock.close()
        data = str(data[5:-1], encoding='ascii')
        

    # Here we are defining the three possible write type defs, keeping them seperate as the concept may change
    def write_coins(self, code,  amount):
        with open(JSON_PATH, 'r+') as file:
            # We load the file
            JSON_DATA = json.load(file)
            # we append the current code using python dict sorting ie {CODE}:{AMOUNT}
            JSON_DATA[code] = amount

            # Sets file's current position at offset.
            file.seek(0)
            # Save the file
            json.dump(JSON_DATA, file)
    
    def write_tokens(self, code,  amount):
        threats = ["High Threat", "Medium Threat", "Low Threat"]
        if amount == "Random Threat":
            picked_choice = random.choices(threats, [1, 5, 50])
            amount = picked_choice[0]

        if amount not in threats:
            picked_choice = random.choices(threats, [1, 5, 50])
            amount = picked_choice[0]
            
        with open(JSON_PATH, 'r+') as file:
            # We load the file
            JSON_DATA = json.load(file)
            # we append the current code using python dict sorting ie {CODE}:{AMOUNT}
            JSON_DATA[code] = amount

            # Sets file's current position at offset.
            file.seek(0)
            # Save the file
            json.dump(JSON_DATA, file)

    def write_items(self, code,  amount):
        if amount == '0':
            picked_choice = random.choice(THE_LIST)
            amount = picked_choice
            
        if amount not in THE_LIST:
            picked_choice = random.choice(THE_LIST)
            amount = picked_choice

        with open(JSON_PATH, 'r+') as file:
            # We load the file
            JSON_DATA = json.load(file)
            # we append the current code using python dict sorting ie {CODE}:{AMOUNT}
            JSON_DATA[code] = amount

            # Sets file's current position at offset.
            file.seek(0)
            # Save the file
            json.dump(JSON_DATA, file)

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')


    async def handle_message(ctx):
        print(ctx)

    @commands.command()
    async def giveaway(self, ctx: commands.Context, type, misc = None, quantity = 1):
        # type - case checker for what we want to do
        # misc - extra data unique to the case type (coin amount, antag token level, giveaway path)
        # quantity - the amount of codes we generate

        # This is a trial command that generates a single use redemption code in standard code format
        # e.g ?giveaway coins 500 3
        # This would generate a code with coins data ie {code} = 500 3 times.

        # Check if we have one of th elisted badges
        badge_list = ('broadcaster', 'moderator')
        if not bool(set(badge_list).intersection(ctx.author.badges)):
            await ctx.send("Sorry you need to be atleast a moderator to do this.")
            return
        
        #pulling data from the command
        type = type.split(" ")[0]
        quantity = quantity

        code_list = []
        for num in range(quantity):
            code = '-'.join([''.join(secrets.token_hex(3)) for _ in range(5)])
            string = ""
            code_list.append(code)

            match type:
                case "coins":
                    string = f"Generated {quantity} Coin Codes worth {misc} Monkecoins each. Generated Codes: {code_list}"
                    self.write_coins(code, misc)
                case "item":
                    if misc is not None:
                        misc = misc.split(" ")[0]

                    if misc == '0':
                        misc = None

                    string = f"Generated {quantity} Item Codes. Generated Codes: {code_list}"
                    self.write_items(code, misc)
                case "token":
                    if misc is not None:
                        misc = misc.split(" ")[0]
                    if misc == '0':
                        misc = None
                    stringed_type = ""
                    match misc:
                        case "high":
                            stringed_type = "High Threat"
                        case "medium":
                            stringed_type = "Medium Threat"
                        case "low":
                            stringed_type = "Low Threat"
                        case None:
                            stringed_type = "Random Threat"

                    string = f"Generated {quantity} {stringed_type} Antag Tokens. Generated Codes: {code_list}"
                    self.write_tokens(code, stringed_type)
                
        await ctx.send(f'{string}!')

    @commands.command()
    async def toggle_giveaways(self, ctx: commands.Context):
        
        # Check if we have one of any of the listed badges
        badge_list = ('broadcaster', 'moderator')
        if not bool(set(badge_list).intersection(ctx.author.badges)):
            await ctx.send("Sorry you need to be atleast a moderator to do this.")
            return

        global GIVEAWAYS
        if GIVEAWAYS != None:
            GIVEAWAYS = None
            await ctx.send("Giveaways will no longer happen!")
        else:
            GIVEAWAYS = 1
            await ctx.send("Giveaways will now happen!")

        while GIVEAWAYS:
            
            chatter_list = []
            for x in ctx.chatters:
                chatter_list.append(x.display_name)
            
            if "borbop" not in chatter_list: #replace this with broadcasters name
                GIVEAWAYS = None
                await ctx.send("Error: Broadcaster not detected in chat! Stopping Giveaways.")
                return
            
            # Sleep for a random time between 5 and 10 seconds
            sleep_time = random.randint(START_TIME, END_TIME)
            await asyncio.sleep(sleep_time)

            
            
            # Run a command here
            values = [250, 500, 1000]
            amount = random.choices(values, weights = [50, 10, 5])
            code = '-'.join([''.join(secrets.token_hex(3)) for _ in range(5)])
            self.write_coins(code, amount[0])
            string = f"Random Giveaway Time: We Have Generated a code worth {amount[0]} Monkecoins. Code: {code}"
        
            await ctx.send(f'{string}')

bot = Bot()
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
