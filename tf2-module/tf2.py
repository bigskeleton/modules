import discord
from discord.ext import commands
from .utils.dataIO import fileIO
from .utils import checks
import os
import json
import httplib2
from copy import deepcopy
from __main__ import user_allowed, send_cmd_help
try: # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False

class TF2:
    """TF2 Red Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.playerlist = fileIO("data/tf2/players.json", "load")

    @commands.group(pass_context=True)
    async def tf2(self, ctx):
        """Returns various data for tf2 players"""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Type help tf2 for info.")

    @tf2.command(name = 'addplayer', pass_context=True)
    @checks.mod_or_permissions(manage_server=True)
    async def addplayer(self, ctx, player : str, *, text):
        """Adds a custom player with an alias and their SteamID64 (ex: 7656119XXXXXXXXXX)

        Example:
        !tf2 addplayer player 7656119XXXXXXXXXX
        """
        server = ctx.message.server
        player = player.lower()
        if not server.id in self.playerlist:
            self.playerlist[server.id] = {}
        plist = self.playerlist[server.id]
        if player not in plist and "7656119" in text and len(text) == 17:
            plist[player] = text
            self.playerlist[server.id] = plist
            fileIO("data/tf2/players.json", "save", self.playerlist)
            await self.bot.say("Player successfully added.")
        elif "7656119" not in text or len(text) != 17:
            await self.bot.say("Invalid SteamID64 (ex: 7656119XXXXXXXXXX)")
        else:
            await self.bot.say("This player already exists. Use delplayer to delete them.")
            
    @tf2.command(name = 'delplayer', pass_context=True)
    @checks.mod_or_permissions(manage_server=True)
    async def delplayer(self, ctx, player : str):
        """Deletes a player and their ID

        Example:
        !tf2 delplayer player 
        """
        server = ctx.message.server
        player = player.lower()
        if server.id in self.playerlist:
            plist = self.playerlist[server.id]
            if player in plist:
                plist.pop(player, None)
                self.playerlist[server.id] = plist
                fileIO("data/tf2/players.json", "save", self.playerlist)
                await self.bot.say("Player successfully deleted.")
            else:
                await self.bot.say("Player not found.")
        else:
            await self.bot.say("No players registered. Use addplayer")
            
    @tf2.command(name = 'profile', pass_context = True)
    async def profile(self, ctx, player):
        """Returns the logs.tf and sizzlingstats profile for the player"""

        server = ctx.message.server
        if server.id in self.playerlist:
            plist = self.playerlist[server.id]
            if player in plist:
                account_id = plist[player]
                message = "Profiles for \""
                message += player
                message += "\"\n<http://logs.tf/profile/"
                message += account_id
                message += ">\n<http://sizzlingstats.com/player/"
                message += account_id
                message += ">"
                await self.bot.say(message)
            else:
                await self.bot.say("Player not found.")
        else:
            await self.bot.say("No players registered. Use addplayer")
        
    @tf2.command(name = 'recent', pass_context = True)
    async def recent(self, ctx, player, matches : int=1):
        """Returns recent matches
        Can return up to 4, defaults to 1
        
        Example:
        !tf2 recent player 3
        """
        
        await self.bot.send_typing(ctx.message.channel)

        server = ctx.message.server
        if server.id in self.playerlist:
            plist = self.playerlist[server.id]
            if player in plist:
                account_id = plist[player]
                logurl = "http://logs.tf/profile/"
                logurl += str(account_id)
                ssurl = "http://sizzlingstats.com/api/player/"
                ssurl += str(account_id)
                
                if matches < 1:
                    matches = 1
                elif matches > 4:
                    matches = 4
                    
                counter = 0
                maps = []
                teams = []
                logs = []
                ss = []
                message = ""
                try:
                    http = httplib2.Http()
                    status, response = http.request(logurl)
                    logsoup = BeautifulSoup(response, 'html.parser')
                    
                    http = httplib2.Http()
                    status, response = http.request(ssurl)
                    sssoup = BeautifulSoup(response, 'html.parser')
                    
                    for item in logsoup.find_all(attrs={'class': 'table loglist'}):
                        for link in item.find_all('a'):
                            logs.append("<http://logs.tf" + link.get('href')[:8] + ">")
                            counter += 1
                            if counter == matches:
                                break

                    ssjson = json.loads(str(sssoup))
                    for i in range(0, counter):
                        maps = ssjson["matches"][i]["map"]
                        teams = ssjson["matches"][i]["redname"] + " vs " + ssjson["matches"][i]["bluname"]
                        ss = "<http://sizzlingstats.com/stats/" + str(ssjson["matches"][i]["_id"]) + ">"
                        message += (teams + " -- " + maps) + '\n'
                        message += str(logs[i]) + " // " + str(ss) + '\n'
                except:
                    message = "Something went wrong pulling matches"
                await self.bot.say(message)
            else:
                await self.bot.say("Player not found.")
        else:
            await self.bot.say("No players registered. Use addplayer")
        
def check_folders():
    if not os.path.exists("data/tf2"):
        print("Creating data/tf2 folder...")
        os.makedirs("data/tf2")

def check_files():
    f = "data/tf2/players.json"
    if not fileIO(f, "check"):
        print("Creating empty players.json...")
        fileIO(f, "save", {})
        
def setup(bot):
    check_folders()
    check_files()
    n = TF2(bot)
    bot.add_cog(n)
    # tf2-module
