import discord

'''Player detials storage from checkin or signup form
'''
class FormData:
    def __init__(self):
        self.text_field = ""
        self.dropdown_selection = ""

    def capture_data(self, text, selection):
        self.text_field = text
        self.dropdown_selection = selection

form_data = FormData()