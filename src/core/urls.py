from collections import namedtuple

# Define the menu item structure
MenuItem = namedtuple('MenuItem', ['title', 'url']) # ['title', 'url', 'visible', 'permission']

# Create menu items with additional parameters
menu_items = [
    MenuItem('Home', '/'),
    MenuItem('Docs', '/docs'),
    MenuItem('Books', '/books/1'),
    MenuItem('Add Book', '/action/add_book'),
    MenuItem('Add Tag', '/action/add_tag'),
    MenuItem('Profile', '/profile'),
    MenuItem('Registration', '/register'),
    MenuItem('Login', '/login'),
    MenuItem('Logout', '/logout'),
]

def get_menu():
    return [item for item in menu_items]

# Example usage:
def choice_from_menu(name:str=None):
    if name:
        for i in menu_items:
            if name.lower() == i.title.lower() or name.lower() == i.url.lower():
                return i
print(choice_from_menu('Logout'))
# Add new item easily
#menu_items.append(MenuItem('Dashboard', '/dashboard', True, 'authenticated'))

# Remove item by condition
#menu_items = [item for item in menu_items if item.title != 'Add Tag']