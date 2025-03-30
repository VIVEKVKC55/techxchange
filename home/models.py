from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

class PromotionBanner(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='promotion_banners/',storage=S3Boto3Storage(), blank=True,null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title if self.title else "Promotion Banner"

    def delete(self, *args, **kwargs):
        """Delete image from S3 when model is deleted"""
        if self.image:
            self.image.delete()
        super().delete(*args, **kwargs)

    class Meta:
        db_table = 'promotion_banner'
