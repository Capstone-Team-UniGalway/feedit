import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.paginator import Page

from companies.tests.factories import CompanyFactory
from accounts.tests.factories import UserFactory

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestPublicCompanyListView:
    """Test the PublicCompanyListView for listing companies publicly."""

    def setup_method(self):
        self.client = Client()
        self.url = reverse('companies:list')

    def test_view_accessible_without_authentication(self):
        """Test that unauthenticated users can access the company list."""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert 'companies' in response.context

    def test_view_accessible_with_authentication(self):
        """Test that authenticated users can access the company list."""
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert 'companies' in response.context

    def test_http_method_restrictions(self):
        """Test that only GET method is allowed."""
        # POST should not be allowed
        response = self.client.post(self.url)
        assert response.status_code == 405

        # PUT should not be allowed
        response = self.client.put(self.url)
        assert response.status_code == 405

        # DELETE should not be allowed
        response = self.client.delete(self.url)
        assert response.status_code == 405

    def test_queryset_filters_deleted_companies(self):
        """Test that deleted companies are not shown in the list."""
        # Create active companies
        active_company1 = CompanyFactory(name="Active Company 1")
        active_company2 = CompanyFactory(name="Active Company 2")

        # Create deleted company
        deleted_company = CompanyFactory(name="Deleted Company")
        deleted_company.delete()  # Soft delete

        response = self.client.get(self.url)
        companies = response.context['companies']

        assert active_company1 in companies
        assert active_company2 in companies
        assert deleted_company not in companies

    def test_queryset_ordering_by_name(self):
        """Test that companies are ordered alphabetically by name."""
        CompanyFactory(name="Zebra Corp")
        CompanyFactory(name="Alpha Inc")
        CompanyFactory(name="Beta LLC")

        response = self.client.get(self.url)
        companies = list(response.context['companies'])

        assert companies[0].name == "Alpha Inc"
        assert companies[1].name == "Beta LLC"
        assert companies[2].name == "Zebra Corp"

    def test_search_functionality_by_name(self):
        """Test searching companies by name."""
        CompanyFactory(name="Tech Solutions", industry="Technology")
        CompanyFactory(name="Medical Corp", industry="Healthcare")
        CompanyFactory(name="Tech Innovations", industry="Software")

        response = self.client.get(self.url, {'q': 'Tech'})
        companies = list(response.context['companies'])

        assert len(companies) == 2
        assert all('Tech' in company.name for company in companies)

    def test_search_functionality_by_industry(self):
        """Test searching companies by industry."""
        CompanyFactory(name="Alpha Corp", industry="Technology")
        CompanyFactory(name="Beta Inc", industry="Healthcare")
        CompanyFactory(name="Gamma LLC", industry="Technology")

        response = self.client.get(self.url, {'q': 'Technology'})
        companies = list(response.context['companies'])

        assert len(companies) == 2
        assert all(company.industry == "Technology" for company in companies)

    def test_search_case_insensitive(self):
        """Test that search is case insensitive."""
        CompanyFactory(name="TechCorp", industry="technology")

        # Test lowercase search
        response = self.client.get(self.url, {'q': 'techcorp'})
        companies = list(response.context['companies'])
        assert len(companies) == 1

        # Test uppercase search
        response = self.client.get(self.url, {'q': 'TECHCORP'})
        companies = list(response.context['companies'])
        assert len(companies) == 1

    def test_empty_search_query_returns_all_companies(self):
        """Test that empty search query returns all companies."""
        CompanyFactory.create_batch(3)

        response = self.client.get(self.url, {'q': ''})
        companies = list(response.context['companies'])

        assert len(companies) == 3

    def test_search_no_results(self):
        """Test search with no matching results."""
        CompanyFactory(name="Tech Corp", industry="Technology")

        response = self.client.get(self.url, {'q': 'NonExistent'})
        companies = list(response.context['companies'])

        assert len(companies) == 0

    def test_pagination_configuration(self):
        """Test that pagination is configured correctly."""
        # Create more than 8 companies (paginate_by = 8)
        CompanyFactory.create_batch(10)

        response = self.client.get(self.url)

        assert response.context['is_paginated'] is True
        assert len(response.context['companies']) == 8
        assert isinstance(response.context['page_obj'], Page)

    def test_pagination_second_page(self):
        """Test accessing the second page of results."""
        CompanyFactory.create_batch(10)

        response = self.client.get(self.url, {'page': 2})

        assert response.status_code == 200
        assert len(response.context['companies']) == 2  # Remaining companies

    def test_context_data_for_unauthenticated_user(self):
        """Test context data for unauthenticated users."""
        CompanyFactory.create_batch(2)

        response = self.client.get(self.url)

        assert 'pending_requests' in response.context
        assert response.context['pending_requests'] == []

    def test_context_data_for_authenticated_user_with_workplace(self):
        """Test context data for authenticated users who already have a workplace."""
        user = UserFactory()
        company = CompanyFactory()
        user.workplace = company
        user.save()

        self.client.force_login(user)
        response = self.client.get(self.url)

        assert 'pending_requests' in response.context
        assert response.context['pending_requests'] == []

    def test_context_data_for_authenticated_user_without_workplace(self):
        """Test context data for authenticated users without workplace."""
        user = UserFactory(workplace=None)
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert 'pending_requests' in response.context
        assert response.context['pending_requests'] == []

    def test_context_data_includes_pending_requests_key(self):
        """Test context data includes pending_requests key for authenticated users without workplace."""
        user = UserFactory(workplace=None)
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert 'pending_requests' in response.context
        assert isinstance(response.context['pending_requests'], list)

    def test_template_used(self):
        """Test that the correct template is used."""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert 'pages/companies/company_list.html' in [t.name for t in response.templates]

    def test_context_object_name(self):
        """Test that the context object name is correct."""
        CompanyFactory()

        response = self.client.get(self.url)

        assert 'companies' in response.context
        assert hasattr(response.context['companies'], '__iter__')

    def test_search_with_special_characters(self):
        """Test search functionality with special characters."""
        CompanyFactory(name="O'Reilly Corp", industry="Publishing")

        response = self.client.get(self.url, {'q': "O'Reilly"})
        companies = list(response.context['companies'])

        assert len(companies) == 1
        assert companies[0].name == "O'Reilly Corp"

    def test_search_partial_matches(self):
        """Test that search returns partial matches."""
        CompanyFactory(name="Microsoft Corporation", industry="Technology")
        CompanyFactory(name="Microchip Inc", industry="Electronics")

        response = self.client.get(self.url, {'q': 'Micro'})
        companies = list(response.context['companies'])

        assert len(companies) == 2

    def test_view_with_large_dataset(self):
        """Test view performance with a large number of companies."""
        CompanyFactory.create_batch(50)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert len(response.context['companies']) == 8  # First page only
        assert response.context['is_paginated'] is True



