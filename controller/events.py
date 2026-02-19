import discord
from discord.ext import commands
from config import settings
from model import dbc_model
from model.button_state import ButtonState, first_login_users
from view.signUp_view import SignUpView
from common import common_scripts


logger = settings.logging.getLogger("discord")

class EventsController(commands.Cog):
    def __init__(self, bot:commands.bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        db = dbc_model.Tournament_DB()
        isMemberexist = dbc_model.Player.isMemberExist(db, member.id)
        db.close_db()
        if not isMemberexist:
            views_for_signup = SignUpView()

            if views_for_signup.children:

                ksu_logo_path = await common_scripts.get_ksu_logo()
                resize_logo, logo_extention  = await common_scripts.ksu_img_resize(ksu_logo_path)
                # logo = discord.File(resize_logo, filename=resize_logo.name)

                logger.info(f"log path is : {resize_logo} and file name {logo_extention}")

                embed = discord.Embed(
                    color=discord.Colour.dark_teal(),
                    description="Please Register Here .........................\
                    .................................................................\
                        ........................................................\
                            .................................",
                    title=f"Welcome To KSU eSports Server"
                )
                # embed.set_image(url=f"{ksu_logo_path}")
                embed.set_thumbnail(url=f"attachment://resized_logo{logo_extention}")

                await member.send(embed=embed, file=discord.File(resize_logo, filename=f"resized_logo{logo_extention}"))
                message = await member.send(view=views_for_signup)

                views_for_signup.message = message

                await views_for_signup.wait()

            else:
                logger.error("signup view is not working please take a look")
                server_owner = member.guild.owner

                await server_owner.send(f"Hello {server_owner} the signup view is not working please check")     

    @commands.Cog.listener()
    async def on_member_remove(self, member : discord.Member):
        db = dbc_model.Tournament_DB()
        dbc_model.Player.remove_player(db, member.id)
        db.close_db()

async def setup(bot):
    await bot.add_cog(EventsController(bot))