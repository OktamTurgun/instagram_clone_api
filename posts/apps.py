from django.apps import AppConfig


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'
    verbose_name = 'Posts'
    
    def ready(self):
        """
        Import signals when Django starts.
        
        This method is called when Django initializes the app.
        We import signals here to ensure they are registered.
        """
        import posts.signals