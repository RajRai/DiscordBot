import sys
import os
import discord
import sqlite3
import asyncio
from sqlite3 import Error
from discord.ext import tasks, commands
from discord.utils import get

from bot.token import TOKEN;




bot = commands.Bot(command_prefix="!")


@commands.check
def check_is_command(ctx):
    return ctx.message.content.startswith('!')


@commands.check
def is_bot_message(ctx):
    return ctx.message.author == bot.user


@bot.event
async def on_message(message):
    await bot.wait_until_ready()

    await bot.process_commands(message)

    # Delete messages not from Raj in get-roles
    if message.channel.id == 752991821851787355 and (
            (752968090295468032 not in message.author.roles) or message.author == bot.user):
        await message.delete(delay=10)

    # Update DB for each message
    db = connectToDB()
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO users VALUES (?,?,?) ON CONFLICT (name) DO UPDATE SET messages = messages + 1",
                    [str(message.author), 0, 1])
    except Exception as e:
        print(e)
        try:
            cur.execute("UPDATE users SET messages = messages + 1 WHERE name = ?;", [str(message.author)])
        except Exception as e:
            print(e)
    db.commit()
    db.close()


@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    await(await(channel.send(
        "Hey " + member.mention + ", welcome to the Discord server!\n\n If your in-game name is different from your "
                                  "Discord username, make sure you do !name \"in-game name\" (including the quotes) "
                                  "to update your name."))).delete(
        delay=3600)


@bot.command(name='restart', help='Restarts the bot')
@commands.has_any_role('Co-Leader', 'Leader', 'Administrator')
async def restart(ctx):
    await(ctx.message.channel.send('Goodbye!'))
    await bot.logout()
    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)
    sys.exit(0)


@bot.command(name='quit', help='Exits the bot')
@commands.has_role('Administrator')
async def quit(ctx):
    await(ctx.message.channel.send('Goodbye!'))
    await bot.logout()
    sys.exit(0)


@bot.command(name='name', help='Sets your nickname')
async def name(ctx, new):
    await bot.wait_until_ready()
    await ctx.message.author.edit(nick=new)
    await(await(ctx.message.channel.send("Ok " + ctx.message.author.mention + ", updated your name."))).delete(
        delay=3600)


@bot.command(name='giverole', help='Gives you the requested role (CWL, Clan Games, or Clan Wars)')
@commands.has_role('Administrator')
async def giverole(ctx, role):
    await bot.wait_until_ready()
    role = role.lower()
    member = ctx.message.author
    if role == "clan war league" or role == "cwl":
        role = get(member.guild.roles, name="Clan War League")
        await member.add_roles(role)
    elif role == "clan games" or role == "cg":
        role = get(member.guild.roles, name="Clan Games")
        await member.add_roles(role)
    elif role == "clan wars" or role == "cw" or role == "wars":
        role = get(member.guild.roles, name="Clan Wars")
        await member.add_roles(role)
    else:
        await(await(ctx.message.channel.send(
            'You didnt enter a valid role! Type !giverole cwl, !giverole cg, or !giverole cw (Clan War Leagues, '
            'Clan Games, and Clan Wars) ' + ctx.message.author.mention))).delete(
            delay=30)
        return
    await(await(ctx.message.channel.send("Gave the role! " + ctx.message.author.mention))).delete(delay=30)


@bot.command(name='activity', help='Displays user activity')
@commands.has_any_role('Administrator', 'Leader', 'Co-Leader')
async def activity(ctx, arg1='desc', arg2=10):
    arg1 = arg1.lower()
    if (arg1 != 'asc' and arg1 != 'desc') or not isinstance(arg2, int):
        await ctx.message.channel.send("Bad input. Example usage: !activity desc 10")
        return
    db = connectToDB()
    cur = db.cursor()
    cur.execute("SELECT * FROM users ORDER BY messages {0} LIMIT {1}".format(str(arg1), str(arg2)))
    data = cur.fetchall()
    out = "Name - Online Hours - Messages Sent (Sorted by messages)\n"
    for row in data:
        out += str(row[0])
        out += ' - '
        out += str(row[1])
        out += ' - '
        out += str(row[2])
        out += '\n'
    out += '\n'
    cur.execute("SELECT * FROM users ORDER BY hours {0} LIMIT {1}".format(str(arg1), str(arg2)))
    data = cur.fetchall()
    out += "Name - Online Hours - Messages Sent (Sorted by hours)\n"
    for row in data:
        out += str(row[0])
        out += ' - '
        out += str(row[1])
        out += ' - '
        out += str(row[2])
        out += '\n'
    out += ctx.message.author.mention
    await ctx.message.channel.send(out)


@bot.command(name='clearactivity', help='Clear the activities database (NOT reversable, be careful!)')
@commands.has_role('Administrator')
async def clearActivity(ctx):
    db = connectToDB()
    cur = db.cursor()
    cur.execute("DELETE FROM users")
    db.execute("VACUUM")
    db.commit()
    db.close()
    ctx.message.channel.send("Done! " + ctx.message.author.mention)


async def updateActivity():
    while True:
        db = connectToDB()
        cur = db.cursor()
        for member in bot.get_all_members():
            if member.status != discord.Status.offline:
                try:
                    cur.execute("INSERT INTO users VALUES (?,?,?)", [str(member), 1, 0])
                except Exception as e:
                    print(e)
                    try:
                        cur.execute("UPDATE users SET hours = hours + 1 WHERE name = ?;", [str(member)])
                    except Exception as e:
                        print(e)
        db.commit()
        db.close()
        await asyncio.sleep(3600)


def connectToDB():
    db_file = r"C:\Users\rajat\sqlite\db\pythonsqlite.db"
    conn = None
    try:
        conn = sqlite3.connect(db_file, isolation_level=None)
        return conn
    except Error as e:
        print(e)
    return conn


bot.loop.create_task(updateActivity())
bot.run(TOKEN)
