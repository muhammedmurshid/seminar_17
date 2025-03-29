from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError


class SeminarLeads(models.Model):
    _name = 'seminar.leads'
    _description = 'Seminar Leads'
    _rec_name = 'lead_source_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    lead_source_id = fields.Many2one('leads.sources', string="Lead Source", required=True, domain=[('name', 'in', ['Seminar','Webinar'])])
    date = fields.Date(string="Date", default=fields.Date.context_today)
    # academic_year = fields.Selection([('2023', '2023-24'), ('2024', '2024-25'), ('2025', '2025-26')], string='Academic Year',)
    reference_no = fields.Char(string='Leads Number', required=True,)
    academic_year = fields.Selection(
        [('2024-2025', '2024-2025'),
         ('2025-2026', '2025-2026'), ('2026-2027', '2026-2027'), ('nil', 'Nil')], string='Academic Year', required=1)
    stream = fields.Char(string="Stream")
    institute_name = fields.Many2one('college.list', string="College / School")
    lead_source_name = fields.Char(related="lead_source_id.name")
    booked_by = fields.Many2one('res.users', string="Seminar Booked By")
    attended_by = fields.Many2one('res.users', string="Seminar Conducted By")
    district = fields.Selection([('wayanad', 'Wayanad'), ('ernakulam', 'Ernakulam'), ('kollam', 'Kollam'),
                                 ('thiruvananthapuram', 'Thiruvananthapuram'), ('kottayam', 'Kottayam'),
                                 ('kozhikode', 'Kozhikode'), ('palakkad', 'Palakkad'), ('kannur', 'Kannur'),
                                 ('alappuzha', 'Alappuzha'), ('malappuram', 'Malappuram'), ('kasaragod', 'Kasaragod'),
                                 ('thrissur', 'Thrissur'), ('idukki', 'Idukki'), ('pathanamthitta', 'Pathanamthitta'),
                                 ('abroad', 'Abroad'), ('other', 'Other'), ('nil', 'Nil')],
                                string='District')
    students_ids = fields.One2many('student.list', 'seminar_id', string="Seminar Leads")
    seminar_duplicate_ids = fields.One2many('duplicate.record.seminar', 'seminar_duplicate_id',
                                            string='Seminar Duplicates')
    bulk_lead_assign = fields.Boolean(string='Bulk Lead Assign')
    assigned_user = fields.Many2one('res.users', string='Assigned User')
    incentive_booked = fields.Boolean(string='Incentive Booked')
    incentive_attended = fields.Boolean(string='Incentive Attended')
    incentive = fields.Float(string="Incentive", compute="_compute_incentive_amount", store=1)
    state = fields.Selection([
        ('draft', 'Draft'), ('filtered', 'Datas Filtered'), ('done', 'Done'), ('leads_assigned', 'Leads Assigned'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('child_count')
    def _compute_incentive_amount(self):
        amount = self.env['seminar.lead.incentive'].sudo().search([], order='id desc', limit=1)
        for rec in self:
            rec.incentive = rec.child_count * amount.incentive_per_lead

    @api.depends('students_ids')
    def _compute_child_count(self):
        for record in self:
            record.child_count = len(record.students_ids)

    child_count = fields.Integer(string='Lead Count', compute='_compute_child_count', store=True)

    def act_submit(self):
        for i in self.students_ids:
            lead = self.env['leads.logic'].create({
                'leads_source': self.lead_source_id.id,
                'email_address': i.email_address,
                'phone_number': i.contact_number,
                'name': i.student_name,
                'seminar_id': self.id,
                'college_name': self.institute_name.college_name,
                'academic_year': self.academic_year,
                'district': self.district,

            })

        self.state = 'done'

    def act_return_to_draft(self):
        self.state = 'draft'

    # def action_add_to_duplicates(self):
    #     leads_rec = self.env['leads.logic'].sudo().search([])
    #
    #     for duplicate in self.students_ids:
    #         # leads_rec = self.env['leads.logic'].sudo().search([])
    #         if duplicate.contact_number:
    #             for j in leads_rec:
    #                 last_10_digits = str(j.phone_number)[-10:]
    #                 print(last_10_digits, 'num')
    #                 # print(j.phone_number[-10:], 'lead')
    #                 # Check if the last 10 digits of both numbers match
    #                 if j.phone_number[-10:] == duplicate.contact_number[-10:]:
    #                     print(duplicate, 'duplicate')
    #                     duplicate.is_it_duplicate = True
    #                     self.seminar_duplicate_ids = [(0, 0, {'student_name': duplicate.student_name,
    #                                                           'contact_number': duplicate.contact_number,
    #                                                           'district': self.district,
    #                                                           'preferred_course': duplicate.preferred_course,
    #                                                           'whatsapp_number': duplicate.whatsapp_number,
    #                                                           'parent_number': duplicate.parent_number,
    #                                                           'email_address': duplicate.email_address,
    #                                                           'place': duplicate.place, })]
    #
    #                     # Uncomment the following line if you want to remove duplicates
    #                     # duplicate.unlink()
    #         if duplicate.is_it_duplicate:
    #             duplicate.unlink()
    #     self.state = 'filtered'
    def action_add_to_duplicates(self):
        leads_rec = {str(j.phone_number)[-10:] for j in self.env['leads.logic'].sudo().search([])}

        duplicates_to_add = []
        for duplicate in self.students_ids:
            if duplicate.contact_number and str(duplicate.contact_number)[-10:] in leads_rec:
                duplicate.is_it_duplicate = True
                duplicates_to_add.append((0, 0, {
                    'student_name': duplicate.student_name,
                    'contact_number': duplicate.contact_number,
                    'district': self.district,
                    'preferred_course': duplicate.preferred_course,
                    'whatsapp_number': duplicate.whatsapp_number,
                    'parent_number': duplicate.parent_number,
                    'email_address': duplicate.email_address,
                    'place': duplicate.place,
                }))

        if duplicates_to_add:
            self.seminar_duplicate_ids = duplicates_to_add

        self.students_ids.filtered(lambda d: d.is_it_duplicate).unlink()
        self.state = 'filtered'

    def action_bulk_lead_assign(self):
        print('action_bulk_lead_assign')
        return {'name': _('Bulk Assign'),
                'type': 'ir.actions.act_window',
                'res_model': 'bulk.seminar.assign',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_seminar_id': self.id}
                }

    def get_current_leads(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Leads',
            'view_mode': 'tree,form',
            'res_model': 'leads.logic',
            'domain': [('seminar_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_count(self):
        for record in self:
            record.leads_smart_count = self.env['leads.logic'].sudo().search_count(
                [('seminar_id', '=', self.id)])

    leads_smart_count = fields.Integer(compute='compute_count')

    def action_check_leads(self):
        """Check if last 10 digits of student contact match leads.logic and update seminar_id"""
        Lead = self.env['leads.logic']  # Access the leads model

        for record in self:
            student_contacts = [s.contact_number[-10:] for s in record.students_ids if s.contact_number]

            matching_leads = Lead.search([
                ('phone_number', '!=', False)
            ])

            for lead in matching_leads:
                if lead.phone_number[-10:] in student_contacts:
                    lead.seminar_id = record.id
                    lead.college_name = record.institute_name.college_name

    def action_bulk_lead_assignment(self):
        Lead = self.env['leads.logic']  # Access the leads model

        selected_records = self
        return {'name': _('Bulk Assign'),
                'type': 'ir.actions.act_window',
                'res_model': 'bulk.seminar.assign',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_seminar_ids': selected_records.ids}
                }
    def action_bulk_lead_connection(self):
        Lead = self.env['leads.logic']  # Access the leads model

        selected_records = self  # This contains the selected records

        for record in selected_records:
            student_contacts = [
                s.contact_number[-10:] for s in record.students_ids if s.contact_number
            ]

            matching_leads = Lead.search([('phone_number', '!=', False)])

            for lead in matching_leads:
                if lead.phone_number[-10:] in student_contacts:
                    lead.seminar_id = record.id
                    lead.college_name = record.institute_name.college_name


class StudentList(models.Model):
    _name = "student.list"

    student_name = fields.Char(string='Student Name', required=True)
    contact_number = fields.Char(string='Contact Number', required=True, default='+91')
    whatsapp_number = fields.Char(string='Whatsapp Number')
    seminar_id = fields.Many2one('seminar.leads', string='Seminar', ondelete='cascade')
    place = fields.Char(string='Place')
    admission_status = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Admission Status', readonly=True,
                                        default='no')
    is_it_duplicate = fields.Boolean(string="Duplicate")
    state = fields.Selection([
        ('draft', 'Draft'), ('done', 'Done'),
    ], string='Status',related='seminar_id.state')
    email_address = fields.Char(string='Email Address')
    parent_number = fields.Char(string='Parent Number')
    preferred_course = fields.Char(string='Preferred Course')
    last_call_by = fields.Char(string="Last Call By")
    date_of_call = fields.Date(string="Date of Call")
    last_call_remarks = fields.Char(string="Last Call Remarks")
    admission_by = fields.Char(string="Admission By")
    admission_date = fields.Date(string="Admission Date")

    @api.onchange('contact_number')
    def _onchange_duplicate_phone_number(self):
        print('Checking for duplicate phone number...')

        if not self.contact_number or self.contact_number == +91:
            return

        # Extract the last 10 digits
        last_10_digits = self.contact_number[-10:]
        print(f'Last 10 Digits: {last_10_digits}, Current Record ID: {self._origin.id}')
        if self.contact_number != '+91':
            print('yes')
            # Search in `leads.logic` model for records with the same last 10 digits
            duplicate = self.env['leads.logic'].sudo().search([
                ('phone_number', 'like', '%' + last_10_digits),
                ('id', '!=', self._origin.id)  # Ignore current record
            ], limit=1)  # Optimized: Fetch only 1 duplicate if exists

            if duplicate:
                return {
                    'warning': {
                        'title': _("Duplicate Phone Number"),
                        'message': _("The phone number %s already exists in the system in a lead.") % self.contact_number,
                    }
                }
        else:
            print('nop')
class SeminarLeadIncentive(models.Model):
    _name = 'seminar.lead.incentive'
    _description = 'Incentive Amount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'incentive_per_lead'

    incentive_per_lead = fields.Float(string='Incentive per lead')

class DuplicateRecord(models.TransientModel):
    _name = 'duplicate.record.seminar'

    student_name = fields.Char(string='Student Name', required=True)
    contact_number = fields.Char(string='Contact Number', required=True)
    whatsapp_number = fields.Char(string='Whatsapp Number')
    seminar_duplicate_id = fields.Many2one('seminar.leads', string='Seminar', ondelete='cascade')
    place = fields.Char(string='Place')
    admission_status = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Admission Status', readonly=True,
                                        default='no')
    district = fields.Selection([('wayanad', 'Wayanad'), ('ernakulam', 'Ernakulam'), ('kollam', 'Kollam'),
                                 ('thiruvananthapuram', 'Thiruvananthapuram'), ('kottayam', 'Kottayam'),
                                 ('kozhikode', 'Kozhikode'), ('palakkad', 'Palakkad'), ('kannur', 'Kannur'),
                                 ('alappuzha', 'Alappuzha'), ('malappuram', 'Malappuram'), ('kasaragod', 'Kasaragod'),
                                 ('thrissur', 'Thrissur'), ('idukki', 'Idukki'), ('pathanamthitta', 'Pathanamthitta'),
                                 ('abroad', 'Abroad'), ('other', 'Other')],
                                string='District')
    email_address = fields.Char(string='Email Address')
    parent_number = fields.Char(string='Parent Number')
    preferred_course = fields.Char(string='Preferred Course')
    selected_lead = fields.Boolean(string='Selected Lead')
