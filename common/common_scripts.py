import pathlib
from config import settings
import random
from PIL import Image
import io
import os
import discord
import asyncio
from view.common_view import PlayerPrefRole

async def get_ksu_logo():
    ksu_logo = pathlib.Path(settings.Base_Dir / "common" / "images").glob("**/*")
    return random.choice(list(ksu_logo))


async def ksu_img_resize(imagepath: str, size : tuple=(200, 200)) -> io.BytesIO:
    """Resize the image with same image format/extention as byte stream for attachment
    and save in memory.
    param:
        imagepath:- the file path of the image to be resized
        Size:- default size is set, custome can be updated in config later
    result:
        return:- a resized image in the form of BytesIo
    """
    img_extention = os.path.splitext(imagepath)[1].lower()
    #open image with pillow
    with Image.open(imagepath) as img:
        # img = img.size((100, 100)) #it is pixel
        resize_img = img.resize(size=size)
        image_format = resize_img.format if resize_img.format else 'PNG'
        #maintain aspect size
        # width, height = img.size
        # comparative_size = width/height

        # new_width = 100
        # new_height = int(new_width/comparative_size)

        # resize_img = img.resize((new_width, new_height))

        #save the resize logo in memory
        img_byte_stream = io.BytesIO()
        img.save(img_byte_stream, image_format)

        img_byte_stream.seek(0)

    return img_byte_stream, img_extention

async def confirmation_recived(submited : bool = False, timeout : int = 300, interaction: discord.Interaction = None):
    if submited:
        role_ref_view = PlayerPrefRole()

        # Send the message and store the reference in the view
        message = await interaction.response.send_message(content="Please select your role preferences", view=role_ref_view)
        role_ref_view.message = message

        # The message will be automatically deleted when the preferences are saved
        # But we'll also set a timeout as a fallback
        await asyncio.sleep(timeout)
        try:
            await message.delete()
        except:
            pass  # Message may have already been deleted by the view
