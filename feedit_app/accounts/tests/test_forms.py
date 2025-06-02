import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from unittest.mock import Mock, patch

from accounts.forms import (
    CustomLoginForm, CustomSignupForm, UserProfileForm, CustomResetPasswordForm
)
from .factories import UserFactory

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestCustomLoginForm:
    """Test the CustomLoginForm."""

    def setup_method(self):
        self.factory = RequestFactory()

    def test_form_initialization(self):
        """Test form initializes with correct field attributes."""
        request = self.factory.get('/')
        form = CustomLoginForm(request=request)

        # Check field widgets and attributes
        assert isinstance(form.fields['login'].widget, forms.EmailInput)
        assert form.fields['login'].label == 'Email'
        assert 'input input-bordered w-full' in form.fields['login'].widget.attrs['class']
        assert form.fields['login'].widget.attrs['placeholder'] == 'Email address'

        assert isinstance(form.fields['password'].widget, forms.PasswordInput)
        assert 'input input-bordered w-full' in form.fields['password'].widget.attrs['class']
        assert form.fields['password'].widget.attrs['placeholder'] == 'Password'

        assert isinstance(form.fields['remember'].widget, forms.CheckboxInput)
        assert 'checkbox' in form.fields['remember'].widget.attrs['class']

    def test_valid_login_form(self):
        """Test form validation with valid data."""
        user = UserFactory(email='test@example.com')
        user.set_password('testpass123')
        user.save()

        request = self.factory.post('/')
        form_data = {
            'login': 'test@example.com',
            'password': 'testpass123',
            'remember': True
        }

        form = CustomLoginForm(request=request, data=form_data)

        # Mock the parent form's clean method to simulate successful authentication
        with patch('accounts.forms.AllauthLoginForm.clean') as mock_clean:
            mock_clean.return_value = form_data
            form.user = user  # Simulate user being set by parent form

            assert form.is_valid()

    def test_invalid_credentials(self):
        """Test form validation with invalid credentials."""
        request = self.factory.post('/')
        form_data = {
            'login': 'nonexistent@example.com',
            'password': 'wrongpassword',
        }

        form = CustomLoginForm(request=request, data=form_data)

        # Mock the parent form's clean method to simulate authentication failure
        with patch('accounts.forms.AllauthLoginForm.clean') as mock_clean:
            mock_clean.side_effect = forms.ValidationError("Invalid credentials")

            assert not form.is_valid()

    def test_deleted_user_blocked(self):
        """Test that deleted users are blocked from logging in."""
        user = UserFactory(email='deleted@example.com')
        user.set_password('testpass123')
        user.delete()  # Soft delete
        user.save()

        request = self.factory.post('/')
        form_data = {
            'login': 'deleted@example.com',
            'password': 'testpass123',
        }

        form = CustomLoginForm(request=request, data=form_data)

        # Mock the parent form's clean method to simulate successful authentication
        with patch('accounts.forms.AllauthLoginForm.clean') as mock_clean:
            mock_clean.return_value = form_data
            form.user = user  # Simulate deleted user being set by parent form

            assert not form.is_valid()
            assert 'This account has been closed.' in str(form.errors)

    def test_active_user_allowed(self):
        """Test that active (non-deleted) users can log in."""
        user = UserFactory(email='active@example.com')
        user.set_password('testpass123')
        user.save()

        request = self.factory.post('/')
        form_data = {
            'login': 'active@example.com',
            'password': 'testpass123',
        }

        form = CustomLoginForm(request=request, data=form_data)

        # Mock the parent form's clean method to simulate successful authentication
        with patch('accounts.forms.AllauthLoginForm.clean') as mock_clean:
            mock_clean.return_value = form_data
            form.user = user  # Simulate active user being set by parent form

            assert form.is_valid()


