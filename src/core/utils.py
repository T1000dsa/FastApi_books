from src.database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data, select_data_book
class Choice:
    def __init__(self, choice:int):
        self.choice = choice
    def get_obj(self):
        return output_data(self.choice)
    
class Select:
    def __init__(self, select_id:int):
        self.select_id = select_id
    def get_obj(self):
        return select_data_book(self.select_id)
    
get_list = Choice
get_select = Select