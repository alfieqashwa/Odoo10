# -*- coding: utf-8 -*-
import requests
import werkzeug
from datetime import datetime
import json
import math
import base64
import logging
_logger = logging.getLogger(__name__)
from openerp.addons.website.models.website import slug

import openerp.http as http
from openerp.http import request

class WebsiteBusinessDiretoryController(http.Controller):

    @http.route('/directory', type="http", auth="public", website=True)
    def directory_search(self, **kwargs):
        return http.request.render('website_business_directory.directory_search', {} )

    @http.route('/directory/register', type="http", auth="public", website=True)
    def directory_register(self, **kwargs):
        return http.request.render('website_business_directory.directory_register', {} )

    @http.route('/directory/register/process', type="http", auth="public", website=True)
    def directory_register_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value
	    
	#Create the new user
	new_user = request.env['res.users'].sudo().create({'name': values['name'], 'login': values['email'], 'email': values['email'], 'password': values['password'] })
	
	#Add the user to the business directory group
	directory_group = request.env['ir.model.data'].sudo().get_object('website_business_directory', 'directory_group')
        directory_group.users = [(4, new_user.id)]

        #Remove 'Contact Creation' permission        
	contact_creation_group = request.env['ir.model.data'].sudo().get_object('base', 'group_partner_manager')
        contact_creation_group.users = [(3,new_user.id)]

        #Also remove them as an employee
	human_resources_group = request.env['ir.model.data'].sudo().get_object('base', 'group_user')
        human_resources_group.users = [(3,new_user.id)]

        #Automatically sign the new user in
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
	request.session.authenticate(request.env.cr.dbname, values['email'], values['password'])

        #Redirect them to thier account page
        return werkzeug.utils.redirect("/directory/account")

    @http.route('/directory/account', type='http', auth="user", website=True)
    def directory_account(self, **kwargs):
        businesses = request.env['res.partner'].sudo().search([('in_directory','=', True), ('business_owner','=', request.env.user.id)])
        return http.request.render('website_business_directory.directory_account', {'businesses': businesses} )

    @http.route('/directory/account/business/add', type='http', auth="user", website=True)
    def directory_account_business_add(self, **kwargs):
        countries = request.env['res.country'].search([])
        states = request.env['res.country.state'].search([])
        return http.request.render('website_business_directory.directory_account_business_add', {'countries': countries,'states': states} )

    @http.route('/directory/account/business/add/process', type='http', auth="user", website=True)
    def directory_account_business_add_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value

        business_logo = base64.encodestring(values['logo'].read() )
                
        insert_values = {'business_owner': request.env.user.id, 'in_directory': True, 'name': values['name']}

        if 'email' in values: insert_values['email'] = values['email']
        if 'street' in values: insert_values['street'] = values['street']
        if 'city' in values: insert_values['city'] = values['city']
        if 'state_id' in values: insert_values['state_id'] = values['state']
        if 'country_id' in values: insert_values['country_id'] = values['country']
        if 'zip' in values: insert_values['zip'] = values['zip']
        if 'directory_description' in values: insert_values['directory_description'] = values['directory_description']
        if 'directory_monday_start' in values: insert_values['directory_monday_start'] = values['directory_monday_start']
        if 'directory_monday_end' in values: insert_values['directory_monday_end'] = values['directory_monday_end']
        if 'directory_tuesday_start' in values: insert_values['directory_tuesday_start'] = values['directory_tuesday_start']
        if 'directory_tuesday_end' in values: insert_values['directory_tuesday_end'] = values['directory_tuesday_end']
        if 'directory_wednbesday_start' in values: insert_values['directory_wednbesday_start'] = values['directory_wednesday_start']
        if 'directory_wednbesday_end' in values: insert_values['directory_wednbesday_end'] = values['directory_wednesday_end']
        if 'directory_thursday_start' in values: insert_values['directory_thursday_start'] = values['directory_thursday_start']
        if 'directory_thursday_end' in values: insert_values['directory_thursday_end'] = values['directory_thursday_end']
        if 'directory_friday_start' in values: insert_values['directory_friday_start'] = values['directory_friday_start']
        if 'directory_friday_end' in values: insert_values['directory_friday_end'] = values['directory_friday_end']
        if 'directory_saturday_start' in values: insert_values['directory_saturday_start'] = values['directory_saturday_start']
        if 'directory_saturday_end' in values: insert_values['directory_saturday_end'] = values['directory_saturday_end']
        if 'directory_sunday_start' in values: insert_values['directory_sunday_start'] = values['directory_sunday_start']
        if 'directory_sunday_end' in values: insert_values['directory_sunday_end'] = values['directory_sunday_end']
        if 'website' in values: insert_values['website'] = values['website']
        if 'allow_restaurant_booking' in values: insert_values['allow_restaurant_booking'] = True
        insert_values['image'] =  business_logo
        
        new_listing = request.env['res.partner'].sudo().create(insert_values)

        #Redirect them to thier account page
        return werkzeug.utils.redirect("/directory/account")

    @http.route('/directory/account/business/edit/<model("res.partner"):directory_company>', type='http', auth="user", website=True)
    def directory_account_business_edit(self, directory_company, **kwargs):
        if directory_company.in_directory and directory_company.business_owner.id == request.env.user.id:
            countries = request.env['res.country'].search([])
            states = request.env['res.country.state'].search([])
            return http.request.render('website_business_directory.directory_account_business_edit', {'directory_company': directory_company, 'countries': countries,'states': states} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/account/business/edit/process', type='http', auth="user", website=True)
    def directory_account_business_edit_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value

        business_logo = base64.encodestring(values['logo'].read() )

        existing_record = request.env['res.partner'].browse( int(values['business_id'] ) )
        
        if existing_record.in_directory and existing_record.business_owner.id == request.env.user.id:
            updated_listing = existing_record.sudo().write({'name': values['name'], 'email': values['email'], 'street': values['street'], 'city': values['city'], 'state_id': values['state'], 'country_id': values['country'], 'zip': values['zip'], 'directory_description': values['description'], 'directory_monday_start': values['directory_monday_start'], 'directory_monday_end': values['directory_monday_end'], 'directory_tuesday_start': values['directory_tuesday_start'], 'directory_tuesday_end': values['directory_tuesday_end'], 'directory_wednbesday_start': values['directory_wednesday_start'], 'directory_wednbesday_end': values['directory_wednesday_end'], 'directory_thursday_start': values['directory_thursday_start'], 'directory_thursday_end': values['directory_thursday_end'], 'directory_friday_start': values['directory_friday_start'], 'directory_friday_end': values['directory_friday_end'], 'directory_saturday_start': values['directory_saturday_start'], 'directory_saturday_end': values['directory_saturday_end'], 'directory_sunday_start': values['directory_sunday_start'], 'directory_sunday_end': values['directory_sunday_end'], 'allow_restaurant_booking': values['allow_restaurant_booking'], 'image': business_logo })

            #Redirect them to thier account page
            return werkzeug.utils.redirect("/directory/account")
        else:
            return "Permission Denied"


    @http.route('/directory/account/business/upgrade/<model("res.partner"):directory_company>', type='http', auth="user", website=True)
    def directory_account_business_upgrade(self, directory_company, **kwargs):
        if directory_company.in_directory and directory_company.business_owner.id == request.env.user.id:
            plan_levels = request.env['website.directory.level'].search([('id','!=', directory_company.listing_level.id)])
            return http.request.render('website_business_directory.directory_account_business_upgrade', {'directory_company': directory_company, 'plan_levels': plan_levels} )
        else:
            return "ACCESS DENIED"


    @http.route('/directory/account/business/upgrade/process', type='http', auth="user", website=True)
    def directory_account_business_upgrade_process(self, **kwargs):

        values = {}
	for field_name, field_value in kwargs.items():
	    values[field_name] = field_value

        existing_record = request.env['res.partner'].browse( int(values['business_id'] ) )

        if existing_record.in_directory and existing_record.business_owner.id == request.env.user.id:

            #paypal_url = "https://api-3t.paypal.com/nvp?"
            paypal_url = "https://api-3t.sandbox.paypal.com/nvp?"

            #Submit details to paypal
            return werkzeug.utils.redirect(paypal_url)
        else:
            return "Permission Denied"


    @http.route('/directory/review/process', type='http', auth="public", website=True)
    def directory_review_process(self, **kwargs):
        
        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        directory_company = request.env['res.partner'].sudo().browse( int(values['business_id']) )        
        
        if directory_company.in_directory:
            if int(values['rating']) >= 1 and int(values['rating']) <= 5:
                request.env['res.partner.directory.review'].create({'business_id': values['business_id'], 'name': values['name'], 'description': values['description'], 'rating': values['rating'] })
                return werkzeug.utils.redirect("/directory/company/" + slug(directory_company) )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>/website', type='http', auth="public", website=True)
    def directory_company_page_website(self, directory_company, **kwargs):
        if directory_company.in_directory:
            #isocountry = request.session.geoip and request.session.geoip.get('country_code') or False
            request.env['website.directory.stat.website'].sudo().create({'listing_id': directory_company.id, 'ip': request.httprequest.remote_addr})
        
            return werkzeug.utils.redirect(directory_company.website)
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>', type='http', auth="public", website=True)
    def directory_company_page(self, directory_company, **kwargs):
        if directory_company.in_directory:
            return http.request.render('website_business_directory.directory_company_page', {'directory_company': directory_company} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>/booking', type='http', auth="public", website=True)
    def directory_company_booking(self, directory_company, **kwargs):
        if directory_company.in_directory:
            return http.request.render('website_business_directory.directory_company_booking', {'directory_company': directory_company} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/<model("res.partner"):directory_company>/menu', type='http', auth="public", website=True)
    def directory_company_menu(self, directory_company, **kwargs):
        if directory_company.in_directory:
            return http.request.render('website_business_directory.directory_company_menu', {'directory_company': directory_company} )
        else:
            return "ACCESS DENIED"

    @http.route('/directory/company/booking/process', type='http', auth="public", website=True)
    def directory_company_booking_process(self, **kwargs):
        """Insert the booking into the database then notify the restaurant of the booking via thier preferred notification method(email only atm)"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        directory_company = request.env['res.partner'].sudo().browse( int(values['business_id']) )
        
        if directory_company.allow_restaurant_booking:
            new_booking = request.env['website.directory.booking'].sudo().create({'partner_id': values['business_id'], 'booking_name': values['booking_name'], 'email': values['email'], 'number_of_people': values['number_of_people'], 'booking_datetime': values['booking_datetime'], 'notes': values['notes']})
        
            #Send email
            notification_template = request.env['ir.model.data'].sudo().get_object('website_business_directory', 'directory_booking')
            notification_template.send_mail(new_booking.id, True)
            
            return werkzeug.utils.redirect("/directory")
        else:
            return "BOOKINGS NOT ALLOWED"

    @http.route('/directory/search/<search_string>', type="http", auth="public", website=True)
    def directory_search_results(self, search_string, **kwargs):
        #directory_companies = request.env['res.partner'].sudo().search([('in_directory','=', True), ('name','ilike', search_string) ])
        featured_listings = request.env['res.partner'].sudo().search([('in_directory','=', True), ('name','ilike', search_string), ('featured_listing','=',True) ])
        regular_listings = request.env['res.partner'].sudo().search([('in_directory','=', True), ('name','ilike', search_string), ('featured_listing','=',False) ])
        return http.request.render('website_business_directory.directory_search_results', {'featured_listings': featured_listings, 'regular_listings': regular_listings} )

    @http.route('/directory/categories', type="http", auth="public", website=True)
    def directory_categories(self, **kwargs):
        directory_categories = request.env['res.partner.directory.category'].sudo().search([('parent_category','=',False)])
        return http.request.render('website_business_directory.directory_categories', {'directory_categories': directory_categories} )
        
    @http.route('/directory/auto-complete', auth="public", website=True, type='http')
    def directory_autocomplete(self, **kw):
        """Provides an autocomplete list of businesses and typs in the directory"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        
        return_string = ""
        
        my_return = []
        
        #Get all businesses that match the search term
        directory_partners = request.env['res.partner'].sudo().search([('in_directory','=',True), ('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for directory_partner in directory_partners:
            return_item = {"label": directory_partner.name + "<br/><sub>" + directory_partner.street + "</sub>","value": "/directory/search/" + str(values['term']) }
            my_return.append(return_item)

        #Get all business types that match the search term
        directory_categories = request.env['res.partner.directory.category'].sudo().search([('name','=ilike',"%" + values['term'] + "%")],limit=5)
        
        for directory_category in directory_categories:
            return_item = {"label": directory_category.name,"value": "/directory/search/" + str(values['term']) }
            my_return.append(return_item)
        
        return json.JSONEncoder().encode(my_return)
