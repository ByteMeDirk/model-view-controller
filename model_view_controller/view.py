from jinja2 import Template


class View:
    @staticmethod
    def render_template(template_string: str, context: dict) -> str:
        """
        Render a Jinja2 template with the given context.

        Args:
            template_string (str): Jinja2 template string
            context (dict): Context data for rendering

        Returns:
            str: Rendered template
        """
        template = Template(template_string)
        return template.render(context)
