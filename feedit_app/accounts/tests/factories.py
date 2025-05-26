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


class FullyActivatedUserFactory(UserFactory):
    """Factory for creating fully activated users with all requirements met."""

    job_title = "Software Engineer"
    bio = "This is a test bio that meets the minimum length requirements for the user profile."

    @factory.post_generation
    def setup_activation(self, create, extracted, **kwargs):
        if not create:
            return

        # Create verified email address
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=self,
            email=self.email,
            verified=True,
            primary=True
        )

        # Create MFA authenticator
        from allauth.mfa.models import Authenticator
        Authenticator.objects.create(
            user=self,
            type="totp",
            data={"secret": "test_secret"}
        )
