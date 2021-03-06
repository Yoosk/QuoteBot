import discord
from discord.ext import commands


class PersonalQuotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def personal_embed(self, guild, user, response):
        embed = discord.Embed(description=response, color=user.color.value or discord.Embed.Empty)
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_footer(text=f"{await self.bot.localize(guild, 'PERSONAL_personal_embedfooter')}")
        return embed

    @commands.command()
    async def personal(self, ctx, quote_id: int):
        if (perms := ctx.guild.me.permissions_in(ctx.channel)).manage_messages and (await (await self.bot.db.execute("SELECT delete_commands FROM guild WHERE id = ?", (ctx.guild.id,))).fetchone())[0]:
            await ctx.message.delete()
        if fetch_quote := await (await self.bot.db.execute("SELECT * FROM personal_quote WHERE id = ?", (quote_id,))).fetchone():
            await ctx.send(embed=await self.personal_embed(ctx.guild, ctx.author, fetch_quote[2]))
        else:
            await ctx.send(content=f"{self.bot.config['response_strings']['error']} {await self.bot.localize(ctx.guild, 'PERSONAL_personal_notfound')}")

    @commands.command(aliases=['plist'])
    async def personallist(self, ctx, page: int = 1):
        if fetch_quotes := await (await self.bot.db.execute("SELECT id, response FROM personal_quote WHERE author = ? LIMIT 10 OFFSET ?", (ctx.author.id, page - 1))).fetchall():
            personal_list = ['```']
            for _id, response in fetch_quotes:
                response = ' '.join(discord.utils.escape_markdown(response).splitlines())
                personal_list.append(f"#{_id: <5} {response if len(response) < 50 else f'{response[:47]}...'}")
            embed = discord.Embed(description='\n'.join(personal_list) + '\n```', color=ctx.author.color.value or discord.Embed.Empty)
            embed.set_author(name=await self.bot.localize(ctx.guild, 'PERSONAL_personallist_embedauthor'), icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(content=f"{self.bot.config['response_strings']['error']} {await self.bot.localize(ctx.guild, 'PERSONAL_personallist_noquotes')}")

    @commands.command(aliases=['padd'])
    async def personaladd(self, ctx, *, response: str):
        await self.bot.db.execute("INSERT INTO personal_quote (author, response) VALUES (?, ?)", (str(ctx.author.id), response))
        await self.bot.db.commit()
        quote_id = await (await self.bot.db.execute("SELECT id FROM personal_quote WHERE author = ? ORDER BY id DESC", (ctx.author.id,))).fetchone()
        await ctx.send(content=f"{self.bot.config['response_strings']['success']} {(await self.bot.localize(ctx.guild, 'PERSONAL_personaladd_added')).format(str(quote_id[0]))}")

    @commands.command(aliases=['premove'])
    async def personalremove(self, ctx, quote_id: int):
        if fetch_quote := await (await self.bot.db.execute("SELECT * FROM personal_quote WHERE author = ? AND id = ?", (ctx.author.id, quote_id))).fetchone():
            await self.bot.db.execute("DELETE FROM personal_quote WHERE id = ?", (quote_id,))
            await self.bot.db.commit()
            await ctx.send(content=f"{self.bot.config['response_strings']['success']} {await self.bot.localize(ctx.guild, 'PERSONAL_personalremove_removed')}")
        else:
            await ctx.send(content=f"{self.bot.config['response_strings']['error']} {await self.bot.localize(ctx.guild, 'PERSONAL_personal_notfound')}")

    @commands.command(aliases=['pclear'])
    async def personalclear(self, ctx):
        await self.bot.db.execute("DELETE FROM personal_quote WHERE author = ?", (ctx.author.id,))
        await self.bot.db.commit()
        await ctx.send(content=f"{self.bot.config['response_strings']['success']} {await self.bot.localize(ctx.guild, 'PERSONAL_personalclear_cleared')}")


def setup(bot):
    bot.add_cog(PersonalQuotes(bot))
