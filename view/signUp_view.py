import discord
from model.button_state import ButtonState
from controller.signup_shared_logic import SharedLogic
import time

class SignUpView(discord.ui.View):
    def __init__(self, timeout = 600):
        super().__init__(timeout=timeout)
        self.timeout = timeout
        self.viewStart_time = time.time()

    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        #await self.message.delete()  --we can delete the messgae at all
        await self.message.edit(view=self)
        


    async def on_timeout(self) -> None:
        await self.message.channel.send("this action is timed out, please use a '/register' command to register")
        await self.disable_all_items()

    @discord.ui.button(label="Sign Up", style=discord.ButtonStyle.success)
    async def signUp(self, interaction: discord.Interaction, button:discord.ui.Button):
        remaining_time = self.timeout - (time.time() - self.viewStart_time)
      
        # self.stop()
        await SharedLogic.execute_signup_model(interaction, timeout=remaining_time)
        # await self.disable_all_items()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction, button:discord.ui.Button):
        await interaction.response.send_message("sure ignore for now")
        self.stop()