class TestCustomSignupForm:
    """Test the CustomSignupForm."""

    def test_form_initialization_without_role(self):
        """Test form initializes correctly without initial role."""
        form = CustomSignupForm()

        # Check that all required fields are present
        assert 'first_name' in form.fields
        assert 'last_name' in form.fields
        assert 'type' in form.fields
        assert 'email' in form.fields
        assert 'password1' in form.fields
        assert 'password2' in form.fields

        # Check field attributes
        assert form.fields['first_name'].max_length == 50
        assert form.fields['last_name'].max_length == 50
        assert form.fields['type'].choices == User.UserType.choices

    def test_form_initialization_with_role(self):
        """Test form initializes with initial role."""
        form = CustomSignupForm(initial_role='employer')

        assert form.fields['type'].initial == 'employer'

    def test_field_styling(self):
        """Test that form fields have correct CSS classes."""
        form = CustomSignupForm()

        # Check CSS classes
        assert 'input input-bordered w-full' in form.fields['first_name'].widget.attrs['class']
        assert 'input input-bordered w-full' in form.fields['last_name'].widget.attrs['class']
        assert 'select select-bordered w-full' in form.fields['type'].widget.attrs['class']
        assert 'input input-bordered w-full' in form.fields['email'].widget.attrs['class']
        assert 'input input-bordered w-full' in form.fields['password1'].widget.attrs['class']
        assert 'input input-bordered w-full' in form.fields['password2'].widget.attrs['class']

        # Check placeholders
        assert form.fields['first_name'].widget.attrs['placeholder'] == 'First name'
        assert form.fields['last_name'].widget.attrs['placeholder'] == 'Last name'
        assert form.fields['email'].widget.attrs['placeholder'] == 'Email address'
        assert form.fields['password1'].widget.attrs['placeholder'] == 'Password'
        assert form.fields['password2'].widget.attrs['placeholder'] == 'Confirm password'

    def test_valid_signup_form(self):
        """Test form validation with valid data."""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'type': 'employee',
        }

        form = CustomSignupForm(data=form_data)

        # Mock the parent form's validation
        with patch('accounts.forms.AllauthSignupForm.is_valid') as mock_valid:
            mock_valid.return_value = True
            with patch('accounts.forms.AllauthSignupForm.save') as mock_save:
                mock_user = UserFactory.build()
                mock_save.return_value = mock_user

                assert form.is_valid()

    def test_invalid_signup_form(self):
        """Test form validation with invalid data."""
        form_data = {
            'first_name': '',  # Required field
            'last_name': '',   # Required field
            'email': 'invalid-email',  # Invalid email
            'password1': 'pass',  # Too short
            'password2': 'different',  # Doesn't match
            'type': 'invalid_type',  # Invalid choice
        }

        form = CustomSignupForm(data=form_data)

        assert not form.is_valid()

    def test_save_method(self):
        """Test that save method correctly sets user attributes."""
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'type': 'employer',
        }

        form = CustomSignupForm(data=form_data)

        # Mock the parent form's save method
        mock_user = Mock()
        mock_request = Mock()

        with patch('accounts.forms.AllauthSignupForm.save') as mock_save:
            mock_save.return_value = mock_user
            with patch('accounts.forms.AllauthSignupForm.is_valid') as mock_valid:
                mock_valid.return_value = True
                form.cleaned_data = form_data

                result = form.save(mock_request)

                assert result.first_name == 'Jane'
                assert result.last_name == 'Smith'
                assert result.type == 'employer'
                mock_user.save.assert_called_once()


