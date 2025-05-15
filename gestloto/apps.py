from django.apps import AppConfig


class GestlotoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestloto'
    icon = 'fa fa-square-poll-vertical'  # FontAwesome icon for the app (optional)
    divider_title = "Apps"  # Title of the section divider in the sidebar (optional)
    priority = 0  # Determines the order of the app in the sidebar (higher values appear first, optional)
    hide = False 
