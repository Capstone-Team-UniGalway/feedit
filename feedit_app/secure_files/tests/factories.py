import factory
from django.core.files.uploadedfile import SimpleUploadedFile
from secure_files.models import SecureFile
from accounts.models import User
from django.contrib.contenttypes.models import ContentType
from accounts.tests.factories import UserFactory


class SecureFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SecureFile

    # By default, we attach to a user
    content_object = factory.SubFactory(UserFactory)
    content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.content_object)
    )
    object_id = factory.SelfAttribute("content_object.id")

    # Dynamically decide who uploaded the file
    @factory.lazy_attribute
    def uploaded_by(self):
        if isinstance(self.content_object, User):
            return self.content_object
        return UserFactory()

    file = SimpleUploadedFile(
        "profile.jpg", b"fake_image_data", content_type="image/jpeg"
    )
    filename = "profile.jpg"
    size = 1024