class TestUserProfileForm:
    """Test the UserProfileForm."""

    def test_form_initialization(self):
        """Test form initializes with correct fields and widgets."""
        user = UserFactory()
        form = UserProfileForm(instance=user)

        # Check that all required fields are present
        assert 'first_name' in form.fields
        assert 'last_name' in form.fields
        assert 'job_title' in form.fields
        assert 'bio' in form.fields
        assert 'privacy' in form.fields

        # Check field requirements
        assert form.fields['job_title'].required == True
        assert form.fields['bio'].required == True
        assert form.fields['bio'].min_length == 20

        # Check field attributes
        assert form.fields['job_title'].max_length == 100
        assert form.fields['job_title'].help_text == "Your current role or position"
        assert form.fields['bio'].help_text == "Tell us about yourself"

    def test_field_styling(self):
        """Test that form fields have correct CSS classes."""
        form = UserProfileForm()

        # Check CSS classes
        assert 'input input-bordered w-full' in form.fields['first_name'].widget.attrs['class']
        assert 'input input-bordered w-full' in form.fields['last_name'].widget.attrs['class']
        assert 'input input-bordered w-full' in form.fields['job_title'].widget.attrs['class']
        assert 'textarea textarea-bordered w-full' in form.fields['bio'].widget.attrs['class']
        assert 'select select-bordered w-full' in form.fields['privacy'].widget.attrs['class']

    def test_valid_profile_form(self):
        """Test form validation with valid data."""
        user = UserFactory()
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'job_title': 'Software Engineer',
            'bio': 'This is a comprehensive bio that meets the minimum length requirement for the form validation.',
            'privacy': 'public',
        }

        form = UserProfileForm(data=form_data, instance=user)

        assert form.is_valid()

    def test_invalid_profile_form_missing_required(self):
        """Test form validation with missing required fields."""
        user = UserFactory()
        form_data = {
            'first_name': '',  # Required
            'last_name': '',   # Required
            'job_title': '',   # Required
            'bio': '',         # Required
            'privacy': 'public',
        }

        form = UserProfileForm(data=form_data, instance=user)

        assert not form.is_valid()
        assert 'first_name' in form.errors
        assert 'last_name' in form.errors
        assert 'job_title' in form.errors
        assert 'bio' in form.errors

    def test_invalid_profile_form_bio_too_short(self):
        """Test form validation with bio too short."""
        user = UserFactory()
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'job_title': 'Developer',
            'bio': 'Too short',  # Less than 20 characters
            'privacy': 'public',
        }

        form = UserProfileForm(data=form_data, instance=user)

        assert not form.is_valid()
        assert 'bio' in form.errors

    def test_help_texts(self):
        """Test that help texts are correctly set."""
        form = UserProfileForm()

        assert form.fields['job_title'].help_text == "Your current role or position"
        assert form.fields['bio'].help_text == "Tell us about yourself"
        assert "Public: any user can view" in form.fields['privacy'].help_text


class TestCustomResetPasswordForm:
    """Test the CustomResetPasswordForm."""

    def test_valid_email_active_user(self):
        """Test form validation with valid email for active user."""
        user = UserFactory(email='active@example.com')

        form_data = {'email': 'active@example.com'}
        form = CustomResetPasswordForm(data=form_data)

        # Mock the parent form's clean_email method
        with patch('accounts.forms.ResetPasswordForm.clean_email') as mock_clean:
            mock_clean.return_value = 'active@example.com'
            form.users = [user]  # Simulate users being set by parent form

            assert form.is_valid()

    def test_deleted_user_blocked(self):
        """Test that deleted users are blocked from password reset."""
        user = UserFactory(email='deleted@example.com')
        user.delete()  # Soft delete

        form_data = {'email': 'deleted@example.com'}
        form = CustomResetPasswordForm(data=form_data)

        # Mock the parent form's clean_email method
        with patch('accounts.forms.ResetPasswordForm.clean_email') as mock_clean:
            mock_clean.return_value = 'deleted@example.com'
            form.users = [user]  # Simulate deleted user being set by parent form

            assert not form.is_valid()
            assert 'This account has been closed.' in str(form.errors)

    def test_nonexistent_email(self):
        """Test form validation with nonexistent email."""
        form_data = {'email': 'nonexistent@example.com'}
        form = CustomResetPasswordForm(data=form_data)

        # Mock the parent form's clean_email method
        with patch('accounts.forms.ResetPasswordForm.clean_email') as mock_clean:
            mock_clean.return_value = 'nonexistent@example.com'
            form.users = []  # No users found

            assert form.is_valid()  # Should still be valid for security reasons

    def test_multiple_users_with_deleted(self):
        """Test form validation with multiple users where one is deleted."""
        active_user = UserFactory(email='active@example.com')
        deleted_user = UserFactory(email='deleted@example.com')
        deleted_user.delete()  # Soft delete

        form_data = {'email': 'test@example.com'}
        form = CustomResetPasswordForm(data=form_data)

        # Mock the parent form's clean_email method
        with patch('accounts.forms.ResetPasswordForm.clean_email') as mock_clean:
            mock_clean.return_value = 'test@example.com'
            form.users = [active_user, deleted_user]  # Mixed users

            assert not form.is_valid()
            assert 'This account has been closed.' in str(form.errors)
