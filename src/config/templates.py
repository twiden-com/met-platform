from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates", auto_reload=False, enable_async=True)

async def render(template_name: str, request, **kwargs):
    context = {"request": request, **kwargs}
    return templates.TemplateResponse(template_name, context)