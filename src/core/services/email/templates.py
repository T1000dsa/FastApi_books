from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.core.config.config import frontend_root

class EmailTemplates:
    def __init__(self, template_dir: str = str(frontend_root)):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def render_template(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(context)