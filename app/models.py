from django.db import models

# Create your models here.
class Code(models.Model):
    name = models.CharField(max_length=55)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    address = models.TextField()
    user_type = models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
from django.db import models

class CodeHistory(models.Model):

    email = models.EmailField()

    action_type = models.CharField(max_length=50)
    # review / generate / analyze

    language = models.CharField(max_length=50, blank=True, null=True)

    input_code = models.TextField()

    output_result = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email