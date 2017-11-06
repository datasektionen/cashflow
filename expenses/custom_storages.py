from django.conf import settings

# storages is named django-storages and is in requirements
# noinspection PyPackageRequirements
from storages.backends.s3boto import S3BotoStorage

# noinspection PyAbstractClass
class MediaStorage(S3BotoStorage):
    location = settings.MEDIAFILES_LOCATION
    file_overwrite = False
