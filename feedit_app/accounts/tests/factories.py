import factory
from accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@feedit.online")
    first_name = "John"
    last_name = "Doe"
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    type = User.UserType.EMPLOYEE
