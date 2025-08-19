from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserGraph(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    memo = models.TextField(blank=True)
    fu = models.IntegerField()
    rr_min = models.FloatField()
    rr_max = models.FloatField()
    chisq_p = models.FloatField()
    fisher_p = models.FloatField()
    disease_names = models.TextField()  # 콤마/JSON 등으로 저장
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
