# -*- coding: utf-8 -*-

import json
import datetime
from flask import current_app, url_for
from werkzeug.datastructures import MultiDict

from purchasing.extensions import mail, db
from purchasing.opportunities.models import Vendor

from purchasing_test.util import insert_a_role, insert_a_user, insert_an_opportunity

from purchasing_test.integration.opportunities.test_opportunities_base import (
    TestOpportunitiesFrontBase, TestOpportunitiesAdminBase
)

class TestOpportunities(TestOpportunitiesFrontBase):
    render_templates = True

    def test_templates(self):
        # insert our opportunity, users
        admin_role = insert_a_role('admin')
        admin = insert_a_user(role=admin_role)

        opportunity = insert_an_opportunity(
            contact=admin, created_by=admin,
            is_public=True, planned_publish=datetime.date.today() - datetime.timedelta(1),
            planned_submission_start=datetime.date.today() + datetime.timedelta(2),
            planned_submission_end=datetime.datetime.today() + datetime.timedelta(2)
        )

        for rule in current_app.url_map.iter_rules():

            _endpoint = rule.endpoint.split('.')
            # filters out non-beacon endpoints
            if (len(_endpoint) > 1 and _endpoint[1] == 'static') or \
                _endpoint[0] != ('opportunities', 'opportunities_admin'):
                    continue
            else:
                if '<int:' in rule.rule:
                    response = self.client.get(url_for(rule.endpoint, opportunity_id=opportunity.id))
                else:
                    response = self.client.get(rule.rule)
                self.assert200(response)

    def test_index(self):
        response = self.client.get('/beacon/')
        self.assert200(response)
        self.assert_template_used('opportunities/front/splash.html')

        self.client.post('/beacon/signup?email=BADEMAIL', follow_redirects=True)

        with self.client.session_transaction() as session:
            assert 'email' not in session

        # assert clicking signup works as expected
        signup = self.client.post('/beacon/signup?email=foo@foo.com', follow_redirects=True)
        self.assertTrue('foo@foo.com' in signup.data)

    def test_signup(self):
        admin_role = insert_a_role('admin')
        superadmin_role = insert_a_role('superadmin')

        insert_a_user(role=admin_role)
        insert_a_user(email='foo2@foo.com', role=superadmin_role)

        response = self.client.get('/beacon/signup')
        self.assert200(response)
        subcats = json.loads(self.get_context_variable('subcategories'))

        # assert three categories (plus the total category)
        self.assertEquals(len(subcats.keys()), 4)
        # assert five total subcatgories (plus 5 in the total field)
        self.assertEquals(len([item for sublist in subcats.values() for item in sublist]), 10)

        # assert email, business, categories needed
        no_email_post = self.client.post('/beacon/signup', data=dict(
            first_name='foo'
        ))

        self.assert200(no_email_post)
        self.assertTrue(no_email_post.data.count('alert-danger'), 3)
        # ensure that there are two required field notes
        self.assertTrue(no_email_post.data.count('This field is required'), 2)

        # assert valid email address
        invalid_email_post = self.client.post('/beacon/signup', data=dict(
            email='INVALID',
            business_name='test'
        ))

        self.assert200(invalid_email_post)
        self.assertTrue(invalid_email_post.data.count('alert-danger'), 1)
        self.assertTrue(invalid_email_post.data.count('Invalid email address.'), 1)

        # assert you need at least one category
        invalid_no_categories = self.client.post('/beacon/signup', data=dict(
            email='foo@foo.com',
            business_name='foo'
        ))
        self.assert200(invalid_no_categories)
        self.assertTrue(invalid_no_categories.data.count('alert-danger'), 1)
        self.assertTrue(invalid_no_categories.data.count('You must select at least one!'), 1)

        # assert valid categories

        with mail.record_messages() as outbox:

            # successful post with only one set of subcategories
            success_post = self.client.post('/beacon/signup', data={
                'email': 'foo@foo.com',
                'business_name': 'foo',
                'subcategories-1': 'on',
                'categories': 'Apparel',
                'subscribed_to_newsletter': True
            })

            with self.client.session_transaction() as session:
                assert 'email' in session
                assert 'business_name' in session
                self.assertEquals(session['email'], 'foo@foo.com')
                self.assertEquals(session['business_name'], 'foo')

            self.assertEquals(success_post.status_code, 302)
            self.assertEquals(success_post.location, 'http://localhost/beacon/')
            # should send three emails
            # one to the vendor, one to the admins
            self.assertEquals(len(outbox), 2)
            self.assertEquals(Vendor.query.count(), 1)
            self.assertTrue(Vendor.query.first().subscribed_to_newsletter)
            self.assertEquals(len(Vendor.query.first().categories), 1)
            self.assert_flashes(
                'Thank you for signing up! Check your email for more information', 'alert-success'
            )

            # successful post with two sets of subcategories
            success_post_everything = self.client.post('/beacon/signup', data={
                'email': 'foo2@foo.com',
                'business_name': 'foo',
                'subcategories-1': 'on',
                'subcategories-2': 'on',
                'subcategories-3': 'on',
                'subcategories-4': 'on',
                'subcategories-5': 'on',
                'categories': 'Apparel',
                'subscribed_to_newsletter': True
            })

            self.assertEquals(success_post_everything.status_code, 302)
            self.assertEquals(success_post_everything.location, 'http://localhost/beacon/')
            self.assertEquals(len(outbox), 4)
            self.assertEquals(Vendor.query.count(), 2)
            self.assertEquals(len(Vendor.query.filter(Vendor.email == 'foo2@foo.com').first().categories), 5)
            self.assert_flashes('Thank you for signing up! Check your email for more information', 'alert-success')

            # successful post with existing email should update the profile, not send message
            success_post_old_email = self.client.post('/beacon/signup', data={
                'email': 'foo2@foo.com',
                'business_name': 'foo',
                'subcategories-1': 'on',
                'subcategories-2': 'on',
                'subcategories-3': 'on',
                'categories': 'Apparel',
                'subscribed_to_newsletter': True
            })

            self.assertEquals(success_post_old_email.status_code, 302)
            self.assertEquals(success_post_old_email.location, 'http://localhost/beacon/')
            self.assertEquals(len(outbox), 4)
            self.assertEquals(Vendor.query.count(), 2)
            self.assertEquals(len(Vendor.query.filter(Vendor.email == 'foo2@foo.com').first().categories), 5)
            self.assert_flashes(
                "You are already signed up! Your profile was updated with this new information", 'alert-info'
            )

            admin_mail, vendor_mail = 0, 0
            for _mail in outbox:
                if 'new vendor has signed up on beacon' in _mail.subject:
                    admin_mail += 1
                if 'Thank you for signing up' in _mail.subject:
                    vendor_mail += 1

            self.assertEquals(admin_mail, 2)
            self.assertEquals(vendor_mail, 2)

            with self.client.session_transaction() as session:
                assert 'email' in session
                assert 'business_name' in session
                self.assertEquals(session['email'], 'foo2@foo.com')
                self.assertEquals(session['business_name'], 'foo')

    def test_signup_different_business_name(self):
        self.client.post('/beacon/signup', data={
            'email': 'foo2@foo.com',
            'business_name': 'foo',
            'subcategories-1': 'on',
            'subcategories-2': 'on',
            'subcategories-3': 'on',
            'categories': 'Apparel',
            'subscribed_to_newsletter': True
        })
        self.assertEquals(Vendor.query.count(), 1)
        self.assertEquals(Vendor.query.first().email, 'foo2@foo.com')
        self.assertEquals(Vendor.query.first().business_name, 'foo')

        self.client.post('/beacon/signup', data={
            'email': 'foo2@foo.com',
            'business_name': 'bar',
            'subcategories-1': 'on',
            'subcategories-2': 'on',
            'subcategories-3': 'on',
            'categories': 'Apparel',
            'subscribed_to_newsletter': True
        })
        self.assertEquals(Vendor.query.count(), 1)
        self.assertEquals(Vendor.query.first().email, 'foo2@foo.com')
        self.assertEquals(Vendor.query.first().business_name, 'bar')

    def test_manage_subscriptions(self):
        self.client.post('/beacon/signup', data={
            'email': 'foo2@foo.com',
            'business_name': 'foo',
            'subcategories-1': 'on',
            'subcategories-2': 'on',
            'subcategories-3': 'on',
            'categories': 'Apparel',
            'subscribed_to_newsletter': True
        })

        manage = self.client.post('/beacon/manage', data=dict(
            email='foo2@foo.com'
        ))

        self.assert200(manage)
        form = self.get_context_variable('form')
        self.assertEquals(len(form.categories.choices), 3)

        # it shouldn't unsubscribe you if you click the wrong button
        not_unsub_button = self.client.post('/beacon/manage', data=dict(
            email='foo2@foo.com',
            categories=[1, 2],
        ))

        self.assert200(not_unsub_button)
        form = self.get_context_variable('form')
        self.assertEquals(len(form.categories.choices), 3)

        unsubscribe = self.client.post('/beacon/manage', data=dict(
            email='foo2@foo.com',
            categories=[1, 2],
            button='Update email preferences'
        ))

        self.assert200(unsubscribe)
        form = self.get_context_variable('form')
        self.assertEquals(len(form.categories.choices), 1)

        # it shouldn't matter if you somehow unsubscribe from things
        # you are accidentally subscribed to
        unsubscribe_all = self.client.post('/beacon/manage', data=dict(
            email='foo2@foo.com',
            categories=[3, 5, 6],
            button='Update email preferences',
            subscribed_to_newsletter=False
        ))

        self.assert200(unsubscribe_all)
        self.assertTrue('You are not subscribed to anything!' in unsubscribe_all.data)

