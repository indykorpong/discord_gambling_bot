from bot_main import *

bot = commands.Bot(command_prefix='$', help_command=None)


# Discord's asynchronous methods

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await print_msg(bot, 'IndyBot has come online!', destroy=True, delay=60)
    await wait_for_users(bot)


# Bot's main asynchronous methods

@bot.command()
async def apply(ctx: commands.Context):
    await bot_apply(ctx, bot)


@bot.command()
async def help(ctx: commands.Context):
    await bot_help(ctx, bot)


@bot.command()
async def current(ctx: commands.Context):
    await bot_current(ctx, bot)


@bot.command()
async def bet_open(ctx: commands.Context):
    await bot_bet_open(bot)


@bot.command()
async def bet_close(ctx: commands.Context):
    await bot_bet_close(bot)


@bot.command()
async def bet(ctx: commands.Context, bet_side, token):
    await bot_bet(ctx, bot, bet_side, token)


@bot.command()
async def result(ctx: commands.Context, bet_result):
    await bot_result(ctx, bot, bet_result)


@bot.command()
async def donate(ctx: commands.Context, donatee: discord.Member, donate_amount):
    await bot_donate(ctx, bot, donatee, donate_amount)


# @bot.command()
# async def redeem(ctx: commands.Context, *args):
#


@bot.command()
async def duel(ctx: commands.Context, user: discord.Member, tokens):
    await bot_duel(ctx, bot, user, tokens)


@bot.command()
async def duel_accept(ctx: commands.Context):
    await bot_duel_accept(ctx, bot)


@bot.command()
async def duel_decline(ctx: commands.Context):
    await bot_duel_decline(ctx, bot)


# Synchronous methods

def read_app_token():
    with open(token_filename, 'r') as f:
        lines = f.readlines()
        return lines[0].strip()


def run_bot():
    app_token = read_app_token()
    bot.run(app_token)


# Call main

if __name__ == '__main__':
    run_bot()
