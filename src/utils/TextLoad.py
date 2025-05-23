import os
from charset_normalizer import detect

from src.core.services.database.models.models import BookModelOrm


class TextLoad:
      def __init__(self, data:BookModelOrm):
          self.data = data

      def push_text(self, *path):
        if path:
            adress = os.path.join(os.getcwd(), *path,  str(self.data.text_hook))
            text_view = 'No text'
            encod = 'utf-8'
        else:
            adress = os.path.join(os.getcwd(),  str(self.data.text_hook))
            text_view = 'No text'
            encod = 'utf-8'


        with open(adress, 'rb') as file:
            detector = detect(file.read())
            
        encod = detector['encoding']

        with open(adress, encoding=encod) as file:
            text_view = file.read()

        return text_view