class TestOpportunitiesSubscriptions(TestOpportunitiesAdminBase):
    def test_signup_for_multiple_opportunities(self):
        self.assertEquals(Vendor.query.count(), 1)
        # duplicates should get filtered out
        post = self.client.post('/beacon/opportunities', data=MultiDict([
            ('email', 'new@foo.com'), ('business_name', 'foo'),
            ('opportunity', str(self.opportunity3.id)),
            ('opportunity', str(self.opportunity4.id)),
            ('opportunity', str(self.opportunity3.id)),
            ('opportunity', str(self.opportunity1.id))
        ]))

        self.assertEquals(Vendor.query.count(), 2)

        # should subscribe that vendor to the opportunity
        self.assertEquals(len(Vendor.query.filter(Vendor.email == 'new@foo.com').first().opportunities), 3)
        for i in Vendor.query.get(1).opportunities:
            self.assertTrue(i.id in [self.opportunity1.id, self.opportunity3.id, self.opportunity4.id])

        # should redirect and flash properly
        self.assertEquals(post.status_code, 302)
        self.assert_flashes('Successfully subscribed for updates!', 'alert-success')

    def test_unicode_get(self):
        self.login_user(self.admin)
        self.assert200(self.client.get('/beacon/opportunities/{}'.format(self.opportunity1.id)))

    def test_signup_for_opportunity(self):
        self.opportunity1.is_public = True
        self.opportunity1.planned_publish = datetime.date.today() - datetime.timedelta(2)
        db.session.commit()

        with mail.record_messages() as outbox:
            self.assertEquals(Vendor.query.count(), 1)
            post = self.client.post('/beacon/opportunities/{}'.format(self.opportunity1.id), data={
                'email': 'new@foo.com', 'business_name': 'foo'
            })
            # should create a new vendor
            self.assertEquals(Vendor.query.count(), 2)

            # should subscribe that vendor to the opportunity
            self.assertEquals(len(Vendor.query.filter(Vendor.email == 'new@foo.com').first().opportunities), 1)
            self.assertTrue(
                self.opportunity1.id in [
                    i.id for i in Vendor.query.filter(Vendor.email == 'new@foo.com').first().opportunities
                ]
            )

            # should redirect and flash properly
            self.assertEquals(post.status_code, 302)
            self.assert_flashes('Successfully subscribed for updates!', 'alert-success')

            self.assertEquals(len(outbox), 1)

    def test_signup_for_opportunity_session(self):
        self.client.post('/beacon/opportunities', data={
            'business_name': 'NEW NAME',
            'email': 'new@foo.com',
            'opportunity': self.opportunity2.id
        })

        self.assertEquals(Vendor.query.count(), 2)
        self.assertEquals(len(Vendor.query.filter(Vendor.email == 'new@foo.com').first().opportunities), 1)

        with self.client.session_transaction() as session:
            self.assertEquals(session['email'], 'new@foo.com')
            self.assertEquals(session['business_name'], 'NEW NAME')

    def test_opportunity_subscription_different_business_name(self):
        with self.client.session_transaction() as session:
            session['email'] = self.vendor.email
            session['business_name'] = self.vendor.business_name

            self.client.post('/beacon/opportunities', data={
                'business_name': 'NEW NAME',
                'email': self.vendor.email,
                'opportunity': self.opportunity2.id
            })

            self.assertEquals(Vendor.query.count(), 1)
            self.assertEquals(Vendor.query.first().business_name, 'NEW NAME')