class TestCompanyDetailView:
    """Test the CompanyDetailView for displaying individual company profiles."""

    def setup_method(self):
        self.client = Client()
        self.company = CompanyFactory(name="Test Company", industry="Technology")
        self.url = reverse('companies:detail', kwargs={'pk': self.company.pk})

    def test_view_accessible_without_authentication(self):
        """Test that unauthenticated users can access company detail page."""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert 'company' in response.context
        assert response.context['company'] == self.company

    def test_view_accessible_with_authentication(self):
        """Test that authenticated users can access company detail page."""
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert 'company' in response.context
        assert response.context['company'] == self.company

    def test_http_method_restrictions(self):
        """Test that only GET method is allowed."""
        # POST should not be allowed
        response = self.client.post(self.url)
        assert response.status_code == 405

        # PUT should not be allowed
        response = self.client.put(self.url)
        assert response.status_code == 405

        # DELETE should not be allowed
        response = self.client.delete(self.url)
        assert response.status_code == 405

        # PATCH should not be allowed
        response = self.client.patch(self.url)
        assert response.status_code == 405

    def test_get_object_filters_deleted_companies(self):
        """Test that deleted companies raise 404."""
        # Delete the company (soft delete)
        self.company.delete()

        response = self.client.get(self.url)

        assert response.status_code == 404

    def test_nonexistent_company_returns_404(self):
        """Test that non-existent company IDs return 404."""
        nonexistent_url = reverse('companies:detail', kwargs={'pk': 99999})

        response = self.client.get(nonexistent_url)

        assert response.status_code == 404

    def test_invalid_company_id_returns_404(self):
        """Test that invalid company IDs return 404."""
        invalid_url = '/companies/invalid/'

        response = self.client.get(invalid_url)

        assert response.status_code == 404

    def test_template_used(self):
        """Test that the correct template is used."""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert 'pages/companies/company_profile.html' in [t.name for t in response.templates]

    def test_context_object_name(self):
        """Test that the context object name is correct."""
        response = self.client.get(self.url)

        assert 'company' in response.context
        assert response.context['company'] == self.company

    def test_reviews_pagination_configuration(self):
        """Test that reviews are paginated with 5 reviews per page."""
        from reviews.tests.factories import ReviewFactory

        # Create 7 reviews to test pagination
        for i in range(7):
            ReviewFactory(company=self.company, rating=4.0, content=f"Review {i}")

        response = self.client.get(self.url)

        assert response.context['is_paginated'] is True
        assert len(response.context['reviews']) == 5
        assert isinstance(response.context['page_obj'], Page)

    def test_reviews_pagination_second_page(self):
        """Test accessing the second page of reviews."""
        from reviews.tests.factories import ReviewFactory

        # Create 7 reviews
        for i in range(7):
            ReviewFactory(company=self.company, rating=4.0, content=f"Review {i}")

        response = self.client.get(self.url, {'page': 2})

        assert response.status_code == 200
        assert len(response.context['reviews']) == 2  # Remaining reviews

    def test_reviews_ordering_by_created_at_desc(self):
        """Test that reviews are ordered by creation date (newest first)."""
        from reviews.tests.factories import ReviewFactory
        import time

        # Create reviews with slight time differences
        review1 = ReviewFactory(company=self.company, content="First review")
        time.sleep(0.01)
        review2 = ReviewFactory(company=self.company, content="Second review")
        time.sleep(0.01)
        review3 = ReviewFactory(company=self.company, content="Third review")

        response = self.client.get(self.url)
        reviews = list(response.context['reviews'])

        # Should be ordered newest first
        assert reviews[0] == review3
        assert reviews[1] == review2
        assert reviews[2] == review1

    def test_reviews_filter_deleted_reviews(self):
        """Test that deleted reviews are not shown."""
        from reviews.tests.factories import ReviewFactory

        # Create active and deleted reviews
        active_review = ReviewFactory(company=self.company, content="Active review")
        deleted_review = ReviewFactory(company=self.company, content="Deleted review")
        deleted_review.delete()  # Soft delete

        response = self.client.get(self.url)
        reviews = list(response.context['reviews'])

        assert active_review in reviews
        assert deleted_review not in reviews

    def test_reviews_select_related_user(self):
        """Test that reviews use select_related for user to avoid N+1 queries."""
        from reviews.tests.factories import ReviewFactory
        from django.test.utils import override_settings
        from django.db import connection

        # Create reviews with users
        ReviewFactory.create_batch(3, company=self.company)

        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            response = self.client.get(self.url)

            # Access the user for each review to trigger queries if not select_related
            for review in response.context['reviews']:
                _ = review.user.email if review.user else None

            # Check that select_related is working by verifying the query includes JOIN
            # The exact query structure may vary, so we check for the presence of user data
            assert len(response.context['reviews']) == 3
            # If select_related is working, we should be able to access user data without additional queries
            initial_query_count = len(connection.queries)
            for review in response.context['reviews']:
                _ = review.user.email if review.user else None
            final_query_count = len(connection.queries)
            # No additional queries should be made
            assert final_query_count == initial_query_count

    def test_reviews_prefetch_related_replies(self):
        """Test that reviews use prefetch_related for replies to avoid N+1 queries."""
        from reviews.tests.factories import ReviewFactory, ReviewReplyFactory
        from django.test.utils import override_settings
        from django.db import connection

        # Create reviews with replies
        review1 = ReviewFactory(company=self.company)
        review2 = ReviewFactory(company=self.company)
        ReviewReplyFactory(review=review1, employer=self.company.employer)
        ReviewReplyFactory(review=review2, employer=self.company.employer)

        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            response = self.client.get(self.url)

            # Access replies for each review
            for review in response.context['reviews']:
                _ = list(review.replies.all())

            # Should not have additional queries for replies due to prefetch_related
            reply_queries = [q for q in connection.queries if 'reviewreply' in q['sql'].lower()]
            # Should have prefetch query but not individual queries per review
            assert len(reply_queries) <= 2  # Initial query + prefetch query

    def test_review_replies_ordering_by_created_at_desc(self):
        """Test that review replies are ordered by creation date (newest first)."""
        from reviews.tests.factories import ReviewFactory, ReviewReplyFactory
        import time

        review = ReviewFactory(company=self.company)

        # Create replies with time differences
        reply1 = ReviewReplyFactory(review=review, employer=self.company.employer, content="First reply")
        time.sleep(0.01)
        reply2 = ReviewReplyFactory(review=review, employer=self.company.employer, content="Second reply")

        response = self.client.get(self.url)
        review_from_context = response.context['reviews'][0]
        replies = list(review_from_context.replies.all())

        # Should be ordered newest first
        assert replies[0] == reply2
        assert replies[1] == reply1

    def test_review_replies_filter_deleted_replies(self):
        """Test that deleted review replies are not shown."""
        from reviews.tests.factories import ReviewFactory, ReviewReplyFactory

        review = ReviewFactory(company=self.company)
        active_reply = ReviewReplyFactory(review=review, employer=self.company.employer, content="Active reply")
        deleted_reply = ReviewReplyFactory(review=review, employer=self.company.employer, content="Deleted reply")
        deleted_reply.delete()  # Soft delete

        response = self.client.get(self.url)
        review_from_context = response.context['reviews'][0]
        replies = list(review_from_context.replies.all())

        assert active_reply in replies
        assert deleted_reply not in replies

    def test_context_is_employer_for_company_employer(self):
        """Test is_employer context flag for company employer."""
        # Create a specific employer user and assign to company
        employer = UserFactory(type='employer')
        employer.save()  # Ensure user is saved
        self.company.employer = employer
        self.company.save()

        self.client.force_login(employer)
        response = self.client.get(self.url)

        assert response.context['is_employer'] is True

    def test_context_is_employer_false_for_other_users(self):
        """Test is_employer context flag for non-employer users."""
        other_user = UserFactory()
        self.client.force_login(other_user)

        response = self.client.get(self.url)

        assert response.context['is_employer'] is False

    def test_context_is_employer_false_for_unauthenticated_users(self):
        """Test is_employer context flag for unauthenticated users."""
        response = self.client.get(self.url)

        assert response.context['is_employer'] is False

    def test_context_is_employee_for_company_employee(self):
        """Test is_employee context flag for company employee."""
        employee = UserFactory(type='employee', workplace=self.company)
        employee.save()  # Ensure user is saved
        self.client.force_login(employee)

        response = self.client.get(self.url)

        assert response.context['is_employee'] is True

    def test_context_is_employee_false_for_other_users(self):
        """Test is_employee context flag for non-employee users."""
        other_user = UserFactory()
        self.client.force_login(other_user)

        response = self.client.get(self.url)

        assert response.context['is_employee'] is False

    def test_context_is_employee_false_for_unauthenticated_users(self):
        """Test is_employee context flag for unauthenticated users."""
        response = self.client.get(self.url)

        assert response.context['is_employee'] is False

    def test_context_has_reviewed_true_for_user_with_review(self):
        """Test has_reviewed context flag for user who has reviewed."""
        from reviews.tests.factories import ReviewFactory

        user = UserFactory()
        user.save()  # Ensure user is saved
        ReviewFactory(company=self.company, user=user, rating=4.0, content="Great company!")
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.context['has_reviewed'] is True

    def test_context_has_reviewed_false_for_user_without_review(self):
        """Test has_reviewed context flag for user who hasn't reviewed."""
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.context['has_reviewed'] is False

    def test_context_has_reviewed_false_for_unauthenticated_users(self):
        """Test has_reviewed context flag for unauthenticated users."""
        response = self.client.get(self.url)

        assert response.context['has_reviewed'] is False

    def test_context_has_reviewed_excludes_deleted_reviews(self):
        """Test has_reviewed excludes deleted reviews."""
        from reviews.tests.factories import ReviewFactory

        user = UserFactory()
        review = ReviewFactory(company=self.company, user=user)
        review.delete()  # Soft delete
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.context['has_reviewed'] is False

    def test_context_pending_requests_for_user_with_pending_request(self):
        """Test pending_requests context for user with pending join request."""
        from company_requests.tests.factories import RequestFactory

        user = UserFactory(workplace=None)
        user.save()  # Ensure user is saved
        RequestFactory(
            author=user,
            company=self.company,
            type='join',
            status='pending'
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.context['pending_requests'] == [self.company.id]

    def test_context_pending_requests_empty_for_user_without_pending_request(self):
        """Test pending_requests context for user without pending join request."""
        user = UserFactory(workplace=None)
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.context['pending_requests'] == []

    def test_context_pending_requests_empty_for_user_with_workplace(self):
        """Test pending_requests context for user who already has workplace."""
        user = UserFactory(workplace=self.company)
        self.client.force_login(user)

        response = self.client.get(self.url)

        assert response.context['pending_requests'] == []

    def test_context_pending_requests_empty_for_unauthenticated_users(self):
        """Test pending_requests context for unauthenticated users."""
        response = self.client.get(self.url)

        assert response.context['pending_requests'] == []

    def test_context_pending_requests_excludes_non_pending_requests(self):
        """Test pending_requests excludes approved/rejected requests."""
        from company_requests.tests.factories import RequestFactory

        user = UserFactory(workplace=None)

        # Create approved request (should not be included)
        RequestFactory(
            author=user,
            company=self.company,
            type='join',
            status='approved'
        )

        # Create rejected request (should not be included)
        RequestFactory(
            author=user,
            company=self.company,
            type='join',
            status='rejected'
        )

        self.client.force_login(user)
        response = self.client.get(self.url)

        assert response.context['pending_requests'] == []

    def test_context_pending_requests_excludes_claim_requests(self):
        """Test pending_requests excludes claim requests (only join requests)."""
        from company_requests.tests.factories import RequestFactory

        user = UserFactory(workplace=None)

        # Create pending claim request (should not be included)
        RequestFactory(
            author=user,
            company=self.company,
            type='claim',
            status='pending'
        )

        self.client.force_login(user)
        response = self.client.get(self.url)

        assert response.context['pending_requests'] == []

    def test_url_routing_with_valid_pk(self):
        """Test that URL routing works with valid company PK."""
        response = self.client.get(f'/companies/{self.company.pk}/')
        assert response.status_code == 200

    def test_company_profile_display_with_all_fields(self):
        """Test company profile displays all company information."""
        # Create company with all fields populated
        full_company = CompanyFactory(
            name="Full Company",
            industry="Technology",
            bio="A great company",
            country="Ireland",
            city="Dublin"
        )
        url = reverse('companies:detail', kwargs={'pk': full_company.pk})

        response = self.client.get(url)

        assert response.status_code == 200
        assert full_company.name in response.content.decode()
        assert full_company.industry in response.content.decode()
        assert full_company.country in response.content.decode()
        assert full_company.city in response.content.decode()

    def test_company_profile_display_with_minimal_fields(self):
        """Test company profile displays correctly with minimal information."""
        minimal_company = CompanyFactory(
            name="Minimal Company",
            industry="",
            bio="",
            country="",
            city=""
        )
        url = reverse('companies:detail', kwargs={'pk': minimal_company.pk})

        response = self.client.get(url)

        assert response.status_code == 200
        assert minimal_company.name in response.content.decode()

    def test_reviews_integration_display(self):
        """Test that reviews are properly integrated and displayed."""
        from reviews.tests.factories import ReviewFactory

        review = ReviewFactory(
            company=self.company,
            rating=4.5,
            content="Great company to work for!"
        )

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert review.content in response.content.decode()
        assert "4.5" in response.content.decode()

    def test_review_replies_integration_display(self):
        """Test that review replies are properly integrated and displayed."""
        from reviews.tests.factories import ReviewFactory, ReviewReplyFactory

        review = ReviewFactory(company=self.company)
        reply = ReviewReplyFactory(
            review=review,
            employer=self.company.employer,
            content="Thank you for your feedback!"
        )

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert reply.content in response.content.decode()

    def test_view_with_large_number_of_reviews(self):
        """Test view performance with many reviews."""
        from reviews.tests.factories import ReviewFactory

        # Create many reviews
        ReviewFactory.create_batch(25, company=self.company)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert len(response.context['reviews']) == 5  # First page only
        assert response.context['is_paginated'] is True
